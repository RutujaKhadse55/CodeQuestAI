"""Sandbox service: a tiny stdlib HTTP server that runs the harness natively (rlimits) for the backend.

Run:  python -m app.engine.sandbox.server           (listens on 0.0.0.0:9000 inside the sandbox container)

Deployed as its OWN container on an internal-only network (see docker-compose.yml): no API keys in its
environment, no route to the internet, read-only filesystem, all capabilities dropped. Even a full escape from
the restricted interpreter therefore has no secret to read and no way to exfiltrate anything.
Endpoints: GET /health, POST /run {"payload": {...}, "total": seconds} + header X-Sandbox-Token.
"""
import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import runner

TOKEN = os.getenv("SANDBOX_TOKEN", "sandbox-dev-token")
MAX_BODY = 8_000_000  # a few LeetCode-sized (10^5 element) inputs fit comfortably
MAX_TOTAL_S = 120.0
SLOTS = threading.BoundedSemaphore(int(os.getenv("SANDBOX_CONCURRENCY", "3")))  # container memory is finite


class Handler(BaseHTTPRequestHandler):
    server_version = "cq-sandbox"

    def _send(self, code: int, obj: dict) -> None:
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # keep logs free of payloads
        pass

    def do_GET(self):
        self._send(200, {"status": "ok"}) if self.path == "/health" else self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/run":
            return self._send(404, {"error": "not found"})
        if not hmac.compare_digest(self.headers.get("X-Sandbox-Token", ""), TOKEN):
            return self._send(401, {"error": "bad token"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if not 0 < n <= MAX_BODY:
                return self._send(413, {"error": "bad body size"})
            req = json.loads(self.rfile.read(n))
            payload, total = req["payload"], min(float(req["total"]), MAX_TOTAL_S)
        except (ValueError, KeyError, TypeError):
            return self._send(400, {"error": "bad request"})
        if not SLOTS.acquire(timeout=30):
            return self._send(503, {"error": "sandbox busy"})
        try:
            self._send(200, {"stdout": runner._native(payload, total)})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": type(e).__name__})
        finally:
            SLOTS.release()


def main() -> None:
    ThreadingHTTPServer(("0.0.0.0", int(os.getenv("SANDBOX_PORT", "9000"))), Handler).serve_forever()


if __name__ == "__main__":
    main()
