import os
from pathlib import Path

import sys
import getpass

from client_interface import ClientInterface
from relativepath import RelativePath
from type import Command, ResCode


class ClientCli(ClientInterface):

    def start_program(self) -> None:
        """
        Runs once when the program is started.
        """
        print("Insert cool banner here")

    def app_exit(self) -> None:
        """
        Runs once when the program is closed.
        """
        print("APP exit successfully")
        sys.exit(os.EX_OK)

    def app_error(self, status: ResCode) -> None:
        """
        Prints error message and exits.
        # ANSI escape codes for red text and resetting the color
        """
        RED = '\033[31m'
        RESET = '\033[0m'
        print(RED + status.desc + RESET)

    def app_print(self, msg: str) -> None:
        """
        prints the basic message
        """
        print(msg)

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
            in_data = input("> ").strip().upper()
            cmd: Command|None = Command.from_str(in_data)

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

    def receive_user_pass(self) -> tuple[str, str]:
        """
        Prompts for a username and a password.
        """
        username = "test"
        password = "test"
        # use getpass module
        return username, password

    def select_server_files(self) -> list[RelativePath]:
        """
        Takes input as a string converts it to RelativePath
        returns when input is empty/None
        """
        paths: list[RelativePath] = []
        while(True):
            input = "test"
            paths.append(self.current_dir / input)
            # return paths when done

    def select_client_files(self) -> list[Path]:
        """
        Takes string input from user in a while loop casts it to Path object and checks if it exists
        returns when input is empty/None
        """

        # use Path(input)
        # use if path_to_check.exists():
        pass

    def select_client_dir(self) -> Path|None:
        """
        Takes string input from user casts it to Path object and checks if it exists
        returns if not a directory return None
        """

        # use Path(input).is_dir() to check if it is a directory
        # use if path_to_check.exists():
        pass

    def progress_bar(self, progress: int, msg: str) -> None:
        """
        Displays a progress bar, from 0-99, when greater than 99 kill progress bar
        """
        pass

if __name__ == "__main__":
    client_cli = ClientCli()
    client_cli.run()