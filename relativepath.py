from pathlib import Path
from typing import Union


class RelativePath:
    """
    Stores a relative start_path with metadata about whether it's a directory and its size in bytes.
    This class preserves file metadata that would be lost when converting absolute paths to relative paths.
    """

    def __init__(self, location: str, name: str = "", bytes_size: int = 0) -> None:
        self.location = location
        self.name = name
        self.bytes = bytes_size

    @classmethod
    def from_base(cls, folder: str = "", start_path: Path | None = None):
        if start_path is None:
            start_path = Path(__file__).parent.resolve()

        return cls.from_path(start_path, start_path, folder)

    @classmethod
    def from_path(cls, start_path: Path, base_path: Path | None = None, folder: str = "") -> 'RelativePath':
        """
        Create a RelativePath from a Path object.

        Args:
            base_path: The starting server location
            start_path: The Path object to convert
            folder: Optional subfolder to append
        """
        if base_path is None:
            base_path = Path(__file__).parent.resolve()

        # Determine if it's a file or directory and get size
        if start_path.is_file():
            name = start_path.name
            bytes_size = start_path.stat().st_size
        else:
            name = ""
            bytes_size = 0

        if start_path.is_relative_to(base_path):
            rel_path = start_path.relative_to(base_path)
        else:
            rel_path = Path(__file__).parent.resolve()


        if folder:
            rel_path = rel_path / folder

        return cls(str(rel_path), name, bytes_size)

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
        if isinstance(other, (str, Path)):
            base = Path(self.location) / self.name if self.name else Path(self.location)
            new_location = str(base / other)
            return RelativePath(new_location, "", 0)
        elif isinstance(other, RelativePath):
            base = Path(self.location) / self.name if self.name else Path(self.location)
            new_location = str(base / other.location)
            return RelativePath(new_location, other.name, other.bytes)
        else:
            return NotImplemented

    def path(self) -> Path:
        """Returns a pathlib Path object representing the full start_path."""
        if self.name:
            return Path(self.location) / self.name
        else:
            return Path(self.location)

    def __repr__(self) -> str:
        return f"RelativePath(location='{self.location}', name='{self.name}', bytes={self.bytes})"

    def __str__(self) -> str:
        """Returns a string representation of the start_path."""
        return self.str_dir if self.isdir else self.str_file

    def __eq__(self, other) -> bool:
        if not isinstance(other, RelativePath):
            return False
        return (self.location == other.location and
                self.name == other.name and
                self.bytes == other.bytes)

    def __hash__(self) -> int:
        return hash((self.location, self.name, self.bytes))