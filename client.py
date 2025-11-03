import socket
from type import Command, ResponseCode, cmd_str, KeyData
from encoder import Encoder


# localhost if needed
IP = "localhost"
PORT = 4453
ADDR = (IP,PORT)
SIZE = 1024 ## byte .. buffer size

def main():
    
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)
    while True:  ### multiple communications
        encoded_data = client.recv(SIZE)
        response: dict = Encoder.server_decode(encoded_data)

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

        data = input("> ") 
        data = data.split(" ")
        cmd: str = data[0]

        match cmd.upper():
            case Command.LOGOUT.name:
                data: bytes = Encoder.encode({}, Command.LOGOUT)
                client.send(data)
            case Command.UPLOAD.name:
                data: bytes = Encoder.encode({}, Command.UPLOAD)
                client.send(data)
            case Command.DOWNLOAD.name:
                data: bytes = Encoder.encode({}, Command.DOWNLOAD)
                client.send(data)
            case Command.DELETE.name:
                data: bytes = Encoder.encode({}, Command.DELETE)
                client.send(data)
            case Command.DIR.name:
                data: bytes = Encoder.encode({}, Command.DIR)
                client.send(data)
            case Command.TREE.name:
                data: bytes = Encoder.encode({}, Command.TREE)
                client.send(data)
            case Command.HELP.name:
                data: bytes = Encoder.encode({}, Command.HELP)
                client.send(data)
            # default case
            case _:
                print(ResponseCode.INVALID_CMD.desc)
                data: bytes = Encoder.encode({}, Command.HELP)
                client.send(data)




    print("Disconnected from the server.")
    client.close() ## close the connection

if __name__ == "__main__":
    main()
