import base64
import os
import secrets

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_SALT = b"himeRAT-lab-ecdh-v1"
_INFO = b"inventory-sync-session"


def _derive(shared: bytes) -> bytes:
  return HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=_SALT,
    info=_INFO,
  ).derive(shared)


def _pub_b64(key: x25519.X25519PublicKey) -> str:
  raw = key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
  )
  return base64.b64encode(raw).decode()


class SessionManager:
  def __init__(self):
    self._sessions: dict[str, "SecureChannel"] = {}

  def open_session(self, client_pk_b64: str) -> tuple[str, str]:
    sid = secrets.token_hex(16)
    priv = x25519.X25519PrivateKey.generate()
    client_pub = x25519.X25519PublicKey.from_public_bytes(
      base64.b64decode(client_pk_b64)
    )
    key = _derive(priv.exchange(client_pub))
    self._sessions[sid] = SecureChannel(sid, key)
    return sid, _pub_b64(priv.public_key())

  def get(self, sid: str) -> "SecureChannel | None":
    return self._sessions.get(sid)


class SecureChannel:
  def __init__(self, sid: str, key: bytes):
    self.sid = sid
    self._gcm = AESGCM(key)

  def pack(self, payload: bytes) -> dict:
    nonce = os.urandom(12)
    blob = self._gcm.encrypt(nonce, payload, None)
    return {
      "n": base64.b64encode(nonce).decode(),
      "d": base64.b64encode(blob).decode(),
    }

  def unpack(self, envelope: dict) -> bytes:
    nonce = base64.b64decode(envelope["n"])
    blob = base64.b64decode(envelope["d"])
    return self._gcm.decrypt(nonce, blob, None)


def client_session_key(
  client_priv: x25519.X25519PrivateKey, server_pk_b64: str
) -> bytes:
  server_pub = x25519.X25519PublicKey.from_public_bytes(
    base64.b64decode(server_pk_b64)
  )
  return _derive(client_priv.exchange(server_pub))
