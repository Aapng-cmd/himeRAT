import os
import zipfile
import base64
import sqlite3
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from .tcp_cr import TCPEncryptor

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, SECRET_KEY=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.alice = TCPEncryptor(SECRET_KEY)

    def do_GET(self):
        if self.path == '/share':
            self.handle_share()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/registrate':
            self.handle_registrate()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_share(self):
        # Specify the directory to zip
        directory_to_zip = './modules'  # Change this to your directory path
        zip_filename = 'archive.zip'

        # Create a zip file of the directory
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(directory_to_zip):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), directory_to_zip))

        # Read the zip file and encode it in base64
        with open(zip_filename, 'rb') as zipf:
            zip_data = zipf.read()
            encoded_data = base64.b64encode(zip_data).decode('utf-8')

        # Encrypt the encoded data
        encrypted_data = self.alice.create_packet(encoded_data).hex()

        # Send the response
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(encrypted_data.encode('utf-8'))

    def handle_registrate(self):
        # Basic authentication
        auth_header = self.headers.get('Authorization')
        if not auth_header or not self.check_auth(auth_header):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Register"')
            self.end_headers()
            return

        # Parse the POST data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        user_info = parse_qs(post_data)

        # Extract user information
        username = user_info.get('username', [None])[0]
        local_ip = user_info.get('local_ip', [None])[0]
        pid = os.getpid()  # Get the current process ID

        if username is None or local_ip is None:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Username and local_ip are required')
            return

        # Generate a UUID
        computer_uuid = str(uuid.uuid4())

        # Save the user information to the database
        self.save_to_database(computer_uuid, pid, username, local_ip)

        # Send a success response
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Registration successful')

    def save_to_database(self, computer_uuid, pid, username, local_ip):
        # Connect to the SQLite database
        conn = sqlite3.connect('../computers.db')
        cursor = conn.cursor()

        # Create the table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS computers (
                uuid TEXT PRIMARY KEY,
                pid INTEGER,
                user TEXT,
                local_ip TEXT
            )
        ''')

        # Insert the new computer record
        cursor.execute('''
            INSERT INTO computers (uuid, pid, user, local_ip)
            VALUES (?, ?, ?, ?)
        ''', (computer_uuid, pid, username, local_ip))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

    def check_auth(self, auth_header):
        # Decode the base64 encoded credentials
        auth_type, credentials = auth_header.split(' ', 1)
        if auth_type.lower() != 'basic':
            return False
        username, password = base64.b64decode(credentials).decode('utf-8').split(':', 1)
        # Here you can implement your own logic to check the username and password
        return username == 'admin' and password == 'password'  # Example credentials

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080, secret_key='your_secret_key'):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class, SECRET_KEY=secret_key)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()

