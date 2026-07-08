import base64
import os

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


def derive_shared(
  private_key: x25519.X25519PrivateKey, peer_pk_b64: str
) -> bytes:
  peer = x25519.X25519PublicKey.from_public_bytes(base64.b64decode(peer_pk_b64))
  return _derive(private_key.exchange(peer))


class NodeChannel:
  """Защищённый канал узла (ECDH X25519 + AES-GCM)."""

  def __init__(self, sid: str, key: bytes):
    self.sid = sid
    self._gcm = AESGCM(key)

  @classmethod
  def from_handshake(cls, server_pk_b64: str) -> tuple["NodeChannel", str]:
    priv = x25519.X25519PrivateKey.generate()
    server_pub = x25519.X25519PublicKey.from_public_bytes(
      base64.b64decode(server_pk_b64)
    )
    key = _derive(priv.exchange(server_pub))
    return cls("", key), _pub_b64(priv.public_key())

  def bind(self, sid: str) -> None:
    self.sid = sid

  def seal(self, payload: bytes) -> dict:
    nonce = os.urandom(12)
    blob = self._gcm.encrypt(nonce, payload, None)
    return {
      "n": base64.b64encode(nonce).decode(),
      "d": base64.b64encode(blob).decode(),
    }

  def open(self, envelope: dict) -> bytes:
    nonce = base64.b64decode(envelope["n"])
    blob = base64.b64decode(envelope["d"])
    return self._gcm.decrypt(nonce, blob, None)
