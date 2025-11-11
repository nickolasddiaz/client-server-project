"""
Lists all the available commands, response codes and keys used in data dictionaries
(in client_CLI.py, client_interface.py, and server.py). Commands indicate what logic
to perform.
"""
from enum import Enum, IntEnum


def format_table(table_data: list[list[str]], header: list[str]) -> str:
    """
    Formats a table with aligned columns, a header, and a separator line.
    Example:
    filename   description
    --------   ------------
    file1.txt  Example file
    """
    if not table_data and not header:
        return ""

    # Combine header and table data temporarily to calculate widths
    combined = [header] + table_data if header else table_data
    col_widths = [max(len(str(item)) for item in col) for col in zip(*combined)]

    formatted_rows = []

    # Format header if present
    if header:
        header_line = "  ".join(str(header[i]).ljust(col_widths[i]) for i in range(len(header)))
        separator_line = "  ".join("-" * col_widths[i] for i in range(len(header)))
        formatted_rows.append(header_line)
        formatted_rows.append(separator_line)

    # Format table data
    for row in table_data:
        padded_items = [str(item).ljust(col_widths[i]) for i, item in enumerate(row)]
        formatted_rows.append("  ".join(padded_items))

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
    STATISTICS = auto(), "Receive network statistics"
    VERIFY_RES = auto(), "Private command to verify a resource is a directory/file and exists"
    VERIFY_PAS = auto(), "Private command to verify a user/pass is correct"


    def __new__(cls, num: int, desc: str):
        obj = object.__new__(cls)
        obj._value_ = num
        obj.desc = desc
        return obj

    @staticmethod
    def cmd_str() -> str:
        header = "Available Commands:\n"

        # Convert Enum members to a list of lists, excluding the last one
        table_data = []
        for command in list(Command)[:-2]:  # Excludes VERIFY_RES, VERIFY_PAS
            table_data.append([command.name, command.desc])

        return format_table(table_data, ["Commands", "Description"])

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
    USER_NAME = auto()
    PASSWORD = auto()

    EXISTS = auto()
    IS_DIR = auto()

    def __int__(self):
        return self.value


def format_bytes(num_bytes: int) -> str:
    """
    Convert bytes into a formatted string with appropriate unit (B, KB, MB, GB, TB).

    Args:
        num_bytes: The number of bytes to format

    Returns:
        A formatted string with the value and unit (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def format_time(seconds: float) -> str:
    """
    Convert seconds into a formatted time string (HH:MM:SS or MM:SS).

    Args:
        seconds: The number of seconds to format

    Returns:
        A formatted time string
    """
    if seconds < 0:
        return "∞"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"



if __name__ == "__main__":
    print(Command.cmd_str())
    print(KeyData.MSG)
    print(ResCode.INVALID_CMD)

