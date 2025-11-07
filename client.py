# client device runs this program

import socket
from pathlib import Path

from directory_func import DirHelp
from file_transfer import Transfer
from relativepath import RelativePath
from type import Command, ResponseCode, cmd_str, KeyData, SIZE
from encoder import Encoder


# localhost if needed
IP = "localhost"
PORT = 4453
ADDR = (IP,PORT)

def main():
    
    conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    conn.connect(ADDR)
    have_input = True
    current_dir: RelativePath = RelativePath.from_base()
    while True:  ### multiple communications

        if have_input:
            encoded_data: bytes = conn.recv(SIZE)
            response: dict = Encoder.decode(encoded_data)

            response_cmd: ResponseCode = response[KeyData.CMD]
            msg: str|None = response.get(KeyData.MSG)
            if msg:
                print(msg)

            in_paths: list[RelativePath] | None = response.get(KeyData.REL_PATHS)
            if in_paths:
                print(DirHelp.str_paths(in_paths))

            if response_cmd != ResponseCode.OK:
                print(response_cmd.desc, "\n")

            match response_cmd:
                case ResponseCode.DISCONNECT:
                    break
                case ResponseCode.INVALID_CMD:
                    print(cmd_str())

        have_input = True
        in_data = input("> ")
        in_data = in_data.split(" ")
        in_cmd: str = in_data[0]

        match in_cmd.upper():
            case Command.LOGOUT.name:
                out_data: bytes = Encoder.encode({}, Command.LOGOUT)
                conn.send(out_data)
            case Command.DOWNLOAD.name:
                
                # server_paths = open_path_server()
                out_data: bytes = Encoder.encode({}, Command.DOWNLOAD)
                conn.send(out_data)
            case Command.DELETE.name:
                out_data: bytes = Encoder.encode({}, Command.DELETE)
                conn.send(out_data)
            case Command.DIR.name:
                out_data: bytes = Encoder.encode({KeyData.REL_PATH: current_dir}, Command.DIR)
                conn.send(out_data)
            case Command.TREE.name:
                out_data: bytes = Encoder.encode({KeyData.REL_PATH: current_dir}, Command.TREE)
                conn.send(out_data)
            case Command.HELP.name:
                out_data: bytes = Encoder.encode({}, Command.HELP)
                conn.send(out_data)
            case Command.UPLOAD.name:
                # sends upload directory to server, to be uploaded
                test = DirHelp.select_file_server(conn, current_dir, True)
                client_paths: Path = DirHelp.select_file_client()
                out_dict: dict = {KeyData.FILE_NAME: client_paths.name, KeyData.REL_PATH: current_dir}
                out_data: bytes = Encoder.encode(out_dict, Command.UPLOAD)
                conn.send(out_data)

                # receives an OK to send the file
                in_data_2 = conn.recv(SIZE)
                response_2: dict = Encoder.decode(in_data_2)
                response_cmd_2: ResponseCode = response_2[KeyData.CMD]
                if response_cmd_2 == ResponseCode.OK:
                    print("Server is ready to receive the file.")
                else:
                    print("Server is not ready to receive the file.")
                    continue

                # sending the file
                Transfer.send_file(conn, client_paths)

                # handle the server response after upload
                in_data_3 = conn.recv(SIZE)
                response_3: dict = Encoder.decode(in_data_3)
                response_cmd_3: ResponseCode = response_3[KeyData.CMD]
                if response_cmd_3 == ResponseCode.OK:
                    print("File uploaded successfully.")
                else:
                    print("File upload failed.")

                have_input = False

            # default case
            case _:
                print(ResponseCode.INVALID_CMD.desc)
                data: bytes = Encoder.encode({}, Command.HELP)
                conn.send(data)




    print("Disconnected from the server.")
    conn.close() ## close the connection

if __name__ == "__main__":
    main()
