from ._helpers import run_cmd

TASK_NAME = "enum_suid"


def run(_context: dict) -> dict:
  stdout, stderr, rc = run_cmd(
    ["find", "/", "-perm", "-4000", "-type", "f", "-readable", "-size", "-10M"],
    timeout=120,
  )
  paths = [line.strip() for line in stdout.splitlines() if line.strip()]
  findings = [{"path": p, "type": "suid_binary"} for p in paths[:200]]
  return {
    "task": TASK_NAME,
    "findings": findings,
    "count": len(paths),
    "truncated": len(paths) > 200,
    "raw": stdout[:8000],
    "stderr": stderr[:2000],
    "returncode": rc,
  }
