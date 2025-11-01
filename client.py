import os
import socket
import threading
from type import commands
from deliminer import deliminer, cmd_delim


# localhost if needed
IP = "localhost"
PORT = 4453
ADDR = (IP,PORT)
SIZE = 1024 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"

def main():
    
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)
    while True:  ### multiple communications
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split(cmd_delim,1)
        if cmd == "OK":
            print(f"{msg}")
        elif cmd == "DISCONNECTED":
            print(f"{msg}")
            break
        
        data = input("> ") 
        data = data.split(" ")
        cmd = data[0]

        match cmd:
            case commands.TASK.name:
                client.send(cmd.encode(FORMAT)) 
            case commands.LOGOUT.name:
                client.send(cmd.encode(FORMAT)) 
            case commands.HELP.name:
                client.send(cmd.encode(FORMAT)) 
            case commands.UPLOAD.name:
                client.send(cmd.encode(FORMAT))
            case commands.DOWNLOAD.name:
                client.send(cmd.encode(FORMAT))
            case commands.DELETE.name:
                client.send(cmd.encode(FORMAT))
            case commands.DIR.name:
                client.send(cmd.encode(FORMAT))
            case commands.SUBFOLDER.name:
                client.send(cmd.encode(FORMAT))
            # default case
            case _:
                client.send(cmd.encode(FORMAT))




    print("Disconnected from the server.")
    client.close() ## close the connection

if __name__ == "__main__":
    main()
