import os
import socket
import threading
from type import commands, cmd_delim
from deliminer import deliminer, cmd_delim
from pathlib import Path


# localhost if needed
IP = "0.0.0.0"
PORT = 4453
ADDR = (IP,PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_PATH = "server"

### to handle the clients
def handle_client (conn,addr):


    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send(f"OK{cmd_delim}Welcome to the server".encode(FORMAT))
    while True:
        data =  conn.recv(SIZE).decode(FORMAT)
        data = data.split(cmd_delim,1)
        cmd = data[0]
       
        send_data = f"OK{cmd_delim}"

        match cmd:
            case commands.TASK.name:
                send_data += "Task has been processed successfully.\n"
                conn.send(send_data.encode(FORMAT))
            case commands.LOGOUT.name:
                send_data += "You have been logged out successfully.\n"
                conn.send(send_data.encode(FORMAT))
                print(f"{addr} disconnected")
                conn.close()
            case commands.HELP.name:
                send_data += "Available commands:\n"
                for command in commands:
                    send_data += f"{command.name}\n"
                conn.send(send_data.encode(FORMAT))
            case commands.DIR.name:
                script_dir = Path(__file__).parent.resolve()
                folder_path = script_dir / "server_location" 

                all_files = get_all_files(folder_path)
                for f in all_files:
                    send_data += f"{f}\n"
                conn.send(send_data.encode(FORMAT))
            # default case
            case _:
                send_data += "Invalid command received.\n"
                conn.send(send_data.encode(FORMAT))
                

        



    print(f"{addr} disconnected")
    conn.close()

def get_all_files(base_directory):
    """
    Retrieves a list of all files with paths relative to the base_directory
    using pathlib.
    """
    # Create a Path object for the base directory
    base_path = Path(base_directory)
    
    file_list = []
    # Use rglob to recursively find all files
    for file_path_obj in base_path.rglob('*'):
        if file_path_obj.is_file():
            # The relative_to() method calculates the relative path
            relative_path = file_path_obj.relative_to(base_path)
            # Add the string representation of the path to our list
            file_list.append(str(relative_path))
            
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


