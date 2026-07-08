import base64
import hashlib
import os

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


class Encryptor:
  def __init__(self, key):
    if isinstance(key, str):
      key = key.encode()
    self.__key__ = key

  def __pad(self, raw):
    bs = AES.block_size
    return raw + chr(bs - len(raw) % bs) * (bs - len(raw) % bs)

  def __unpad(self, raw):
    return raw[: -ord(raw[-1])]

  def encrypt_str(self, raw):
    padded = base64.b64encode(self.__pad(raw).encode("utf-8"))
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(self.__key__, AES.MODE_CFB, iv=iv)
    return base64.b64encode(iv + cipher.encrypt(padded)).decode("ascii")

  def encrypt(self, fn):
    with open(fn, "r", encoding="utf-8") as f:
      data = f.read()
    with open(fn, "w", encoding="utf-8") as f:
      f.write(self.encrypt_str(data))
