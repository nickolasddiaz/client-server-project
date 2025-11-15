import socket
import threading
from pathlib import Path
from zipfile import ZIP_DEFLATED

from zipstream import ZipStream

from database import DataStorage
from encoder import Encoder
from file_transfer import Transfer
from settings import Settings
from type import Command, ResCode, KeyData, SIZE
from relativepath import RelativePath

# localhost if needed
sett = Settings()
SERVER_DIR = RelativePath.from_base("server_location")
SERVER_DIR.path().mkdir(parents=True, exist_ok=True)

### to handle the clients
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    info: dict = {KeyData.MSG: "Welcome to the server: Type help to list all available commands if in CLI or right click for the GUI"}
    out_data: bytes = Encoder.encode(info, ResCode.OK)
    conn.send(out_data)

    # delete these variables so it does not cause collisions in the future
    del out_data, info
    Data = DataStorage()

    while True:
        encoded_data = conn.recv(SIZE)
        if not encoded_data:
            # If no data is received (client closed connection), break the loop
            break

        in_data: dict = Encoder.decode(encoded_data)

        cmd: Command = in_data[KeyData.CMD]
        match cmd:
            case Command.VERIFY_RES:
                is_dir: bool = in_data[KeyData.IS_DIR]
                exists: bool = in_data[KeyData.EXISTS]
                rel_path: RelativePath = SERVER_DIR / in_data[KeyData.REL_PATH]

                if rel_path.path().exists() ^ exists:
                    out_data: bytes = Encoder.encode({}, ResCode.EXISTS)

                elif exists and is_dir is not None and (rel_path.path().is_dir() ^ is_dir):
                    res: ResCode = ResCode.DIRECTORY_NEEDED if is_dir else ResCode.FILE_NEEDED
                    out_data: bytes = Encoder.encode({}, res)

                else:
                    out_data: bytes = Encoder.encode({}, ResCode.OK)

                conn.send(out_data)

            case Command.VERIFY_PAS:
                username: str = in_data[KeyData.USER_NAME]
                password: str = in_data[KeyData.PASSWORD]

                #verified = Data.verify_user(username, password)
                verified = True

                # check if it is ok or not will be implemented
                if verified:
                    out_data: bytes = Encoder.encode({}, ResCode.OK)
                else:
                    out_data: bytes = Encoder.encode({}, ResCode.AUTH_FAILED)
                conn.send(out_data)

            case Command.LOGOUT:
                out_data: bytes = Encoder.encode({}, ResCode.DISCONNECT)
                conn.send(out_data)
                break  # gets out of the while(true) loop

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
                byte_files: int = in_data[KeyData.BYTES]

                # Validate directory exists
                target_dir = SERVER_DIR / directory
                if not target_dir.path().exists() or not target_dir.path().is_dir():
                    out_data: bytes = Encoder.encode({},ResCode.DIRECTORY_NEEDED)
                    conn.send(out_data)
                    continue

                # Send OK to start receiving file
                out_data: bytes = Encoder.encode({}, ResCode.OK)
                conn.send(out_data)

                # Receive the file using safe path resolution
                safe_dir = Transfer.file_traversal(SERVER_DIR.path(), directory.path())
                worked: bool = Transfer.recv_file(conn, safe_dir, byte_files)

                # Send back if it worked or not
                if worked:
                    info_2: dict = {KeyData.MSG: "File uploaded successfully"}
                    out_data_2: bytes = Encoder.encode(info_2, ResCode.OK)
                else:
                    out_data_2: bytes = Encoder.encode({}, ResCode.UPLOAD_FAILED)

                conn.send(out_data_2)

            case Command.DOWNLOAD:
                file_paths: list[RelativePath] = in_data[KeyData.REL_PATHS]

                zs = ZipStream(compress_type=ZIP_DEFLATED, compress_level=6) # high compression level, 1-7

                num_bytes: int = 0 # approximated size

                for file_path in file_paths:
                    full_path = SERVER_DIR / file_path
                    if not full_path.path().exists() or (full_path.path().is_dir() and not any(full_path.path().iterdir())):
                        continue

                    safe_path = Transfer.file_traversal(SERVER_DIR.path(), file_path.path())

                    num_bytes += int(safe_path.stat().st_size) # approximation not perfectly accurate

                    zs.add_path(safe_path)

                if zs.is_empty():
                    out_data: bytes = Encoder.encode({}, ResCode.NO_FIlES_SELECTED)
                    conn.send(out_data)
                    continue

                # Send the amount of bytes client
                info: dict = {
                    KeyData.BYTES: num_bytes,
                }
                out_data: bytes = Encoder.encode(info, ResCode.OK)
                conn.send(out_data)

                # Wait for client confirmation
                in_data_2 = conn.recv(SIZE)
                response_2: dict = Encoder.decode(in_data_2)
                response_cmd_2: ResCode = response_2[KeyData.CMD]

                if response_cmd_2 == ResCode.CANCEL:
                    print("Client cancelled download")
                    continue

                if response_cmd_2 != ResCode.OK:
                    print(f"Unexpected response from client: {response_cmd_2}")
                    continue

                # Send the file
                succeeded: bool = Transfer.send_file(conn, zs, num_bytes)

                if succeeded:
                    print(f"File sent successfully to {addr}")
                else:
                    print(f"Failed to send file to {addr}")

            case Command.CD:
                selected_path: RelativePath = in_data[KeyData.REL_PATH]

                if selected_path.isdir and (SERVER_DIR / selected_path).path().exists():
                    out_data: bytes = Encoder.encode({}, ResCode.OK)
                else:
                    out_data: bytes = Encoder.encode({}, ResCode.EXISTS)

                conn.send(out_data)

            case Command.RMDIR | Command.DELETE:
                selected_path: RelativePath = in_data[KeyData.REL_PATH]

                if Transfer.recursively_remove_dir(SERVER_DIR.path(), selected_path.path()):
                    out_data: bytes = Encoder.encode({}, ResCode.OK)
                else:
                    out_data: bytes = Encoder.encode({}, ResCode.EXISTS)
                conn.send(out_data)

            case Command.MKDIR:
                selected_path: RelativePath = in_data[KeyData.REL_PATH]

                if Transfer.create_directory(SERVER_DIR.path(), selected_path.path()):
                    out_data: bytes = Encoder.encode({}, ResCode.OK)
                else:
                    out_data: bytes = Encoder.encode({}, ResCode.EXISTS)
                conn.send(out_data)

            case Command.STATS:
                out_data: bytes = Encoder.encode({KeyData.STATS: "Dummy stats"}, ResCode.OK)
                conn.send(out_data)

            # default case
            case _:
                out_data: bytes = Encoder.encode({}, ResCode.INVALID_CMD)
                conn.send(out_data)

    print(f"{addr} disconnected")
    conn.close()


def list_directory(server_dir: RelativePath, base_dir: RelativePath, recursive: bool) -> list[RelativePath]:
    """
    Private function to take in a Path/directory and return the list of starting_path
    Used for sending the TREE and DIR commands
    """
    assert base_dir.isdir, f"Input needs to be a directory not a file: {base_dir}"

    file_list = []

    base_path: Path = Transfer.file_traversal(server_dir.path(), base_dir.path())

    # rglob represents all files recursively while glob is not recursive
    iterator = base_path.rglob('*') if recursive else base_path.glob('*')

    for file_path_obj in iterator:
        file_list.append(RelativePath.from_path(file_path_obj, base_path))

    return file_list


def main():
    print("Starting the server")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  ## used IPV4 and TCP connection
    server.bind(sett.SERVER_ADDR)  # bind the address
    server.listen()  ## start listening
    print(f"server is listening on {sett.SERVER_IP}:{sett.PORT}")
    while True:
        conn, addr = server.accept()  ### accept a connection from a client
        thread = threading.Thread(target=handle_client, args=(conn, addr))  ## assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()