import os

from ._helpers import run_cmd

TASK_NAME = "enum_writable"


def run(_context: dict) -> dict:
  targets = ["/etc/passwd", "/etc/shadow", "/etc/sudoers", "/etc/cron.d"]
  findings = []
  raw_parts = []
  for path in targets:
    if os.path.exists(path):
      findings.append(
        {
          "path": path,
          "writable": os.access(path, os.W_OK),
          "readable": os.access(path, os.R_OK),
        }
      )
  stdout, stderr, rc = run_cmd(
    ["find", "/tmp", "/var/tmp", "/dev/shm", "-writable", "-type", "f"],
    timeout=60,
  )
  writable_tmp = stdout.splitlines()[:50]
  findings.append({"type": "writable_temp_files", "count": len(writable_tmp)})
  raw_parts.append(stdout[:4000])
  return {
    "task": TASK_NAME,
    "findings": findings,
    "raw": "\n".join(raw_parts),
    "stderr": stderr[:1000],
    "returncode": rc,
  }
