import subprocess


def run_cmd(cmd: list[str], timeout: int = 30) -> tuple[str, str, int]:
  try:
    proc = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      timeout=timeout,
    )
    return proc.stdout, proc.stderr, proc.returncode
  except subprocess.TimeoutExpired:
    return "", "timeout", -1
  except FileNotFoundError:
    return "", f"command not found: {cmd[0]}", -1
