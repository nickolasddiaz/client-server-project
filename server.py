import socket
import threading

from encoder import Encoder
from directory_func import list_directory, path_directory, str_path
from type import Command, cmd_str, ResponseCode, KeyData

# localhost if needed
IP = "0.0.0.0"
PORT = 4453
ADDR = (IP,PORT)
SIZE = 1024

### to handle the clients
def handle_client (conn,addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    info: dict = {KeyData.MSG: "Welcome to the server"}
    data: bytes = Encoder.encode(info, ResponseCode.OK)
    conn.send(data)
    while True:
        encoded_data = conn.recv(SIZE)
        if not encoded_data:
            # If no data is received (client closed connection), break the loop
            break

        data: dict = Encoder.client_decode(encoded_data)

        cmd: Command = data[KeyData.CMD]
        match cmd:
            case Command.LOGOUT:
                info: dict = {KeyData.MSG.value: "Disconnecting from server"}
                data: bytes = Encoder.encode(info, ResponseCode.DISCONNECT)
                conn.send(data)
                break # gets out of the while(true) loop
            case Command.DIR:
                folder_path = path_directory()
                info: dict = {KeyData.MSG: str_path(list_directory(folder_path))}
                data: bytes = Encoder.encode(info, ResponseCode.OK)
                conn.send(data)
            case Command.TREE:
                folder_path = path_directory()
                info: dict = {KeyData.MSG: str_path(list_directory(folder_path, True))}
                data: bytes = Encoder.encode(info, ResponseCode.OK)
                conn.send(data)
            case Command.HELP:
                info: dict = {KeyData.MSG: cmd_str()}
                data: bytes = Encoder.encode(info, ResponseCode.OK)
                conn.send(data)
            # default case
            case _:
                info: dict = {KeyData.MSG: "Invalid command received"}
                data: bytes = Encoder.encode(info, ResponseCode.INVALID_CMD)
                conn.send(data)

    print(f"{addr} disconnected")
    conn.close()


def main():
    print("Starting the server")
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) ## used IPV4 and TCP connection
    server.bind(ADDR) # bind the address
    print(ADDR)
    server.listen() ## start listening
    print(f"server is listening on {IP}: {PORT}")
    while True:
        conn, addr = server.accept() ### accept a connection from a client
        thread = threading.Thread(target = handle_client, args = (conn, addr)) ## assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()


