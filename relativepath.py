import time
from pathlib import Path
from typing import Union



class RelativePath:
    """
    Stores a relative base_path with metadata about whether it's a directory,
    byte size, modification date and name.
    This class preserves file metadata that would be lost when converting 
    absolute paths to relative paths in the Pathlib library.
    Attributes:
        location (str): The relative location of the base_path.
        name (str): The name of the file or directory.
        bytes_size (int): The size of the file in bytes.
        mtime (float): The modification time of the file or directory.
        isdir (bool): True if this represents a directory.
        isfile (bool): True if this represents a file.

        Create this class using from_path or from_base class methods.
        from_path: Creates a RelativePath from a Path object.
        from_base: Creates a RelativePath from a base folder and optional subfolder.


    """

    def __init__(self, location: str, name: str = "", bytes_size: int = 0, mtime: float = 0.0) -> None:
        self.location = location
        self.name = name
        self.bytes = bytes_size
        self.time = mtime

    @classmethod
    def from_base(cls, folder: str = "", base_path: Path | None = None):
        """
        Create a RelativePath from a base folder and optional subfolder.
        
        Args:
            folder: subfolder to append (optional)
            base_path: The Path object
        """

        return cls.from_path(base_path, base_path, folder)

    @classmethod
    def from_path(cls, start_path: Path | None, base_path: Path | None = None, folder: str = "") -> 'RelativePath':
        """
        Create a RelativePath from a Path object.

        Args:
            start_path: The Path object to convert
            base_path: The starting server location (optional)
            folder: Subfolder to append (Optional)
        """
        if base_path is None:
            base_path = Path.cwd()

        if start_path is None:
            start_path = Path.cwd()

        temp_time = 0
        # Determine if it's a file or directory and get size
        if start_path.is_file():
            name = start_path.name
            bytes_size = start_path.stat().st_size
            temp_time = start_path.stat().st_mtime
        else:
            name = ""
            bytes_size = 0

        if start_path.is_relative_to(base_path):
            rel_path = start_path.relative_to(base_path)
        else:
            rel_path = Path.cwd()

        if folder:
            rel_path = rel_path / folder

        return cls(str(rel_path.as_posix()), name, bytes_size, temp_time)

    @property
    def true_name(self):
        """Returns the true name of the file or directory."""
        if self.isdir:
            p = Path(self.location).parts
            if len(p) >= 1:
                return p[0]
            else:
                return ""

        else:
            return self.name

    @property
    def time_str(self) -> str:
        """Returns a human-readable string of the modification time."""
        return time.ctime(self.time)

    @property
    def isdir(self) -> bool:
        """Returns True if this represents a directory."""
        return not self.name

    @property
    def isfile(self) -> bool:
        """Returns True if this represents a file."""
        return bool(self.name)

    @property
    def str_bytes(self) -> str:
        """Returns a human-readable string of the file size with appropriate unit."""
        if self.bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = self.bytes
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        # Format with appropriate decimal places
        if unit_index == 0:  # Bytes
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"

    @property
    def str_dir(self) -> str:
        """Returns a formatted string for directory display."""
        full_path = str(Path(self.location) / self.name) if self.name else self.location
        return f"{full_path}\t<DIR>"

    @property
    def str_file(self) -> str:
        """Returns a formatted string for file display."""
        return f"{self.name}\t{self.str_bytes}"

    def go_up(self) -> 'RelativePath':
        """Navigate to the parent directory."""
        path = Path(self.location)
        if path == Path('.'):
            return RelativePath('.', '', 0)
        else:
            parent = path.parent
            return RelativePath(str(parent), '', 0)

    def __truediv__(self, other: Union[str, 'RelativePath', Path]) -> 'RelativePath':
        """Enables the use of the / operator to join paths."""
        if isinstance(other, (str, Path)):
            new_location = str(self.path() / other)
            return RelativePath(new_location, "", 0)
        elif isinstance(other, RelativePath):
            new_location = str(self.path() / other.location)
            return RelativePath(new_location, other.name, other.bytes)
        else:
            return NotImplemented

    def path(self) -> Path:
        """Returns a pathlib Path object representing the full base_path."""
        if self.name:
            return Path(Path(self.location).as_posix()) / self.name
        else:
            return Path(Path(self.location).as_posix())

    def __repr__(self) -> str:
        """Returns a detailed string representation of the RelativePath."""
        return f"RelativePath(location='{self.location}', name='{self.true_name}', bytes={self.bytes}, time={self.time_str})"

    def __str__(self) -> str:
        """Returns a string representation of the base_path."""
        return f"{(self.str_dir if self.isdir else self.str_file)}: \t{self.time_str}"

    def __eq__(self, other) -> bool:
        """Checks equality based on location, name, and bytes size."""
        if not isinstance(other, RelativePath):
            return False
        return (self.location == other.location and
                self.name == other.name and
                self.bytes == other.bytes)

    def __hash__(self) -> int:
        """Allows RelativePath to be used in sets and as dictionary keys."""
        return hash((self.location, self.name, self.bytes))