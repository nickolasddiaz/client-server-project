# this file lists all commands to be used in client.py and server.py

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
    ECHO = auto(), "Echo a message to yourself"
    DELETE = auto(), "Delete a file"
    DIR = auto(), "Show the directory"
    TREE = auto(), "Show every file recursively"
    DOWNLOAD = auto(), "Download a file"
    HELP = auto(), "Show all available commands"
    LOGOUT = auto(), "Log out"
    UPLOAD = auto(), "Upload a file"

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
    INVALID_CMD = auto(), f"Invalid command:\n {Command.cmd_str()}"
    INVALID_ARGS = auto(), "Invalid arguments"
    LOGIN_NEEDED = auto(), "Login required"
    PASS_NEEDED = auto(), "Password required"
    USER_NEEDED = auto(), "Username required"
    UPLOAD_FAILED = auto(), "Upload failed"
    SERVER_NOT_READY = auto(), "Server not ready"

    def __new__(cls, num: int, desc: str):
        obj = int.__new__(cls,num)
        obj._value_ = num
        obj.desc = desc
        return obj

class KeyData(IntEnum):
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

