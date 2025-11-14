import io
import os
import time
import zipfile
from pathlib import Path
import shutil
from typing import Callable

from zipstream import ZipStream

from type import SIZE


class Transfer:
    @staticmethod
    def send_file(conn, zip_file: ZipStream, num_bytes: int, progress_func: Callable[[int, int, int], None] = lambda num, num2, num3: None) -> bool:
        """
        Upload a file by reading from file_path and sending num_bytes

        Args:
            conn: Socket connection
            zip_file: Path to the file to send
            num_bytes: Number of bytes to receive, This is NOT accurate, it is only used for the progress bar
            progress_func: callable function to display the progress of the transfer it is an int from 0 to 100

        Returns:
            bool: True if successful, False otherwise
        """

        progress_func(0, 0, num_bytes)
        start_time: float = time.perf_counter()
        elapsed_bytes: int = 0

        try:
            bytes_sent = 0
            for chunk in zip_file:
                elapsed_time = time.perf_counter() - start_time

                # Update progress every 0.2 seconds
                if elapsed_time >= 0.2:
                    progress_func(bytes_sent * 100 // num_bytes, int(elapsed_bytes / elapsed_time), num_bytes)
                    start_time = time.perf_counter()
                    elapsed_bytes = 0

                conn.sendall(chunk)
                bytes_sent += len(chunk)
                elapsed_bytes += len(chunk)

            # Final progress update
            conn.sendall(b'EOF')
            return True

        except Exception as e:
            print(f"Error sending file: {e}")
            return False
        finally:
            progress_func(99, 0, num_bytes)

    @staticmethod
    def recv_file(conn, directory_path: Path, num_bytes: int,
                  progress_func: Callable[[int, int, int], None] = lambda num, num2, num3: None) -> bool:
        """
        Downloads a file by receiving num_bytes into an in-memory buffer and extracting it.

        Args:
            conn: Socket connection
            directory_path: Directory where file contents should be extracted
            num_bytes: Number of bytes to receive, used for the progress bar
            progress_func: Callable to display transfer progress: progress_func(percentage, speed, total_size)

        Returns:
            bool: True if successful, False otherwise
        """
        assert directory_path.is_dir(), f"Invalid input: '{directory_path}' is not a directory."
        assert directory_path.exists(), f"Invalid input: '{directory_path}' does not exist."

        # create an in-memory bytes buffer instead of a file on disk.
        in_memory_zip = io.BytesIO()

        try:
            bytes_received = 0
            progress_func(0, 0, num_bytes)
            start_time: float = time.perf_counter()
            elapsed_bytes: int = 0

            # Loop to receive data from the socket
            while True:
                elapsed_time = time.perf_counter() - start_time

                # Update progress every 0.2 seconds
                if elapsed_time >= 0.2:
                    speed = int(elapsed_bytes / elapsed_time) if elapsed_time > 0 else 0
                    progress_func(bytes_received * 100 // num_bytes, speed, num_bytes)
                    start_time = time.perf_counter()
                    elapsed_bytes = 0

                # Receive data
                filedata = conn.recv(SIZE)

                if filedata == b'EOF':
                    # Connection closed - transfer complete
                    break

                # write the received data directly into the memory buffer
                in_memory_zip.write(filedata)
                bytes_received += len(filedata)
                elapsed_bytes += len(filedata)

            # Final progress update
            progress_func(99, 0, num_bytes)

            # Rewind the buffer to the beginning
            in_memory_zip.seek(0)

            with zipfile.ZipFile(in_memory_zip, 'r') as zip_ref:
                zip_ref.extractall(directory_path)


            return True

        except Exception as e:
            print(f"Error receiving file: {e}")
            return False
        finally:
            #  close the buffer to release memory immediately
            progress_func(100, 0, num_bytes)
            in_memory_zip.close()

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

        del_path: Path = Transfer.file_traversal(base_path, server_dir)

        if base_path.resolve() == del_path:
            return False

        try:
            if del_path.is_dir():
                shutil.rmtree(del_path)
                print(f"Directory '{del_path}' and its contents deleted successfully.")
            elif del_path.exists():
                del_path.unlink()
            return True
        except Exception as e:
            print(f"Error: {del_path} : {e}")
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