# server device runs this program

from pathlib import Path
import socket
import threading

from directory_func import DirHelp
from encoder import Encoder
from file_transfer import Transfer
from type import Command, cmd_str, ResponseCode, KeyData, SIZE
from relativepath import RelativePath

# localhost if needed
IP = "0.0.0.0"
PORT = 4453
ADDR = (IP,PORT)
SERVER_DIR = RelativePath.from_base("server_location")

### to handle the clients
def handle_client (conn,addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    info: dict = {KeyData.MSG: "Welcome to the server"}
    out_data: bytes = Encoder.encode(info, ResponseCode.OK)
    conn.send(out_data)

    # delete these variables so it does not cause collisions in the future
    del out_data, info

    while True:
        encoded_data = conn.recv(SIZE)
        if not encoded_data:
            # If no data is received (client closed connection), break the loop
            break

        in_data: dict = Encoder.decode(encoded_data)

        cmd: Command = in_data[KeyData.CMD]
        match cmd:
            case Command.LOGOUT:
                info: dict = {KeyData.MSG.value: "Disconnecting from server"}
                out_data: bytes = Encoder.encode(info, ResponseCode.DISCONNECT)
                conn.send(out_data)
                break # gets out of the while(true) loop
            case Command.DIR:
                folder_path = in_data[KeyData.REL_PATH]
                info: dict = {KeyData.REL_PATHS: DirHelp.list_directory(SERVER_DIR, folder_path, False)}
                out_data: bytes = Encoder.encode(info, ResponseCode.OK)
                conn.send(out_data)
            case Command.TREE:
                folder_path = in_data[KeyData.REL_PATH]
                info: dict = {KeyData.REL_PATHS: DirHelp.list_directory(SERVER_DIR, folder_path, True)}
                out_data: bytes = Encoder.encode(info, ResponseCode.OK)
                conn.send(out_data)
            case Command.HELP:
                info: dict = {KeyData.MSG: cmd_str()}
                out_data: bytes = Encoder.encode(info, ResponseCode.OK)
                conn.send(out_data)
            case Command.UPLOAD:
                directory: RelativePath = in_data[KeyData.REL_PATH]
                file_name: str = in_data[KeyData.FILE_NAME]

                # FOR NOW: always sends OK, even if not OK
                out_data: bytes = Encoder.encode({}, ResponseCode.OK)
                conn.send(out_data)

                # receives the file
                worked:bool = Transfer.recv_file(conn, SERVER_DIR, directory, file_name)

                # sends back if it worked or not
                if worked:
                    info_2: dict = {KeyData.MSG: "File uploaded successfully"}
                    out_data_2: bytes = Encoder.encode(info_2, ResponseCode.OK)
                else:
                    info_2: dict = {KeyData.MSG: "File upload failed"}
                    out_data_2: bytes = Encoder.encode(info_2, ResponseCode.ERROR)

                conn.send(out_data_2)

            
            # default case
            case _:
                info: dict = {KeyData.MSG: "Invalid command received"}
                out_data: bytes = Encoder.encode(info, ResponseCode.INVALID_CMD)
                conn.send(out_data)

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


