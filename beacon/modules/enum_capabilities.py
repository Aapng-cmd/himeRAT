from ._helpers import run_cmd

TASK_NAME = "enum_capabilities"


def run(_context: dict) -> dict:
  stdout, stderr, rc = run_cmd(["getcap", "-r", "/", "/dev/null"], timeout=120)
  findings = []
  for line in stdout.splitlines():
    line = line.strip()
    if not line:
      continue
    findings.append({"type": "capability", "line": line})
    if "cap_setuid" in line or "cap_dac_override" in line:
      findings[-1]["elevated_risk"] = True
  return {
    "task": TASK_NAME,
    "findings": findings,
    "raw": stdout[:8000],
    "stderr": stderr[:2000],
    "returncode": rc,
  }
