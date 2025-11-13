import copy
import os
import shutil
from pathlib import Path

import sys
import getpass

from client_interface import ClientInterface
from relativepath import RelativePath
from type import Command, ResCode, format_table


class ClientCli(ClientInterface):
    def __init__(self):
        super().__init__()
        print(r"""  
                        | \ | (_) ___| | _____ | | __ _ ___( )   __ _ _ __   __| |                 
                        |  \| | |/ __| |/ / _ \| |/ _` / __|/   / _` | '_ \ / _` |                 
                        | |\  | | (__|   < (_) | | (_| \__ \   | (_| | | | | (_| |                 
                        |_| \_|_|\___|_|\_\___/|_|\__,_|___/    \__,_|_| |_|\__,_|_            _   
                        |  \/  | __ _| |_| |_| |__   _____      _( )___   / ___| (_) ___ _ __ | |_ 
                        | |\/| |/ _` | __| __| '_ \ / _ \ \ /\ / /// __| | |   | | |/ _ \ '_ \| __|
                        | |  | | (_| | |_| |_| | | |  __/\ V  V /  \__ \ | |___| | |  __/ | | | |_ 
                        |_|__|_|\__,_|\__|\__|_| |_|\___| \_/\_/   |___/  \____|_|_|\___|_| |_|\__|
                        / ___|  ___ _ ____   _____ _ __  |  _ \ _ __ ___ (_) ___  ___| |_          
                        \___ \ / _ \ '__\ \ / / _ \ '__| | |_) | '__/ _ \| |/ _ \/ __| __|         
                         ___) |  __/ |   \ V /  __/ |    |  __/| | | (_) | |  __/ (__| |_          
                        |____/ \___|_|    \_/ \___|_|    |_|   |_|  \___// |\___|\___|\__|
                            """)

    def login_helper(self, response_code: ResCode) -> None:
        pass # not used in CLI

    def clear_screen(self) -> None:
        print("\033c", end="")

    def rename_file_error(self, file_name: str) -> str:
        self.app_error_print(f"{file_name} already exists: choose a new filename default override file")
        return input(f"\t{self.current_dir.location} > Type in new name:")

    def rename_file(self, file_name: str) -> str:
        self.app_print("Option to rename the file? enter nothing to skip")
        rename = input(f"\t{self.current_dir.location} > Type in new name:")
        if rename == "":
            return file_name
        else:
            return rename


    def app_exit(self) -> None:
        """
        Runs when the program is closed.
        """
        print("APP exited successfully")
        sys.exit(os.EX_OK)

    def app_error(self, status: ResCode) -> None:
        """
        Prints ResCode error.
        # ANSI escape codes for red text and resetting the color
        """

        self.app_error_print(status.desc)

        if status.is_auth_related():
            self.receive_user_pass()

    def app_print(self, msg: str) -> None:
        """
        prints the basic message
        """
        print(msg)

    def app_error_print(self, msg: str) -> None:
        """
        Prints error message.
        # ANSI escape codes for red text and resetting the color
        """
        red = '\033[31m'
        reset = '\033[0m'
        print(red + msg + reset)

    def app_print_statistics(self, msg: str) -> None:
        """
        prints the statistics about the program
        """
        print(msg)

    def command_input(self) -> Command:
        """
        Takes string input and casts it to the Command enum
        """
        while True:
            in_data = input(f"{self.current_dir.location}> ")
            cmd: Command | None = Command.from_str(in_data)

            if cmd is None:
                self.app_error(ResCode.INVALID_CMD)
            else:
                return cmd

    def show_dir(self, rel_paths: list[RelativePath]) -> None:
        """
        Prints the directory when received, executed when DIR/TREE command is executed
        """
        path_table: list[list[str]] = []
        for path in rel_paths:
            path_table.append(["📁" if path.isdir else "📄",path.true_name, path.str_bytes ,path.time_str])

        print(format_table(path_table,["📁", "Name", "Bytes", "Modified Time"]))

    def receive_user_pass(self) -> None:
        """
        Prompts for a username and a password.
        """
        while True:
            self.user_name = input("Enter username: ")
            self.password = getpass.getpass("Enter password: ")

            response_code: ResCode = self.verify_userpass()
            if response_code ==  ResCode.OK:
                return
            else:
                self.app_error(response_code)

    def select_server_files(self) -> list[RelativePath]:

        """
        Takes input as a string converts it to RelativePath
        Verifies each file exists and is a file (not directory)
        Returns when input is empty
        """
        print("Select multiple files on the server: Return nothing to exit")
        paths: list[RelativePath] = []
        while True:
            in_files = input(f"\t{self.current_dir.location} <-|").strip('"')
            if in_files == '':
                return paths

            path_file = copy.deepcopy(self.current_dir) / in_files

            # Verify file exists and is a file (not directory)
            valid_file: ResCode = self.verify_resource(False, True, path_file)
            if valid_file != ResCode.OK:
                self.app_error(valid_file)
                continue

            paths.append(path_file)

    def select_client_files(self) -> list[tuple[Path, str]]:
        """
        Takes string input from user in a while loop, casts it to Path object and checks if it exists
        Allows user to rename file if it would override an existing file on server
        Program returns list when input is empty
        """
        print("Select multiple files on your machine (relative or absolute paths): Return nothing to exit")
        current_directory: str = os.getcwd()
        paths: list[tuple[Path, str]] = []

        while True:
            in_files = input(f"\t{current_directory} <-| ").strip('"')
            if in_files == '':
                return paths

            path_file = Path(in_files)

            # Check if local file exists
            if not path_file.exists():
                self.app_error(ResCode.FILE_NOT_FOUND)
                continue

            # Check if it's a file (not directory)
            if not path_file.is_file():
                self.app_error(ResCode.FILE_NEEDED)
                continue

            # Check server-side if file would override existing file
            new_name = self.rename_file(path_file.name)
            server_path = self.current_dir / new_name

            while True:
                valid_check: ResCode = self.verify_resource(False, False, server_path)

                if valid_check == ResCode.OK:
                    # File doesn't exist on server, good to go
                    break
                elif valid_check == ResCode.EXISTS:
                    # File exists on server, ask user to rename
                    new_name = self.rename_file_error(new_name)
                    server_path = self.current_dir / new_name
                else:
                    # Some other error
                    self.app_error(valid_check)
                    break

            # Only add if verification passed
            if valid_check == ResCode.OK:
                paths.append((path_file, new_name))

    def select_client_dir(self) -> Path:
        """
        Takes string input from user, casts it to Path object and checks if it exists
        Returns directory path if valid, current directory if empty input
        """
        print("Select a directory on your machine (relative or absolute path): Return nothing for current directory")
        current_directory: str = os.getcwd()

        while True:
            in_files = input(f"\t{current_directory} <-| ").strip('"')
            if in_files == '':
                return Path(current_directory)

            path_file = Path(in_files)

            # Check if path exists
            if not path_file.exists():
                self.app_error(ResCode.FILE_NOT_FOUND)
            # Check if it's a directory
            elif not path_file.is_dir():
                self.app_error(ResCode.DIRECTORY_NEEDED)
            else:
                return path_file

    def select_server_dir(self, exists: bool, skip_verification: bool = False) -> RelativePath|None:
        """
        Takes string input from user casts it to RelativePath object and checks if it exists
        Returns directory path if valid, None if empty input
        """
        print("Select a directory of the server")

        while True:
            in_files = input(f"\t{self.current_dir.location}\\ <-|").strip('"')
            if in_files == '':
                return None

            path_file = copy.deepcopy(self.current_dir) / in_files

            # Verify directory exists and is a directory
            if not skip_verification:
                valid_dir: ResCode = self.verify_resource(True, exists, path_file)
                if valid_dir != ResCode.OK:
                    self.app_error(valid_dir)
                    continue

            return path_file

    # https://gist.github.com/sibosutd/c1d9ef01d38630750a1d1fe05c367eb8
    # modified script from Sibo
    def progress_bar(self, progress: int, byte_per_sec: int, num_bytes: int) -> None:
        """
            Displays a progress bar, from 0-99, when greater than 99 kill progress bar
            Displays bytes per second formatted in B, KB, MB, or GB
            Displays the estimated time for it to finish

            Args:
                progress: int displays the amount of progress done (0-100)
                byte_per_sec: display the amount of bytes per second
                num_bytes: display the total amount of bytes to be received
            """
        if progress > 99:
            sys.stdout.write('\n')
            sys.stdout.flush()
            return

        # dynamically get the terminal width
        bar_length: int = shutil.get_terminal_size().columns * 3 // 6
        bar_ratio: int = 100 // bar_length

        if bar_ratio == 0:
            bar_ratio = 1

        stat_str = self.progress_str(progress, byte_per_sec, num_bytes)

        sys.stdout.write('\r')  # \r (carriage return) returns the cursor to the start of the line
        sys.stdout.write("\033[32mTransferring: {:{}} {:>3} \033[0m"
                         .format(progress // bar_ratio * '0', bar_length, stat_str))
        sys.stdout.flush()



if __name__ == "__main__":
    client_cli = ClientCli()
    client_cli.run()

