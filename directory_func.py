# this file holds the directory functions (helper functions to be used
# ...in client.py and server.py)

from pathlib import Path
from tkinter import filedialog as fd
import tkinter as tk
import tkinter.ttk as ttk

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
        assert base_dir.isdir, f"Input needs to be a directory not a file: {base_dir}"

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
    def get_dir(conn, starting_path: RelativePath, rtn_files:bool) -> list[RelativePath]:
        out_data: bytes = Encoder.encode({KeyData.REL_PATH: starting_path}, Command.DIR)
        conn.send(out_data)

        encoded_data: bytes = conn.recv(SIZE)
        response: dict = Encoder.decode(encoded_data)

        rel_paths: list[RelativePath] = response.get(KeyData.REL_PATHS)

        if not rtn_files:
            rel_paths = list(filter(lambda item: item.isdir, rel_paths))

        return rel_paths

    @staticmethod
    def select_file_server(conn, starting_path: RelativePath, show_file: bool) -> list[RelativePath] | None:
        """
        Displays a list of file starting_path from the server and lets the user select one.
        Returns the selected Path object, or None if cancelled/something went wrong.
        """

        if not starting_path or starting_path.isfile:
            return None

        selected_path = None
        select_paths: list[RelativePath] = []

        def refresh_treeview():
            nonlocal paths
            for item in treeview.get_children():
                treeview.delete(item)

            paths = DirHelp.get_dir(conn, starting_path, show_file)
            DirHelp.str_paths(paths)

            # Add parent directory option
            if starting_path.path() != Path('.'):
                parent_item = starting_path.go_up()
                paths.insert(0, parent_item)
                treeview.insert(
                    "", "end", iid="parent", text="📁 .. (Parent Directory)",
                    values=("", "", "Directory", "")
                )

            # Insert current directory content
            for i, p in enumerate(paths[1:] if starting_path.path() != Path('.') else paths):
                prefix = "📁" if p.isdir else "📄"
                treeview.insert(
                    "",
                    "end",
                    iid=str(i),
                    text=f"{prefix} {p.true_name}",
                    values=(f"{p.bytes} bytes", "Directory" if p.isdir else "File", p.time_str if p.isfile else "")
                )

            path_label.config(text=f"Current Directory: {starting_path.location}\\")

        def on_double_click(event):
            nonlocal starting_path, selected_path
            item_id = treeview.focus()
            if not item_id:
                return

            if item_id == "parent":
                starting_path = starting_path.go_up()
                refresh_treeview()
                return

            index = int(item_id)
            selected_item = paths[index + (1 if starting_path.path() != Path('.') else 0)]

            if selected_item.isdir:
                starting_path = selected_item
                refresh_treeview()


        def on_select():
            selected_iids = treeview.selection()
            for iid in selected_iids:
                index = int(iid)
                selected_item = paths[index + (1 if starting_path.path() != Path('.') else 0)]
                select_paths.append(selected_item)

            root.destroy()


        def on_cancel():
            root.destroy()

        root = tk.Tk()
        root.title("Select file/s")
        root.geometry("700x400")

        main_frame = ttk.Labelframe(root, padding=10, text="Available files on server:")
        main_frame.pack(fill="both", expand=True)

        path_label = ttk.Label(main_frame, text="")
        path_label.pack(anchor="w", pady=5)

        # Treeview setup
        columns = ("Size", "Type", "Modified")
        treeview = ttk.Treeview(main_frame, columns=columns, show="tree headings", selectmode="extended")
        treeview.heading("#0", text="Name")
        treeview.heading("Size", text="Size")
        treeview.heading("Type", text="Type")
        treeview.heading("Modified", text="Modified")

        treeview.column("#0", width=250, anchor="w")
        treeview.column("Size", width=100, anchor="e")
        treeview.column("Type", width=100, anchor="center")
        treeview.column("Modified", width=100, anchor="center")

        treeview.pack(fill="both", expand=True, pady=5)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=5)

        select_btn = ttk.Button(btn_frame, text="Select", command=on_select)
        select_btn.grid(row=0, column=0, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.grid(row=0, column=1, padx=5)

        treeview.bind("<Double-1>", on_double_click)

        # Initial population
        paths = []
        refresh_treeview()

        root.mainloop()
        return select_paths


