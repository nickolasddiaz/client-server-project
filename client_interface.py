import copy
import socket
from pathlib import Path
from zipfile import ZIP_DEFLATED

from zipstream import ZipStream

from file_transfer import Transfer
from relativepath import RelativePath
from settings import Settings
from type import Command, ResCode, KeyData, SIZE, format_bytes, format_time
from encoder import Encoder

from abc import ABC, abstractmethod


class ClientInterface(ABC):
    def __init__(self):
        self.sett = Settings()
        self.current_dir: RelativePath = RelativePath.from_base()
        self.conn = None
        self.PLATFORM: str = ""

    def run(self):

        self.connect_helper()

        # receive initial message
        out_data: bytes = Encoder.encode({KeyData.PLATFORM: self.PLATFORM}, Command.STARTING_MSG)
        self.conn.send(out_data)

        encoded_data: bytes = self.conn.recv(SIZE)
        response: dict = Encoder.decode(encoded_data)

        msg: str | None = response.get(KeyData.MSG)
        if msg:
            self.app_print(msg)

        while True:  ### multiple communications

            in_cmd: Command|None = self.command_input()

            match in_cmd:
                case Command.CLS:
                    self.clear_screen()

                case Command.EXIT:
                    self.app_exit()

                case Command.TREE | Command.DIR:
                    out_data: bytes = Encoder.encode({KeyData.REL_PATH: copy.deepcopy(self.current_dir)}, in_cmd)
                    self.conn.send(out_data)

                    encoded_data: bytes = self.conn.recv(SIZE)
                    response: dict = Encoder.decode(encoded_data)

                    response_cmd: ResCode = response[KeyData.CMD]
                    if response_cmd != ResCode.OK:
                        self.app_error(response_cmd)
                        continue

                    in_paths: list[RelativePath] | None = response.get(KeyData.REL_PATHS)
                    if not in_paths:
                        self.app_print("Directory is Empty")
                        in_paths = []
                    self.show_dir(in_paths)

                case Command.HELP:
                    self.app_print(Command.cmd_str())

                case Command.UPLOAD:
                    client_paths: list[tuple[Path, str]] = self.select_client_files()

                    zs = ZipStream(compress_type=ZIP_DEFLATED, compress_level=self.sett.COMPRESS_LVL) # high compression level, 1-7

                    num_bytes: int = 0  # approximated size

                    for client_path, file_name in client_paths:
                        if not client_path.exists() or (client_path.is_dir() and not any(client_path.iterdir())):
                            continue

                        num_bytes += int(client_path.stat().st_size) # approximation not perfectly accurate

                        zs.add_path(client_path, file_name)

                    if zs.is_empty():
                        self.app_error(ResCode.NO_FIlES_SELECTED)
                        continue


                    out_dict: dict = {
                        KeyData.REL_PATH: self.current_dir,
                        KeyData.BYTES: num_bytes,
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
                    self.app_print("Uploading ...")

                    succeeded: bool = Transfer.send_file(self.conn, zs, num_bytes, self.progress_bar)
                    if not succeeded:
                        self.app_error_print("File failed to be transferred")
                        continue

                    # handle the server response after upload
                    in_data_3 = self.conn.recv(SIZE)
                    self.progress_bar(100,0,0)
                    response_3: dict = Encoder.decode(in_data_3)
                    response_cmd_3: ResCode = response_3[KeyData.CMD]
                    if response_cmd_3 == ResCode.OK:
                        self.app_print("File  uploaded successfully.")
                    else:
                        self.app_error(response_cmd_3)

                case Command.DOWNLOAD:
                    server_files: list[RelativePath] = self.select_server_files()

                    # Select local directory to save file
                    local_dir: Path | None = self.select_client_dir()

                    if local_dir is None:
                        self.app_print("Canceled Download")

                    # Request download from server
                    out_dict: dict = {KeyData.REL_PATHS: server_files}
                    out_data: bytes = Encoder.encode(out_dict, Command.DOWNLOAD)
                    self.conn.send(out_data)

                    # Receive server response with file info
                    in_data_1 = self.conn.recv(SIZE)
                    response_1: dict = Encoder.decode(in_data_1)
                    response_cmd_1: ResCode = response_1[KeyData.CMD]

                    if response_cmd_1 != ResCode.OK:
                        self.app_error(response_cmd_1)
                        del in_data_1
                        continue

                    # Get file info from response
                    byte_file: int = response_1[KeyData.BYTES]

                        # Send OK to start receiving file
                    ok_data: bytes = Encoder.encode({}, ResCode.OK)
                    self.conn.send(ok_data)

                    # Receive the file
                    self.app_print("Downloading")

                    succeeded: bool = Transfer.recv_file(self.conn, local_dir, byte_file, self.progress_bar)

                    if succeeded:
                        self.app_print(f"File downloaded successfully to {local_dir}")
                    else:
                        self.app_error_print("File failed to download")

                case Command.CD:
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

                case Command.MKDIR:
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

                case Command.DELETE | Command.RMDIR:
                    if in_cmd == Command.DELETE:
                        selected_paths = self.select_server_files()
                    else:
                        selected_paths = [self.select_server_dir(True)]

                    for selected_path in selected_paths:
                        if selected_path is None:
                            self.app_print(f"Exited out of {in_cmd.name}")
                            continue
                        out_data: bytes = Encoder.encode({KeyData.REL_PATH:selected_path}, Command.DELETE)
                        self.conn.send(out_data)

                        in_data = self.conn.recv(SIZE)
                        response: dict = Encoder.decode(in_data)
                        response_cmd: ResCode = response[KeyData.CMD]
                        if response_cmd == ResCode.OK:
                            self.app_print(f"Deleted resource {selected_path}")
                        else:
                            self.app_error(response_cmd)

                case Command.STATS:
                    out_data: bytes = Encoder.encode({}, Command.STATS)
                    self.conn.send(out_data)

                    in_data_2 = self.conn.recv(SIZE)
                    response_2: dict = Encoder.decode(in_data_2)
                    response_cmd_2: ResCode = response_2[KeyData.CMD]
                    if response_cmd_2 != ResCode.OK:
                        self.app_error(response_cmd_2)
                        continue

                    self.app_print_statistics(response_2[KeyData.STATS])

                case Command.DISCONNECT:
                    self.connect_helper()
                case Command.LOGOUT:
                    self.sett.AUTH_KEY = ""
                    self.verify_userpass()

                # default case
                case _:
                    self.app_error(ResCode.INVALID_CMD)

        self.app_error(ResCode.DISCONNECT)
        self.conn.close()  ## close the connection
        self.app_exit()

    def verify_resource(self, is_dir: bool|None, exists: bool, rel_path: RelativePath) -> ResCode:
        out_dict = {KeyData.IS_DIR: is_dir, KeyData.EXISTS: exists, KeyData.REL_PATH: rel_path}
        out_data: bytes = Encoder.encode(out_dict, Command.VERIFY_RES)
        self.conn.send(out_data)

        in_data = self.conn.recv(SIZE)
        response: dict = Encoder.decode(in_data)
        response_cmd: ResCode = response[KeyData.CMD]

        return response_cmd

    def connect_helper(self) -> None:
        self.welcome_connection()
        while True:
            ip, port = self.get_connection()
            if port.isdigit() and self.sett.set_client_addr(ip, int(port) & 0xFFFF):
                break

        self.sett.save_changes()

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(self.sett.CLIENT_ADDR)
        self.print_connection_success()

        # go to verify user
        self.verify_userpass()

    def verify_token(self) -> bool:
        if self.sett.AUTH_KEY == "":
            return False

        out_dict = {KeyData.AUTH_TOKEN: self.sett.AUTH_KEY}
        out_data: bytes = Encoder.encode(out_dict, Command.VERIFY_AUTH)
        self.conn.send(out_data)

        in_data = self.conn.recv(SIZE)
        response: dict = Encoder.decode(in_data)
        response_cmd: ResCode = response[KeyData.CMD]

        return response_cmd == ResCode.OK


    def verify_userpass(self) -> None:
        if self.verify_token():
            self.print_login_success()
            return

        self.welcome_login()

        while True:
            username, password = self.get_login()

            out_dict = {KeyData.USER_NAME: username, KeyData.PASSWORD: password}
            out_data: bytes = Encoder.encode(out_dict, Command.VERIFY_PAS)
            self.conn.send(out_data)

            in_data = self.conn.recv(SIZE)
            response: dict = Encoder.decode(in_data)
            response_cmd: ResCode = response[KeyData.CMD]

            if response_cmd == ResCode.OK:
                self.sett.AUTH_KEY = str(response[KeyData.AUTH_TOKEN])
                break
            else:
                self.app_error(response_cmd)

        self.sett.USERNAME = username
        self.sett.PASSWORD = password # password is not saved
        self.sett.save_changes()


        self.print_login_success()

    @abstractmethod
    def welcome_connection(self):
        pass

    @abstractmethod
    def get_connection(self) -> tuple[str,str]:
        pass

    @abstractmethod
    def print_connection_success(self):
        pass

    @abstractmethod
    def welcome_login(self):
        pass

    @abstractmethod
    def get_login(self) -> tuple[str,str]:
        pass

    @abstractmethod
    def print_login_success(self):
        pass

    @abstractmethod
    def clear_screen(self) -> None:
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
    def select_server_dir(self, exists: bool, skip_verification: bool = False) -> RelativePath|None:
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
    def progress_bar(self, progress: int, byte_per_sec: int, num_bytes: int) -> None:
        pass

    @staticmethod
    def progress_str(progress: int, byte_per_sec: int, num_bytes: int) -> str:
        # 0% | 0.00 B/s | 00.00 KB | ETA: ∞

        # Calculate estimated time remaining
        bytes_remaining = num_bytes * (100 - progress) / 100
        if byte_per_sec > 0:
            time_remaining = bytes_remaining / byte_per_sec
        else:
            time_remaining = -1  # Infinite or unknown


        speed_str = format_bytes(byte_per_sec) + "/s"
        total_size_str = format_bytes(num_bytes)
        time_str = format_time(time_remaining)

        return f"{progress}% | {speed_str} | {total_size_str} | ETA: {time_str}"