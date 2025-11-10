import time
from pathlib import Path
import shutil
from typing import Callable


from type import SIZE


class Transfer:
    @staticmethod
    def send_file(conn, file_path: Path, num_bytes: int, progress_func: Callable[[int, int, int], None] = lambda num, num2, num3: None) -> bool:
        """
        Upload a file by reading from file_path and sending num_bytes

        Args:
            conn: Socket connection
            file_path: Path to the file to send
            num_bytes: Number of bytes to send
            progress_func: callable function to display the progress of the transfer it is an int from 0 to 100

        Returns:
            bool: True if successful, False otherwise
        """
        assert file_path.is_file(), f"Invalid input: '{file_path}' is not a file."
        assert file_path.exists(), f"Invalid input: '{file_path}' does not exist."

        progress_func(0, 0, num_bytes)
        start_time: float = time.perf_counter()
        elapsed_bytes: int = 0

        try:
            bytes_sent = 0
            with open(file_path, "rb") as fileToSend:
                while bytes_sent < num_bytes:

                    elapsed_time = time.perf_counter() - start_time
                    if elapsed_time >= 0.2:
                        progress_func(bytes_sent * 100 // num_bytes, int(elapsed_bytes/elapsed_time), num_bytes)
                        start_time = time.perf_counter()
                        elapsed_bytes = 0



                    # Calculate how much to read in this iteration
                    chunk_size = min(SIZE, num_bytes - bytes_sent)
                    elapsed_bytes += chunk_size
                    filedata = fileToSend.read(chunk_size)

                    if not filedata:
                        # File ended before expected bytes
                        return False

                    conn.sendall(filedata)
                    bytes_sent += len(filedata)

            return bytes_sent == num_bytes

        except Exception as e:
            print(f"Error sending file: {e}")
            return False
        finally:
            progress_func(100, 0, num_bytes)

    @staticmethod
    def recv_file(conn, directory_path: Path, file_name: str, num_bytes: int, progress_func: Callable[[int, int, int], None] = lambda num, num2, num3: None) -> bool:
        """
        Downloads a file by receiving num_bytes and writing to directory_path/file_name

        Args:
            conn: Socket connection
            directory_path: Directory where file should be saved
            file_name: Name of the file to create
            num_bytes: Number of bytes to receive
            progress_func: callable function to display the progress of the transfer it is an int from 0 to 100

        Returns:
            bool: True if successful, False otherwise
        """
        assert directory_path.is_dir(), f"Invalid input: '{directory_path}' is not a directory."
        assert directory_path.exists(), f"Invalid input: '{directory_path}' does not exist."

        try:
            bytes_received = 0
            file_path = directory_path / file_name

            progress_func(0, 0, num_bytes)
            start_time: float = time.perf_counter()
            elapsed_bytes: int = 0

            with open(file_path, "wb") as fileToWrite:
                while bytes_received < num_bytes:

                    elapsed_time = time.perf_counter() - start_time
                    if elapsed_time >= 0.2:
                        progress_func(bytes_received * 100 // num_bytes, int(elapsed_bytes / elapsed_time), num_bytes)
                        start_time = time.perf_counter()
                        elapsed_bytes = 0

                    # Calculate how much to receive in this iteration
                    chunk_size = min(SIZE, num_bytes - bytes_received)
                    elapsed_bytes += chunk_size
                    filedata = conn.recv(chunk_size)

                    if not filedata:
                        # Connection closed before expected bytes
                        return False

                    fileToWrite.write(filedata)
                    bytes_received += len(filedata)

            return bytes_received == num_bytes

        except Exception as e:
            print(f"Error receiving file: {e}")
            return False
        finally:
            progress_func(100, 0, num_bytes)

    @staticmethod
    def file_traversal(base_path: Path, start_path: Path) -> Path:
        """Fixes directory traversal vulnerability"""
        try:
            main_path: Path = (base_path / start_path).resolve()
            base_resolved = base_path.resolve()

            # Check if main_path is relative to base_path
            if main_path.is_relative_to(base_resolved):
                return main_path
            else:
                return base_resolved
        except Exception:
            return base_path

    @staticmethod
    def recursively_remove_dir(base_path: Path, server_dir: Path) -> bool:

        base_path: Path = Transfer.file_traversal(base_path, server_dir)

        try:
            shutil.rmtree(base_path)
            print(f"Directory '{base_path}' and its contents deleted successfully.")
            return True
        except Exception as e:
            print(f"Error: {base_path} : {e.strerror}")
            return False


    @staticmethod
    def create_directory(base_path: Path, server_dir: Path) -> bool:
        try:
            base_path: Path = Transfer.file_traversal(base_path, server_dir)
            base_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            return False

    @staticmethod
    def delete_file(base_path: Path, server_dir: Path) -> bool:
        try:
            base_path: Path = Transfer.file_traversal(base_path, server_dir)
            if base_path.exists() and base_path.is_file():
                base_path.unlink()
                return True
            else:
                return False
        except Exception as e:
            return False



