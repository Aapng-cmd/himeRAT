import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


class Encryptor:
  def __init__(self, key: bytes):
    if isinstance(key, str):
      key = key.encode()
    self._key = key

  def _pad(self, raw: str) -> str:
    bs = AES.block_size
    return raw + chr(bs - len(raw) % bs) * (bs - len(raw) % bs)

  def _unpad(self, raw: str) -> str:
    return raw[: -ord(raw[-1])]

  def encrypt_str(self, raw: str) -> str:
    padded = base64.b64encode(self._pad(raw).encode("utf-8"))
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(self._key, AES.MODE_CFB, iv=iv)
    return base64.b64encode(iv + cipher.encrypt(padded)).decode("ascii")

  def decrypt_str(self, enc: str) -> str:
    enc = base64.b64decode(enc)
    iv = enc[: AES.block_size]
    cipher = AES.new(self._key, AES.MODE_CFB, iv=iv)
    padded = base64.b64decode(cipher.decrypt(enc[AES.block_size :]))
    return self._unpad(padded.decode("utf-8"))

  def decrypt_payload(self, enc: str) -> str:
    return base64.b64decode(self.decrypt_str(enc)).decode("utf-8")
