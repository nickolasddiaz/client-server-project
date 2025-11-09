import socket
import threading
from pathlib import Path

from encoder import Encoder
from file_transfer import Transfer
from type import Command, ResCode, KeyData, SIZE
from relativepath import RelativePath

# localhost if needed
IP = "0.0.0.0"
PORT = 4453
ADDR = (IP,PORT)
SERVER_DIR = RelativePath.from_base("server_location")

### to handle the clients
def handle_client (conn,addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    info: dict = {KeyData.MSG: "Welcome to the server: Type help to list all available commands"}
    out_data: bytes = Encoder.encode(info, ResCode.OK)
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
                out_data: bytes = Encoder.encode(info, ResCode.DISCONNECT)
                conn.send(out_data)
                break # gets out of the while(true) loop
            case Command.DIR:
                folder_path = in_data[KeyData.REL_PATH]
                info: dict = {KeyData.REL_PATHS: list_directory(SERVER_DIR, folder_path, False)}
                out_data: bytes = Encoder.encode(info, ResCode.OK)
                conn.send(out_data)
            case Command.TREE:
                folder_path = in_data[KeyData.REL_PATH]
                info: dict = {KeyData.REL_PATHS: list_directory(SERVER_DIR, folder_path, True)}
                out_data: bytes = Encoder.encode(info, ResCode.OK)
                conn.send(out_data)
            case Command.UPLOAD:
                directory: RelativePath = in_data[KeyData.REL_PATH]
                file_name: str = in_data[KeyData.FILE_NAME]

                if not (SERVER_DIR / directory).path().exists():
                    out_data: bytes = Encoder.encode({}, ResCode.FILE_EXISTS)
                else:
                    out_data: bytes = Encoder.encode({}, ResCode.OK)

                conn.send(out_data)

                # receives the file
                worked:bool = Transfer.recv_file(conn, SERVER_DIR, directory, file_name)

                # sends back if it worked or not
                if worked:
                    info_2: dict = {KeyData.MSG: "File uploaded successfully"}
                    out_data_2: bytes = Encoder.encode(info_2, ResCode.OK)
                else:
                    info_2: dict = {KeyData.MSG: "File upload failed"}
                    out_data_2: bytes = Encoder.encode(info_2, ResCode.ERROR)

                conn.send(out_data_2)


            case Command.DOWNLOAD:
                directory: RelativePath = in_data[KeyData.REL_PATH]

                if (SERVER_DIR / directory).path().exists():
                    out_data: bytes = Encoder.encode({}, ResCode.FILE_NOT_FOUND)
                else:
                    out_data: bytes = Encoder.encode({}, ResCode.OK)
                    
                conn.send(out_data)

                base_path: Path = SERVER_DIR.path() / directory.path()

                # Fixes directory traversal vulnerability
                if not base_path.is_relative_to(SERVER_DIR.path()):
                    base_path = SERVER_DIR.path()


                # send the file
                worked:bool = Transfer.send_file(conn, base_path / file_name)

                # sends back if it worked or not
                if worked:
                    info_2: dict = {KeyData.MSG: "File downloaded successfully"}
                    out_data_2: bytes = Encoder.encode(info_2, ResCode.OK)
                else:
                    info_2: dict = {KeyData.MSG: "File download failed"}
                    out_data_2: bytes = Encoder.encode(info_2, ResCode.ERROR)

                conn.send(out_data_2)

            
            case Command.CD:
                selected_path: RelativePath = in_data[KeyData.REL_PATH]

                if selected_path.isdir and (SERVER_DIR / selected_path).path().exists():
                    info: dict = {KeyData.REL_PATH: selected_path}
                    out_data: bytes = Encoder.encode(info, ResCode.OK)
                else:
                    out_data: bytes = Encoder.encode({}, ResCode.INVALID_DIR)

                conn.send(out_data)
                

            # default case
            case _:
                info: dict = {KeyData.MSG: "Invalid command received"}
                out_data: bytes = Encoder.encode(info, ResCode.INVALID_CMD)
                conn.send(out_data)

    print(f"{addr} disconnected")
    conn.close()


def list_directory(server_dir: RelativePath, base_dir: RelativePath, recursive: bool)-> list[RelativePath]:
    """
    Private function to take in a Path/directory and return the list of starting_path
    Used for sending the TREE and DIR commands
    """
    assert base_dir.isdir, f"Input needs to be a directory not a file: {base_dir}"

    file_list = []
    base_path: Path = server_dir.path() / base_dir.path()

    # Fixes directory traversal vulnerability
    if not base_path.is_relative_to(server_dir.path()):
        base_path = server_dir.path()

    # rglob represents all files recursively while glob is not recursive
    iterator = base_path.rglob('*') if recursive else base_path.glob('*')

    # potential features show files size and modification date
    # doesn't show any directory info
    for file_path_obj in iterator:
        file_list.append(RelativePath.from_path(file_path_obj, server_dir.path()))

    return file_list


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


