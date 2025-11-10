import socket
from pathlib import Path

from file_transfer import Transfer
from relativepath import RelativePath
from type import Command, ResCode, KeyData, SIZE
from encoder import Encoder

from abc import ABC, abstractmethod


class ClientInterface(ABC):

    def __init__(self):
        self.IP: str = "localhost"
        self.PORT: int = 4453
        self.ADDR: tuple[str, int] = (self.IP, self.PORT)
        self.current_dir: RelativePath = RelativePath.from_base()
        self.conn = None
        self.local_user: str = ""
        self.local_pass: str = ""

    def run(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(self.ADDR)
        skip_server_input: bool = True
        while True:  ### multiple communications

            if skip_server_input:
                encoded_data: bytes = self.conn.recv(SIZE)
                response: dict = Encoder.decode(encoded_data)

                response_cmd: ResCode = response[KeyData.CMD]
                msg: str | None = response.get(KeyData.MSG)
                if msg:
                    self.app_print(msg)

                if response_cmd != ResCode.OK:
                    self.app_error(response_cmd)

                if response_cmd == ResCode.DISCONNECT:
                    break

                in_paths: list[RelativePath] | None = response.get(KeyData.REL_PATHS)
                if in_paths:
                    self.show_dir(in_paths)

            skip_server_input = True

            in_cmd: Command = self.command_input()

            match in_cmd:
                case Command.CLS:
                    self.clear_screen()
                    skip_server_input = False

                case Command.LOGOUT:
                    out_data: bytes = Encoder.encode({}, Command.LOGOUT)
                    self.conn.send(out_data)

                case Command.DIR:
                    out_data: bytes = Encoder.encode({KeyData.REL_PATH: self.current_dir}, Command.DIR)
                    self.conn.send(out_data)

                case Command.TREE:
                    out_data: bytes = Encoder.encode({KeyData.REL_PATH: self.current_dir}, Command.TREE)
                    self.conn.send(out_data)

                case Command.HELP:
                    self.app_print(Command.cmd_str())
                    skip_server_input = False

                case Command.UPLOAD:
                    skip_server_input = False
                    client_paths: list[tuple[Path, str]] = self.select_client_files()

                    for client_path, file_name in client_paths:
                        byte_file = client_path.stat().st_size

                        # sends upload directory to server, to be uploaded
                        out_dict: dict = {
                            KeyData.REL_PATH: self.current_dir,
                            KeyData.FILE_NAME: file_name,
                            KeyData.BYTES: byte_file
                        }
                        out_data: bytes = Encoder.encode(out_dict, Command.UPLOAD)
                        self.conn.send(out_data)

                        # receives an OK to send the file
                        in_data_2 = self.conn.recv(SIZE)
                        response_2: dict = Encoder.decode(in_data_2)
                        response_cmd_2: ResCode = response_2[KeyData.CMD]
                        if response_cmd_2 != ResCode.OK:
                            self.app_error(response_cmd_2)
                            continue

                        # sending the file
                        self.app_print(f"Uploading {file_name}...")
                        succeeded: bool = Transfer.send_file(self.conn, client_path, byte_file)
                        if not succeeded:
                            self.app_error_print(f"File {file_name} failed to be transferred")
                            continue

                        # handle the server response after upload
                        in_data_3 = self.conn.recv(SIZE)
                        response_3: dict = Encoder.decode(in_data_3)
                        response_cmd_3: ResCode = response_3[KeyData.CMD]
                        if response_cmd_3 == ResCode.OK:
                            self.app_print(f"File {client_path.name} uploaded successfully.")
                        else:
                            self.app_error(response_cmd_3)
                            self.app_error_print(f"File {client_path.name} failed to be transferred")

                case Command.DOWNLOAD:
                    skip_server_input = False
                    server_files: list[RelativePath] = self.select_server_files()

                    for server_file in server_files:
                        # Request download from server
                        out_dict: dict = {KeyData.REL_PATH: server_file}
                        out_data: bytes = Encoder.encode(out_dict, Command.DOWNLOAD)
                        self.conn.send(out_data)

                        # Receive server response with file info
                        in_data_1 = self.conn.recv(SIZE)
                        response_1: dict = Encoder.decode(in_data_1)
                        response_cmd_1: ResCode = response_1[KeyData.CMD]

                        if response_cmd_1 != ResCode.OK:
                            self.app_error(response_cmd_1)
                            self.app_error_print(f"Cannot download {server_file.location}")
                            continue

                        # Get file info from response
                        file_name: str = response_1[KeyData.FILE_NAME]
                        byte_file: int = response_1[KeyData.BYTES]

                        # Select local directory to save file
                        local_dir: Path | None = self.select_client_dir()
                        if local_dir is None:
                            self.app_print("Download cancelled")
                            # Send cancel message to server
                            cancel_data: bytes = Encoder.encode({}, ResCode.CANCEL)
                            self.conn.send(cancel_data)
                            continue

                        # Check if file already exists locally
                        local_file_path = local_dir / file_name
                        if local_file_path.exists():
                            new_name = self.rename_file(file_name)
                            if new_name:
                                file_name = new_name
                            else:
                                self.app_print("Download cancelled")
                                cancel_data: bytes = Encoder.encode({}, ResCode.CANCEL)
                                self.conn.send(cancel_data)
                                continue

                        # Send OK to start receiving file
                        ok_data: bytes = Encoder.encode({}, ResCode.OK)
                        self.conn.send(ok_data)

                        # Receive the file
                        self.app_print(f"Downloading {file_name}...")
                        succeeded: bool = Transfer.recv_file(self.conn, local_dir, file_name, byte_file)

                        if succeeded:
                            self.app_print(f"File {file_name} downloaded successfully to {local_dir}")
                        else:
                            self.app_error_print(f"File {file_name} failed to download")

                case Command.CD:
                    skip_server_input = False
                    # get the selected directory from user
                    selected_path: RelativePath | None = self.select_server_dir(True)
                    if selected_path is None:
                        self.app_print("Exited out of CD")
                        continue

                    out_data: bytes = Encoder.encode({KeyData.REL_PATH: selected_path}, Command.CD)
                    # send to data to the server
                    self.conn.send(out_data)

                    # receive server response if it is a valid directory
                    in_data = self.conn.recv(SIZE)
                    response: dict = Encoder.decode(in_data)
                    response_cmd: ResCode = response[KeyData.CMD]
                    if response_cmd == ResCode.OK:
                        self.current_dir = selected_path
                        self.app_print(f"Changed directory to {self.current_dir.location}")
                    else:
                        self.app_error(response_cmd)

                case Command.RMDIR:
                    skip_server_input = False
                    # get the selected directory from user
                    selected_path: RelativePath | None = self.select_server_dir(True)
                    if selected_path is None:
                        self.app_print("Exited out of RMDIR")
                        continue

                    out_data: bytes = Encoder.encode({KeyData.REL_PATH: selected_path}, Command.RMDIR)
                    # send to data to the server
                    self.conn.send(out_data)

                    # receive server response if it is a valid directory
                    in_data = self.conn.recv(SIZE)
                    response: dict = Encoder.decode(in_data)
                    response_cmd: ResCode = response[KeyData.CMD]
                    if response_cmd == ResCode.OK:
                        self.app_print(f"Removed directory {selected_path}")
                    else:
                        self.app_error(response_cmd)

                case Command.MKDIR:
                    skip_server_input = False
                    # get the selected directory from user
                    selected_path: RelativePath | None = self.select_server_dir(False, True)
                    if selected_path is None:
                        self.app_print("Exited out of MKDIR")
                        continue

                    out_data: bytes = Encoder.encode({KeyData.REL_PATH: selected_path}, Command.MKDIR)
                    # send to data to the server
                    self.conn.send(out_data)

                    # receive server response if it is a valid directory
                    in_data = self.conn.recv(SIZE)
                    response: dict = Encoder.decode(in_data)
                    response_cmd: ResCode = response[KeyData.CMD]
                    if response_cmd == ResCode.OK:
                        self.app_print(f"Added directory {selected_path}")
                    else:
                        self.app_error(response_cmd)

                case Command.DELETE:
                    skip_server_input = False
                    selected_paths: list[RelativePath] = self.select_server_files()
                    for selected_path in selected_paths:
                        out_data: bytes = Encoder.encode({KeyData.REL_PATH:selected_path}, Command.DELETE)
                        self.conn.send(out_data)

                        in_data = self.conn.recv(SIZE)
                        response: dict = Encoder.decode(in_data)
                        response_cmd: ResCode = response[KeyData.CMD]
                        if response_cmd == ResCode.OK:
                            self.app_print(f"Deleted directory {selected_path}")
                        else:
                            self.app_error(response_cmd)


                # default case
                case _:
                    self.app_error(ResCode.INVALID_CMD)
                    skip_server_input = False

        self.app_error(ResCode.DISCONNECT)
        self.conn.close()  ## close the connection
        self.app_exit()

    def verify(self, is_dir: bool, exists: bool, rel_path: RelativePath) -> ResCode:
        out_dict = {KeyData.IS_DIR: is_dir, KeyData.EXISTS: exists, KeyData.REL_PATH: rel_path}
        out_data: bytes = Encoder.encode(out_dict, Command.VERIFY)
        self.conn.send(out_data)

        in_data = self.conn.recv(SIZE)
        response: dict = Encoder.decode(in_data)
        response_cmd: ResCode = response[KeyData.CMD]

        return response_cmd

    @abstractmethod
    def clear_screen(self) -> None:
        pass

    @abstractmethod
    def rename_file_error(self, file_name: str) -> str:
        pass

    @abstractmethod
    def rename_file(self, file_name: str) -> str:
        pass

    @abstractmethod
    def app_exit(self) -> None:
        pass

    @abstractmethod
    def app_error(self, status: ResCode) -> None:
        pass

    @abstractmethod
    def app_print(self, msg: str) -> None:
        pass

    @abstractmethod
    def app_error_print(self, msg: str) -> None:
        pass

    @abstractmethod
    def app_print_statistics(self, msg: str) -> None:
        pass

    @abstractmethod
    def command_input(self) -> Command:
        pass

    @abstractmethod
    def show_dir(self, rel_paths: list[RelativePath]) -> None:
        pass

    @abstractmethod
    def receive_user_pass(self) -> None:
        pass

    @abstractmethod
    def select_server_dir(self, exists: bool, skip_verification: bool = False) -> RelativePath:
        pass

    @abstractmethod
    def select_server_files(self) -> list[RelativePath]:
        pass

    @abstractmethod
    def select_client_files(self) -> list[tuple[Path, str]]:
        pass

    @abstractmethod
    def select_client_dir(self) -> Path | None:
        pass

    @abstractmethod
    def progress_bar(self, progress: int) -> None:
        pass