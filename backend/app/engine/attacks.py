"""Attack snippets the sandbox must neutralise (plan §6 Phase 1 item 8). Used by tests and /admin/attacks."""

_WRAP = "class Solution:\n    def f(self, nums):\n{body}\n"


def _sol(body: str) -> str:
    return _WRAP.format(body="\n".join("        " + ln for ln in body.splitlines()))


ATTACKS: dict[str, str] = {
    "file_read": _sol("return open('/etc/passwd').read()"),
    "os_system": "import os\n" + _sol("return os.system('echo pwned')"),
    "network_socket": "import socket\n" + _sol("return socket.socket().connect(('8.8.8.8', 53))"),
    "subprocess": "import subprocess\n" + _sol("return subprocess.run(['ls'])"),
    "eval_exec": _sol("return eval('__import__(\"os\").getcwd()')"),
    "dunder_escape": _sol("return ().__class__.__bases__[0].__subclasses__()"),
    "infinite_loop": _sol("while True:\n    pass"),
    "memory_bomb": _sol("x = [0] * (10 ** 10)\nreturn len(x)"),
}
# Policy-level attacks are rejected before execution; the last two must be contained by the sandbox.
SANDBOX_CONTAINED = {"infinite_loop", "memory_bomb"}
