"""Sandbox runner: executes the harness with a JSON payload in Docker, natively (POSIX), or on a remote sandbox
service.

SANDBOX_MODE = docker | native | remote | auto (auto: native only on POSIX with `resource`, else docker).
  docker : `docker run --network none ...` per call (dev laptops; Windows => docker, decided in Phase 0)
  native : rlimit'd child process; ONLY safe inside a container that has no secrets and no egress
  remote : POST to the sandbox service (engine/sandbox/server.py) on an internal-only network: production default.
           The service container holds no API keys and cannot reach the internet, so even a full interpreter
           escape finds nothing to steal and nowhere to send it.
"""
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from ... import config

_ENGINE = Path(__file__).resolve().parents[1]
# One standalone source: shrinker + tracer + harness (the harness uses their names directly).
SOURCE_FILES = [_ENGINE / "shrinker.py", _ENGINE / "tracer" / "tracer.py", _ENGINE / "harness.py"]


def build_source() -> str:
    return (chr(10) * 2).join(f.read_text(encoding="utf-8") for f in SOURCE_FILES)


IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.11-slim")
STARTUP_SLACK_S = 12.0  # container start / image latency
MAX_STDOUT_BYTES = 1_000_000


class SandboxUnavailable(RuntimeError):
    pass


def resolve_mode() -> str:
    mode = config.SANDBOX_MODE
    if mode in ("docker", "native", "remote"):
        return mode
    try:
        import resource  # noqa: F401
        return "native" if sys.platform != "win32" else "docker"
    except ImportError:
        return "docker"


def run(payload: dict, total_timeout_s: float) -> list[dict]:
    """Return the harness' JSON lines (parsed). Raises SandboxUnavailable if no sandbox can start."""
    mode = resolve_mode()
    raw = {"docker": _docker, "native": _native, "remote": _remote}[mode](payload, total_timeout_s)
    lines = []
    for ln in raw.splitlines():
        try:
            lines.append(json.loads(ln))
        except ValueError:
            continue
    return lines


def _text(b) -> str:
    if b is None:
        return ""
    s = b.decode("utf-8", "replace") if isinstance(b, bytes) else b
    return s[:MAX_STDOUT_BYTES]


def _remote(payload: dict, total: float) -> str:
    """Send the payload to the sandbox service; it answers with the harness' stdout."""
    body = json.dumps({"payload": payload, "total": total}).encode()
    req = urllib.request.Request(config.SANDBOX_URL.rstrip("/") + "/run", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "X-Sandbox-Token": config.SANDBOX_TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=total + STARTUP_SLACK_S) as resp:
            return _text(json.loads(resp.read(MAX_STDOUT_BYTES * 2)).get("stdout", ""))
    except urllib.error.HTTPError as e:
        raise SandboxUnavailable(f"sandbox service returned HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as e:
        raise SandboxUnavailable(f"sandbox service unreachable: {type(e).__name__}") from e


def _docker(payload: dict, total: float) -> str:
    name = f"cq-sbx-{uuid.uuid4().hex[:12]}"
    cmd = ["docker", "run", "--rm", "-i", "--name", name, "--network", "none",
           "--memory", "256m", "--memory-swap", "256m", "--cpus", "1", "--pids-limit", "64",
           "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
           "--user", "65534:65534", "--tmpfs", "/tmp:rw,noexec,size=16m",
           IMAGE, "python", "-I", "-c", build_source()]
    try:
        r = subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True,
                           timeout=total + STARTUP_SLACK_S)
    except subprocess.TimeoutExpired as e:
        subprocess.run(["docker", "kill", name], capture_output=True)
        return _text(e.stdout)
    except FileNotFoundError as e:
        raise SandboxUnavailable("docker is not installed") from e
    if r.returncode == 125 or (r.returncode != 0 and not r.stdout and "docker" in r.stderr.lower()):
        raise SandboxUnavailable(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "docker failed")
    out = _text(r.stdout)
    if r.returncode in (137, 139):  # SIGKILL (OOM killer / limits) or SIGSEGV, no timeout involved
        out += chr(10) + json.dumps({"killed": "sandbox process terminated (memory limit or crash)"}) + chr(10)
    return out


def _native(payload: dict, total: float) -> str:
    import resource  # POSIX only

    def limits():
        os.setsid()
        mem = 256 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        cpu = int(total) + 2
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))

    with tempfile.TemporaryDirectory() as cwd:
        script = Path(cwd) / "sandbox_main.py"
        script.write_text(build_source(), encoding="utf-8")
        p = subprocess.Popen([sys.executable, "-I", str(script)], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env={}, cwd=cwd,
                             preexec_fn=limits)
        try:
            out, _ = p.communicate(json.dumps(payload).encode(), timeout=total)
        except subprocess.TimeoutExpired:
            import signal
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            out, _ = p.communicate()
        return _text(out)
