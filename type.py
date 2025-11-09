"""
Lists all the available commands, response codes and keys used in data dictionaries
(in client_CLI.py, client_interface.py, and server.py). Commands indicate what logic
to perform.
"""
    
from enum import Enum, IntEnum

SIZE = 1024

def auto() -> int:
    """
    Overriding the auto() function to make sure multiple enums have different values
    """
    if not hasattr(auto, 'counter'):
        auto.counter = 0
    auto.counter += 1
    return auto.counter

class Command(Enum):
    """
    Enum for all the available commands
    """
    DELETE = auto(), "Delete a file"
    DIR = auto(), "Show the directory"
    TREE = auto(), "Show every file recursively"
    DOWNLOAD = auto(), "Download a file"
    HELP = auto(), "Show all available commands"
    LOGOUT = auto(), "Log out"
    UPLOAD = auto(), "Upload a file"
    CD = auto(), "Change directory"
    RMDIR = auto(), "Delete a folder/directory"

    def __new__(cls, num: int, desc: str):
        obj = object.__new__(cls)
        obj._value_ = num
        obj.desc = desc
        return obj

    @staticmethod
    def cmd_str() -> str:
        data = "Available Commands:\n"
        for command in Command:
            data += f"{command.name}: {command.desc}\n"
        return data

    @staticmethod
    def from_str(name: str) -> "Command | None":
        name = name.strip().upper()
        try:
            return Command[name]
        except KeyError:
            return None


class ResCode(IntEnum):
    """
    Enum for all the available response codes
    """
    OK = auto(), "Request accepted"
    ERROR = auto(), "Request failed"
    DISCONNECT = auto(), "Disconnect from server"
    INVALID_CMD = auto(), f"Invalid command:\n{Command.cmd_str()}"
    INVALID_ARGS = auto(), "Invalid arguments"
    LOGIN_NEEDED = auto(), "Login required"
    UPLOAD_FAILED = auto(), "Upload failed"
    SERVER_NOT_READY = auto(), "Server not ready"
    FILE_NOT_FOUND = auto(), "File does not exist"
    DIRECTORY_NEEDED = auto(), "Directory is needed"
    FILE_NEEDED = auto(), "File is needed"
    INVALID_DIR = auto(), "Directory does not exist"
    FILE_EXISTS = auto(), "File already exists"


    PASS_REQUESTED = auto(), "Password requested"
    PASS_REQUIRED = auto(), "Password required"
    AUTH_FAILED = auto(), "Authentication failed"

    def __new__(cls, num: int, desc: str):
        obj = int.__new__(cls,num)
        obj._value_ = num
        obj.desc = desc
        return obj

    def is_auth_related (self) -> bool:
        return ResCode.PASS_REQUESTED.value <= self.value <= ResCode.AUTH_FAILED.value

class KeyData(IntEnum):
    """Enum for all the available keys in the data dictionaries"""
    MSG = auto()
    CMD = auto()
    REL_PATH = auto()
    REL_PATHS = auto()
    FILE_NAME = auto()

    def __int__(self):
        return self.value

if __name__ == "__main__":
    print(Command.cmd_str())
    print(KeyData.MSG)
    print(ResCode.INVALID_CMD)

