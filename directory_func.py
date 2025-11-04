# this file holds the directory functions (helper functions to be used
# ...in client.py and server.py)

import os
from pathlib import Path
from tkinter import filedialog as fd
import tkinter as tk

from encoder import Encoder
from type import SIZE, Command


class RelativePath:
    """
    Basic tuple for that stores the relative path
    is it a directory and how many bytes it is
    Absolute path has these variables but when it becomes a relative path it looses them
    """
    def __init__(self,relative_path : Path, is_dir : bool, file_bytes : int) -> None:
        self.relative_path = relative_path
        self.is_dir = is_dir
        self.file_bytes = file_bytes

    def __str__(self):
        if self.is_dir:
            return f"{str(self.relative_path.name)}\t <DIR>\n"
        else:
            if self.file_bytes > 1000:
                file_stat: str = f"{self.file_bytes / 1000} KB"
            else:
                file_stat: str = f"{self.file_bytes} B"
            return f"{str(self.relative_path.name)}\t {file_stat}\n"



class DirectoryHelper:
    def __init__(self):
        """
        Runs only once defines the default_location location for the file server
        """
        script_dir = Path(__file__).resolve().parent / 'server_location'
        if not script_dir.is_dir():
            os.makedirs(script_dir, exist_ok=True) # Creates the directory if it doesn't exist

        self.default_location = script_dir


    def list_directory(self, base_directory: Path, recursive: bool)-> list[RelativePath]:
        """
        Private function to take in a Path/directory and return the list of relative_path
        Why list[tuple[Path, bool, int] because relative relative_path do not have a way to determine a directory
        """
        base_path = Path(base_directory)

        file_list = []

        # rglob represents all files recursively while glob is not recursive
        iterator = base_path.rglob('*') if recursive else base_path.glob('*')

        # potential features show files size and modification date
        # doesn't show any directory info
        for file_path_obj in iterator:
            is_dir = False
            file_bytes = 0
            if file_path_obj.is_dir():
                is_dir = True
            else:
                file_bytes = (self.default_location / file_path_obj).stat().st_size

            relative_path = file_path_obj.relative_to(base_path)
            file_list.append(RelativePath(relative_path, is_dir, file_bytes))

        return file_list

    def Tree_str(self, base_directory: Path) -> str:
        """
        Helper function recursively returns a string from a directory
        """
        return self.str_paths(self.list_directory(base_directory, True))

    def Dir_str(self, base_directory: Path) -> str:
        """
        Helper function returns a string from a directory
        """
        return self.str_paths(self.list_directory(base_directory, False))

    def str_paths(self, path_list: list[RelativePath]) -> str:
        """
        Takes in a list of relative_path and pretty prints out
        """
        pretty_path = ""
        for relative_path in path_list:
            pretty_path += str(relative_path)

        return pretty_path


    def open_path_client(self) -> Path | None:
        """
        opens file dialog box, user selects 1 file from their device
        :return a Path or None if something went wrong
        """
        root = tk.Tk()
        root.attributes('-topmost', True)  # Bring dialog to front
        root.focus_force()  # Force focus

        file_path_str = None
        try:
            file_path = fd.askopenfilename(title="Select a File", filetypes=[("All files", "*.*")]) # Added title and filetypes for better UX
            if file_path:
                file_path_str = file_path
        except Exception as e:
            return None
        finally:
            root.destroy()

        if file_path_str:
            path_variable = Path(file_path_str)
            return path_variable
        else:
            return None

    def open_path_server(self, relative_path: list[RelativePath]) -> RelativePath | None:
        """
        Displays a list of file relative_path from the server and lets the user select one.
        Returns the selected Path object, or None if cancelled/something went wrong.
        """

        if not relative_path:
            return None

        selected_path = None

        def on_select():
            nonlocal selected_path
            selection = listbox.curselection()
            if selection:
                selected_path = relative_path[selection[0]]
            root.destroy()

        def on_cancel():
            root.destroy()

        root = tk.Tk()
        root.title("Select a file to download")

        tk.Label(root, text="Available files on server:").pack(pady=5)

        listbox = tk.Listbox(root, width=80, height=15)
        listbox.pack(padx=10, pady=5)

        # Insert the file names into the listbox
        for p in relative_path:
            listbox.insert(tk.END, str(p))

        tk.Button(root, text="Select", command=on_select).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(root, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=10, pady=10)

        root.mainloop()
        return selected_path
    

    def send_file(self, conn, file_path: Path) -> bool:
        """
        Upload a file, by reading a file from a path
        """
        if file_path.is_dir():
            raise ValueError(f"Invalid input: '{file_path}' is a directory, not a file.")
        elif not file_path.exists():
            raise ValueError(f"Invalid input: '{file_path}' does not exist.")

        with open(file_path, "rb") as fileToSend:
            while True:
                filedata = fileToSend.read(SIZE)
                if not filedata:
                    break
                conn.send(filedata)

            conn.send(b'EOF')

        return True

    def recv_file(self, conn, dir_path: Path, file_name: str) -> bool:
        """
        Downloads a file, by reading a file from a path
        """

        if dir_path.is_file():
            raise ValueError(f"Invalid input: '{dir_path}' is a file, not a directory.")
        elif not dir_path.exists():
            raise ValueError(f"Invalid input: '{dir_path}' does not exist.")

        with open(dir_path / file_name, "wb") as fileToWrite:
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

    
if __name__ == "__main__":
    """
    Live demonstration of seeing and selecting files on a server 
    """

    Dir_Help = DirectoryHelper()

    print(Dir_Help.Dir_str(Dir_Help.default_location))

    # Gets all the list of file relative_path
    files_on_server : list[RelativePath] = Dir_Help.list_directory(Dir_Help.default_location, False)

    # opens the custom GUI file opener
    chosen = Dir_Help.open_path_server(files_on_server)
    if chosen:
        print(f"User selected: {chosen}")
    else:
        print("No file selected.")
