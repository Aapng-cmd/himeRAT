import requests
import base64
import os
import socket
import hashlib, random
import zipfile
import shutil
import threading
import platform
import uuid
from io import BytesIO


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
            # data = str(data)
            # print(data)
            data = base64.b64decode(data).decode()
            f.write(data)

# ------------------END---------------

class Client:
    def __init__(self, server_url, creds, alias):
        self.server_url = server_url
        self.username = creds[0]
        self.password = creds[1]
        self.creds = creds
        self.local_ip = socket.gethostbyname(socket.gethostname())
        self.pid = os.getpid()
        self.encoded_credentials = self.encode_credentials()
        self.e = Encryptor(alias)#base64.b64decode(alias[::-1]))

    def encode_credentials(self):
        credentials = f"{self.username}:{self.password}"
        return base64.b64encode(credentials.encode()).decode()

    def __get_system_hash(self):
        os_info = platform.platform()
        cpu_info = platform.processor()
        ram_info = str(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')) if os.name != 'nt' else str(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES'))
        disk_info = "Disk serial info not available on this OS"
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 2)][::-1])
        username = os.getlogin() if os.name != 'nt' else os.environ.get('USERNAME')
        system_info = f"{os_info}|{cpu_info}|{ram_info}|{disk_info}|{mac}|{username}"
        return hashlib.sha256(system_info.encode()).hexdigest()

    
    def register(self):
        registration_data = {
            'pid': self.pid,
            'username': self.username,
            'local_ip': self.local_ip,
            'system_hash': self.__get_system_hash()
        }
        response = requests.post(
            f"{self.server_url}/registrate",
            data=registration_data,
            headers={'Authorization': f'Basic {self.encoded_credentials}'}
        )
        return response

    def get_modules(self, cuuid):
        key = hashlib.pbkdf2_hmac('sha256', os.urandom(32), os.urandom(32), random.randint(100000, 999999))
        k = base64.b64encode(key).decode()

        data = {
            "cuuid": cuuid,
            "key": k,
        }
        q = requests.post(self.server_url + '/share', auth=self.creds, data=data)
        if not q.ok:
            return q.status_code
        # print(q.content)
        z = zipfile.ZipFile(BytesIO(base64.b64decode(q.content)))
        z.extractall("./test")
        # _ = self.decrypt_folder("test", key)
        return q.status_code
    
    def decrypt_folder(self, name, key):
        fn = os.listdir(name)[0]
        names = os.listdir("test\\" + fn)
        for name in names:
            if os.path.isfile("test\\" + fn + "\\" + name):
                self.e.decrypt("test\\" + fn + "\\" + name)

        return fn

if __name__ == "__main__":
    client = Client('http://127.0.0.1:1337', ('admin', 'password'), "secret_key")
    registration_response = client.register()
    if registration_response.status_code == 200:
        cuuid = registration_response.text
        print(f"Registration successful. {cuuid=}")
        modules_response = client.get_modules(cuuid)
        if modules_response == 200:
            print("Modules received successfully.")
        else:
            print("Failed to retrieve modules:", modules_response.text)
    else:
        print("Registration failed:", registration_response.text)

