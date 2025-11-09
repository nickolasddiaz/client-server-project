import os
from pathlib import Path

import sys
import getpass

from client_interface import ClientInterface
from relativepath import RelativePath
from type import Command, ResCode


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
            in_data = input(f"{self.current_dir.location}\\> ")
            cmd: Command | None = Command.from_str(in_data)

            if cmd is None:
                self.app_error(ResCode.INVALID_CMD)
            else:
                return cmd

    def show_dir(self, rel_paths: list[RelativePath]) -> None:
        """
        Prints the directory when received, executed when DIR/TREE command is executed
        """
        for path in rel_paths:
            print(path)

    def receive_user_pass(self) -> None:
        """
        Prompts for a username and a password.
        """
        self.local_user = input("Enter username: ")
        self.local_pass = getpass.getpass("Enter password: ")

    def select_server_dir(self) -> RelativePath|None:
        """
        Takes string input from user casts it to RelativePath object and checks if it exists
        returns if not a directory return None
        """
        print("Select a directory of the server")
        while True:
            in_files = in_files = input(f"\t{self.current_dir.location}\\ <-|").strip('"')
            if in_files == '':
                return None

            path_file = RelativePath(str(self.current_dir.location), "", 0, 0) / in_files
            return path_file

    def select_server_files(self) -> list[RelativePath]:
        """
        Takes input as a string converts it to RelativePath
        returns when input is empty
        """
        print("Select multiple files on the server: Return nothing to exit")
        paths: list[RelativePath] = []
        while True:
            in_files = input(f"\t{self.current_dir.location}\\ <-|").strip('"')
            if in_files == '':
                return paths
            paths.append(self.current_dir / in_files)

    def select_client_files(self) -> list[Path]:
        """
        Takes string input from user in a while loop casts it to Path object and checks if it exists
        program returns to list when input is empty
        """
        print("Select multiple files on your machine (relative or absolute paths): Return nothing to exit")
        current_directory: str = os.getcwd()
        paths: list[Path] = []
        while True:
            in_files = input(f"\t{current_directory} <-| ").strip('"')
            if in_files == '':
                return paths

            path_file = Path(in_files)
            if path_file.exists():
                paths.append(path_file)
            else:
                self.app_error(ResCode.FILE_NOT_FOUND)


    def select_client_dir(self) -> Path:
        """
        Takes string input from user casts it to Path object and checks if it exists
        returns if not a directory return None
        """
        print("Select a directory on your machine (relative or absolute path): Return nothing for current directory")
        current_directory: str = os.getcwd()
        while True:
            in_files = input(f"\t{current_directory} <-| ").strip('"')
            if in_files == '':
                return Path(current_directory)

            path_file = Path(in_files)
            if not path_file.exists():
                self.app_error(ResCode.FILE_NOT_FOUND)
            elif not path_file.is_dir():
                self.app_error(ResCode.DIRECTORY_NEEDED)
            else:
                return path_file

    # https://gist.github.com/sibosutd/c1d9ef01d38630750a1d1fe05c367eb8
    # modified script from Sibo
    def progress_bar(self, progress: int) -> None:
        """
        Displays a progress bar, from 0-99, when greater than 99 kill progress bar
        """
        if progress > 99:
            sys.stdout.write('\r')
            sys.stdout.write(' ' * 100 + '\n')
            sys.stdout.flush()
            return

        bar_length: int = 30
        bar_ratio: int = 100 // bar_length
        sys.stdout.write('\r') # \r (carriage return) returns the cursor to the start of the line
        sys.stdout.write("Finishing: {:{}} {:>3}%"
                         .format(progress // bar_ratio * '🏁', bar_length, progress))



if __name__ == "__main__":
    client_cli = ClientCli()
    client_cli.run()

