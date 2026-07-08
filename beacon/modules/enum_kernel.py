import json
import os
import platform

TASK_NAME = "enum_kernel"


def _load_cve_db() -> list[dict]:
  here = os.path.dirname(os.path.abspath(__file__))
  candidates = [
    os.path.join(here, "..", "data", "cve_db.json"),
    os.path.join(here, "data", "cve_db.json"),
    "/tmp/beacon_data/cve_db.json",
  ]
  for path in candidates:
    if os.path.isfile(path):
      with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
  return []


def _kernel_matches(kernel: str, pattern: str) -> bool:
  if pattern.endswith("*"):
    return kernel.startswith(pattern[:-1])
  return kernel == pattern


def run(context: dict) -> dict:
  kernel = platform.release()
  os_info = platform.platform()
  cve_db = context.get("cve_db") or _load_cve_db()
  findings = []
  for entry in cve_db:
    for pattern in entry.get("kernels", []):
      if _kernel_matches(kernel, pattern):
        findings.append(
          {
            "type": "potential_cve",
            "cve_id": entry["cve_id"],
            "description": entry.get("description", ""),
            "severity": entry.get("severity", "unknown"),
            "kernel": kernel,
            "note": "Report only — manual verification required in isolated lab",
          }
        )
        break
  return {
    "task": TASK_NAME,
    "findings": findings,
    "kernel": kernel,
    "os_info": os_info,
    "raw": f"kernel={kernel}\nos={os_info}",
  }
