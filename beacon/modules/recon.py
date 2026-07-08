import os
import platform
import socket

TASK_NAME = "recon"  # базовая информация об узле


def run(_context: dict) -> dict:
  findings = {
    "hostname": socket.gethostname(),
    "user": os.environ.get("USER") or os.environ.get("USERNAME", "unknown"),
    "uid": os.getuid() if hasattr(os, "getuid") else None,
    "pid": os.getpid(),
    "cwd": os.getcwd(),
    "platform": platform.platform(),
    "kernel": platform.release(),
    "machine": platform.machine(),
  }
  return {"task": TASK_NAME, "findings": findings, "raw": str(findings)}
