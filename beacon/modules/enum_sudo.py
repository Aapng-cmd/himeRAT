from ._helpers import run_cmd

TASK_NAME = "enum_sudo"

GTFOBINS = {
  "vim", "vi", "nano", "less", "more", "awk", "python", "python3",
  "perl", "ruby", "lua", "find", "nmap", "tar", "cp", "mv", "dd",
  "mount", "umount", "systemctl", "journalctl", "docker", "git",
  "ftp", "socat", "nc", "netcat", "openssl", "env", "bash", "sh",
}


def run(_context: dict) -> dict:
  stdout, stderr, rc = run_cmd(["sudo", "-l", "-n"], timeout=15)
  findings = []
  for line in stdout.splitlines():
    lower = line.lower()
    if "nopasswd" in lower:
      for binary in GTFOBINS:
        if binary in lower:
          findings.append(
            {
              "type": "gtfobin_candidate",
              "binary": binary,
              "line": line.strip(),
              "note": "Check https://gtfobins.github.io/ for manual verification",
            }
          )
          break
      else:
        findings.append({"type": "sudo_nopasswd", "line": line.strip()})
  return {
    "task": TASK_NAME,
    "findings": findings,
    "raw": stdout[:8000],
    "stderr": stderr[:2000],
    "returncode": rc,
  }
