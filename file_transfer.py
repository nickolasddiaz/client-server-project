from pathlib import Path

from relativepath import RelativePath
from type import SIZE

class Transfer:
    @staticmethod
    def send_file(conn, file_path: Path) -> bool:
        """
        Upload a file, by reading a file from a base_path
        """
        assert file_path.is_file(), f"Invalid input: '{file_path}' is a file, not a directory."
        assert file_path.exists(), f"Invalid input: '{file_path}' does not exist."

        with open(file_path, "rb") as fileToSend:
            while True:
                filedata = fileToSend.read(SIZE)
                if not filedata:
                    break
                conn.send(filedata)

            conn.send(b'EOF')

        return True

    @staticmethod
    def recv_file(conn, server_path: RelativePath ,rel_path: RelativePath, file_name: str) -> bool:
        """
        Downloads a file, by reading a file from a base_path
        """

        assert rel_path.isdir, f"Invalid input: '{rel_path}' is a file, not a directory."

        base_path: Path = server_path.path() / rel_path.path()

        # Fixes directory traversal vulnerability
        if not base_path.is_relative_to(server_path.path()):
            base_path = server_path.path()

        with open(base_path / file_name, "wb") as fileToWrite:
            while True:
                filedata = conn.recv(SIZE)
                if not filedata:
                    break
                # Check if EOF marker is in the received data
                if b'EOF' in filedata:
                    # Write everything before the EOF marker
                    fileToWrite.write(filedata.replace(b'EOF', b''))
                    break
                fileToWrite.write(filedata)

        return True