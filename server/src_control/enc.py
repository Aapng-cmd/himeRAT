# ----------------------Encryption files--------------
import base64
import hashlib
import os

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


class Encryptor:
    def __init__(self, key):
        self.__key__ = key

    def __encrypt(self, raw):
        BS = AES.block_size
        pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)

        raw = base64.b64encode(pad(raw).encode('ascii'))
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(key=self.__key__, mode=AES.MODE_CFB ,iv=iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def encrypt(self, fn):
        with open(fn, "r") as f:
            data = f.read()
        with open(fn, "w") as f:
            f.write(self.__encrypt(data).decode())

# ------------------------Encryption END----------------
