# client device runs this program

import socket
from pathlib import Path

from directory_func import DirectoryHelper
from type import Command, ResponseCode, cmd_str, KeyData, SIZE
from encoder import Encoder

from tkinter import filedialog as fd
import tkinter as tk


# localhost if needed
IP = "localhost"
PORT = 4453
ADDR = (IP,PORT)
Dir_Help = DirectoryHelper()

def main():
    
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)
    have_input = True
    while True:  ### multiple communications

        if have_input:
            encoded_data: bytes = client.recv(SIZE)
            response: dict = Encoder.decode(encoded_data)

            response_cmd: ResponseCode = response[KeyData.CMD]
            msg: str = response[KeyData.MSG]
            print(msg)

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
                client.send(out_data)
            case Command.DOWNLOAD.name:
                
                # server_paths = open_path_server()
                out_data: bytes = Encoder.encode({}, Command.DOWNLOAD)
                client.send(out_data)
            case Command.DELETE.name:
                out_data: bytes = Encoder.encode({}, Command.DELETE)
                client.send(out_data)
            case Command.DIR.name:
                out_data: bytes = Encoder.encode({}, Command.DIR)
                client.send(out_data)
            case Command.TREE.name:
                out_data: bytes = Encoder.encode({}, Command.TREE)
                client.send(out_data)
            case Command.HELP.name:
                out_data: bytes = Encoder.encode({}, Command.HELP)
                client.send(out_data)
            case Command.UPLOAD.name:
                # sends upload directory to server, to be uploaded
                client_paths: Path = Dir_Help.open_path_client()
                out_data: bytes = Encoder.encode({KeyData.FILE_NAME: client_paths.name}, Command.UPLOAD)
                client.send(out_data)

                # receives an OK to send the file
                in_data_2 = client.recv(SIZE)
                response_2: dict = Encoder.decode(in_data_2)
                response_cmd_2: ResponseCode = response_2[KeyData.CMD]
                if response_cmd_2 == ResponseCode.OK:
                    print("Server is ready to receive the file.")
                else:
                    print("Server is not ready to receive the file.")
                    continue

                # sending the file
                Dir_Help.send_file(client, client_paths)

                # handle the server response after upload
                in_data_3 = client.recv(SIZE)
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
                client.send(data)




    print("Disconnected from the server.")
    client.close() ## close the connection

if __name__ == "__main__":
    main()
