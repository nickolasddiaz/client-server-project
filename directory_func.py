# this file holds the directory functions (helper functions to be used
# ...in client.py and server.py)

from pathlib import Path
from tkinter import filedialog as fd
import tkinter as tk

from encoder import Encoder
from relativepath import RelativePath
from type import KeyData, Command, SIZE


class DirHelp:
    @staticmethod
    def list_directory(server_dir: RelativePath, base_dir: RelativePath, recursive: bool)-> list[RelativePath]:
        """
        Private function to take in a Path/directory and return the list of starting_path
        Why list[tuple[Path, bool, int] because relative starting_path do not have a way to determine a directory
        """
        assert base_dir.str_dir, f"Input needs to be a directory not a file: {base_dir}"

        file_list = []
        base_path: Path = server_dir.path() / base_dir.path()

        # rglob represents all files recursively while glob is not recursive
        iterator = base_path.rglob('*') if recursive else base_path.glob('*')

        # potential features show files size and modification date
        # doesn't show any directory info
        for file_path_obj in iterator:
            file_list.append(RelativePath.from_path(file_path_obj, server_dir.path()))

        return file_list

    @staticmethod
    def str_paths(path_list: list[RelativePath]) -> str:
        """
        Takes in a list of starting_path and pretty prints out
        """
        pretty_path = ""
        for path in path_list:
            pretty_path += str(path) + '\n'

        return pretty_path

    @staticmethod
    def select_file_client() -> Path | None:
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

    @staticmethod
    def get_dir(conn, starting_path: RelativePath) -> list[RelativePath]|None:
        out_data: bytes = Encoder.encode({KeyData.REL_PATH: starting_path}, Command.DIR)
        conn.send(out_data)

        encoded_data: bytes = conn.recv(SIZE)
        response: dict = Encoder.decode(encoded_data)

        return response.get(KeyData.REL_PATHS)

    @staticmethod
    def select_file_server(conn, starting_path: RelativePath, select_dir: bool,
                           select_file: bool) -> RelativePath | None:
        """
        Displays a list of file starting_path from the server and lets the user select one.
        Returns the selected Path object, or None if cancelled/something went wrong.
        """

        if not starting_path or starting_path.isfile:
            return None

        selected_path = None

        def refresh_listbox():
            nonlocal paths
            listbox.delete(0, tk.END)

            paths = DirHelp.get_dir(conn, starting_path)
            DirHelp.str_paths(paths)

            # Add parent directory option if not at root
            if starting_path.path() != Path('.'):
                parent_item = starting_path.go_up()
                listbox.insert(tk.END, f"📁 .. (Parent Directory)")
                paths.insert(0, parent_item)

            # Insert the file/directory names into the listbox
            for p in paths[1:] if starting_path.path() != Path('.') else paths:
                prefix = "📁" if p.isdir else "📄"
                listbox.insert(tk.END, f"{prefix} {str(p)}")

            path_label.config(text=f"Current: {starting_path.location}")

        def on_double_click(event):
            nonlocal starting_path, selected_path
            selection = listbox.curselection()
            if selection:
                selected_item = paths[selection[0]]

                if selected_item.isdir:
                    # Navigate into the directory
                    if selection[0] == 0 and starting_path.path() != Path('.'):
                        starting_path = starting_path.go_up()
                    else:
                        # Go into subdirectory
                        starting_path = selected_item
                    refresh_listbox()
                elif select_file:
                    selected_path = selected_item
                    root.destroy()

        def on_select():
            nonlocal selected_path
            selection = listbox.curselection()
            if selection:
                selected_item = paths[selection[0]]

                # Check if selection is valid based on select_dir and select_file
                if (selected_item.isdir and select_dir) or (not selected_item.isdir and select_file):
                    selected_path = selected_item
                    root.destroy()

        def on_cancel():
            root.destroy()

        root = tk.Tk()
        root.title("Select file/s")

        # Label showing current start_path
        path_label = tk.Label(root, text=f"Current Directory: {starting_path.location}", font=("Arial", 10, "bold"))
        path_label.pack(pady=5)

        tk.Label(root, text="Available files on server:").pack(pady=5)

        listbox = tk.Listbox(root, width=80, height=15)
        listbox.pack(padx=10, pady=5)

        # Bind double-click event
        listbox.bind('<Double-Button-1>', on_double_click)

        paths = []
        refresh_listbox()

        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Select", command=on_select).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=10)

        root.mainloop()
        return selected_path


