from enum import Enum, auto, IntEnum


#upload test.txt

class commands(Enum):
    LOGOUT = auto()
    TASK = auto()
    DOWNLOAD = auto()
    DELETE = auto()
    UPLOAD = auto()
    DIR = auto()
    HELP = auto()