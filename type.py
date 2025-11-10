"""
Lists all the available commands, response codes and keys used in data dictionaries
(in client_CLI.py, client_interface.py, and server.py). Commands indicate what logic
to perform.
"""
    
from enum import Enum, IntEnum


def format_table(table_data) -> str:
    if not table_data:
        return ""

    # Calculate maximum column widths
    col_widths = [max(len(str(item)) for item in col) for col in zip(*table_data)]

    # Build a list of formatted row strings
    formatted_rows = []
    for row in table_data:
        # Format each item in the row with the correct padding
        padded_items = [str(item).ljust(col_widths[i]) for i, item in enumerate(row)]
        # Join the padded items with a separator to form one row string
        formatted_rows.append("  ".join(padded_items))

    # Join all the row strings with a newline character
    return "\n".join(formatted_rows)


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
    RMDIR = auto(), "Delete a directory"
    MKDIR = auto(), "Create a new directory"
    CLS = auto(), "Clear the screen"
    VERIFY = auto(), "Private command"

    def __new__(cls, num: int, desc: str):
        obj = object.__new__(cls)
        obj._value_ = num
        obj.desc = desc
        return obj

    @staticmethod
    def cmd_str() -> str:
        header = "Available Commands:\n"

        # Convert Enum members to a list of lists, excluding the last one
        table_data = [["Commands", "Description"]]
        for command in list(Command)[:-1]:  # Excludes VERIFY
            table_data.append([command.name, command.desc])

        return format_table(table_data)

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
    INVALID_CMD = auto(), f"{Command.cmd_str()}"
    INVALID_ARGS = auto(), "Invalid arguments"
    LOGIN_NEEDED = auto(), "Login required"
    UPLOAD_FAILED = auto(), "Upload failed"
    SERVER_NOT_READY = auto(), "Server not ready"
    FILE_NOT_FOUND = auto(), "File does not exist"


    DIRECTORY_NEEDED = auto(), "Directory is needed"
    FILE_NEEDED = auto(), "File is needed"

    EXISTS = auto(), "Resource exists"


    PASS_REQUESTED = auto(), "Password requested"
    PASS_REQUIRED = auto(), "Password required"
    AUTH_FAILED = auto(), "Authentication failed"
    CANCEL = auto(), "Cancel requested"

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
    BYTES = auto()

    EXISTS = auto()
    IS_DIR = auto()

    def __int__(self):
        return self.value

if __name__ == "__main__":
    print(Command.cmd_str())
    print(KeyData.MSG)
    print(ResCode.INVALID_CMD)

