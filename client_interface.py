# client device runs this program

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

    def run(self):
        self.conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.conn.connect(self.ADDR)
        self.start_program()
        have_input: bool = True
        while True:  ### multiple communications

            if have_input:
                encoded_data: bytes = self.conn.recv(SIZE)
                response: dict = Encoder.decode(encoded_data)

                response_cmd: ResCode = response[KeyData.CMD]
                msg: str|None = response.get(KeyData.MSG)
                if msg:
                    self.app_print(msg)

                if response_cmd != ResCode.OK:
                    self.app_error(response_cmd)

                if response_cmd == ResCode.DISCONNECT:
                    break

                in_paths: list[RelativePath] | None = response.get(KeyData.REL_PATHS)
                if in_paths:
                    self.show_dir(in_paths)

            have_input = True

            in_cmd: Command = self.command_input()

            match in_cmd:
                case Command.LOGOUT:
                    out_data: bytes = Encoder.encode({}, Command.LOGOUT)
                    self.conn.send(out_data)
                case Command.DOWNLOAD:
                    out_data: bytes = Encoder.encode({}, Command.DOWNLOAD)
                    self.conn.send(out_data)
                case Command.DELETE:
                    out_data: bytes = Encoder.encode({}, Command.DELETE)
                    self.conn.send(out_data)
                case Command.DIR:
                    out_data: bytes = Encoder.encode({KeyData.REL_PATH: self.current_dir}, Command.DIR)
                    self.conn.send(out_data)

                case Command.TREE:
                    out_data: bytes = Encoder.encode({KeyData.REL_PATH: self.current_dir}, Command.TREE)
                    self.conn.send(out_data)

                case Command.HELP:
                    self.app_print(Command.cmd_str())
                    have_input = False
                case Command.UPLOAD:
                    # sends upload directory to server, to be uploaded
                    out_dict: dict = {KeyData.REL_PATH: self.current_dir}
                    out_data: bytes = Encoder.encode(out_dict, Command.UPLOAD)
                    self.conn.send(out_data)

                    # receives an OK to send the file
                    in_data_2 = self.conn.recv(SIZE)
                    response_2: dict = Encoder.decode(in_data_2)
                    response_cmd_2: ResCode = response_2[KeyData.CMD]
                    if response_cmd_2 == ResCode.OK:
                        self.app_print("Server is ready to receive the file.")
                    else:
                        self.app_error(response_cmd_2)
                        have_input = False
                        continue

                    # sending the file
                    client_paths: list[Path] = self.select_client_files()
                    Transfer.send_file(self.conn, client_paths)

                    # handle the server response after upload
                    in_data_3 = self.conn.recv(SIZE)
                    response_3: dict = Encoder.decode(in_data_3)
                    response_cmd_3: ResCode = response_3[KeyData.CMD]
                    if response_cmd_3 == ResCode.OK:
                        self.app_print("File uploaded successfully.")
                    else:
                        self.app_error(response_cmd_3)

                    have_input = False

                # default case
                case _:
                    self.app_error(ResCode.INVALID_CMD)
                    have_input = False

        self.app_error(ResCode.DISCONNECT)
        self.conn.close() ## close the connection
        self.app_exit()

    @abstractmethod
    def start_program(self) -> None:
        pass

    @abstractmethod
    def app_exit(self) -> None:
        pass

    @abstractmethod
    def app_error(self, status: ResCode) -> None:
        pass

    @abstractmethod
    def app_print(self, msg:str) -> None:
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
    def receive_user_pass(self) -> tuple[str, str]:
        pass

    @abstractmethod
    def select_server_files(self) -> list[RelativePath]:
        pass

    @abstractmethod
    def select_client_files(self) -> list[Path]:
        pass

    @abstractmethod
    def select_client_dir(self) -> Path|None:
        pass

    @abstractmethod
    def progress_bar(self, progress: int, msg: str) -> None:
        pass



