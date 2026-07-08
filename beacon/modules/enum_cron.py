import glob
import os

from ._helpers import run_cmd

TASK_NAME = "enum_cron"


def run(_context: dict) -> dict:
  findings = []
  paths = [
    "/etc/crontab",
    "/etc/cron.d",
    "/etc/cron.daily",
    "/etc/cron.hourly",
    "/etc/cron.weekly",
    "/etc/cron.monthly",
    "/var/spool/cron",
    "/var/spool/cron/crontabs",
  ]
  raw_parts = []
  for path in paths:
    if os.path.isfile(path) and os.access(path, os.R_OK):
      with open(path, "r", errors="replace") as f:
        content = f.read(4000)
      findings.append({"type": "cron_file", "path": path, "writable": os.access(path, os.W_OK)})
      raw_parts.append(f"=== {path} ===\n{content}")
    elif os.path.isdir(path):
      for entry in glob.glob(path + "/*")[:50]:
        readable = os.access(entry, os.R_OK)
        writable = os.access(entry, os.W_OK)
        findings.append(
          {
            "type": "cron_entry",
            "path": entry,
            "readable": readable,
            "writable": writable,
          }
        )
  user_cron, _, _ = run_cmd(["crontab", "-l"], timeout=10)
  if user_cron.strip():
    findings.append({"type": "user_crontab", "content_preview": user_cron[:1000]})
    raw_parts.append(f"=== user crontab ===\n{user_cron}")
  return {
    "task": TASK_NAME,
    "findings": findings,
    "raw": "\n".join(raw_parts)[:12000],
  }
