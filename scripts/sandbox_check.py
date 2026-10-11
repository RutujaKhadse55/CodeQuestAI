"""Phase 0 sandbox hello-world: decide native vs Docker on THIS machine (plan §6 P0, Backend item 5).

Run on every teammate laptop:  python scripts/sandbox_check.py
"""
import platform
import shutil
import subprocess
import sys
import tempfile

HELLO = "print('hello from sandbox')"


def native() -> tuple[bool, str]:
    try:
        import resource  # noqa: F401  (POSIX only: needed for setrlimit memory/CPU caps)
    except ImportError:
        return False, "no `resource` module (Windows) -> cannot enforce rlimits natively"
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([sys.executable, "-I", "-c", HELLO], cwd=d, env={}, capture_output=True,
                           text=True, timeout=5)
    return r.stdout.strip() == "hello from sandbox", "python -I, empty env, temp cwd"


def docker() -> tuple[bool, str]:
    if not shutil.which("docker"):
        return False, "docker not installed"
    try:
        r = subprocess.run(["docker", "run", "--rm", "--network", "none", "--memory", "256m", "--cpus", "1",
                            "--pids-limit", "64", "--read-only", "python:3.11-slim", "python", "-I", "-c", HELLO],
                           capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return False, "docker run timed out (image pull?)"
    if r.returncode == 0 and "hello" in r.stdout:
        return True, "docker run with --network none --read-only limits"
    return False, (r.stderr.strip().splitlines() or ["docker failed"])[-1]


if __name__ == "__main__":
    n_ok, n_msg = native()
    d_ok, d_msg = docker()
    print(f"{platform.system()} | native: {'OK' if n_ok else 'NO'} ({n_msg}) | docker: {'OK' if d_ok else 'NO'} ({d_msg})")
    mode = "native" if n_ok else "docker" if d_ok else "NONE"
    print(f"SANDBOX_MODE={mode}")
    sys.exit(0 if mode != "NONE" else 1)
