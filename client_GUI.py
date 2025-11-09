import os
import sys
from pathlib import Path

from client_interface import ClientInterface
from encoder import Encoder
from relativepath import RelativePath
from type import Command, ResCode, KeyData, SIZE
import tkinter as tk
from tkinter import filedialog, ttk


class ClientGui(ClientInterface):
    def __init__(self):
        super().__init__()
        self.received_first_msg = False

    def app_exit(self) -> None:
        print("APP exit successfully")
        sys.exit(os.EX_OK)

    def app_error(self, status: ResCode) -> None:
        pass

    def app_print(self, msg: str) -> None:
        if self.received_first_msg:
            print(msg)
        else:
            self.received_first_msg = True
            self.main_gui()

    def app_error_print(self, msg: str) -> None:
        pass

    def app_print_statistics(self, msg: str) -> None:
        pass

    def command_input(self) -> Command:
        pass

    def show_dir(self, rel_paths: list[RelativePath]) -> None:
        pass

    def receive_user_pass(self) -> None:
        pass

    def select_server_dir(self) -> RelativePath:
        pass

    def select_server_files(self) -> list[RelativePath]:
        pass

    def select_client_files(self) -> list[Path]:
        root = tk.Tk()
        root.withdraw()

        # Open the file dialog, allowing multiple selections
        file_paths = filedialog.askopenfilenames(
            title="Select Multiple Files",
            filetypes=[("All files", "*.*")]  # Optional: Filter file types
        )
        paths: list[Path] = []
        if file_paths:
            for file_path in file_paths:
                paths.append(Path(file_path))

        return paths


    def select_client_dir(self) -> Path|None:
        root = tk.Tk()
        root.withdraw()

        directory_path: str = filedialog.askdirectory(
            initialdir="/",  # Optional: Set the initial directory
            title="Select a Directory"  # Optional: Set the dialog title
        )
        root.destroy()
        if directory_path:
            return Path(directory_path)
        else:
            return None

    def progress_bar(self, progress: int) -> None:
        pass

    def main_gui(self):
        select_paths: list[RelativePath] = []

        def refresh_treeview():
            nonlocal paths
            for item in treeview.get_children():
                treeview.delete(item)

            paths = self.get_dir()

            # Add parent directory option
            if self.current_dir.path() != Path('.'):
                parent_item = self.current_dir.go_up()
                paths.insert(0, parent_item)
                treeview.insert(
                    "", "end", iid="parent", text="📁 .. (Parent Directory)",
                    values=("", "", "Directory", "")
                )

            # Insert current directory content
            for i, p in enumerate(paths[1:] if self.current_dir.path() != Path('.') else paths):
                prefix = "📁" if p.isdir else "📄"
                treeview.insert(
                    "",
                    "end",
                    iid=str(i),
                    text=f"{prefix} {p.true_name}",
                    values=(f"{p.bytes} bytes", "Directory" if p.isdir else "File", p.time_str if p.isfile else "")
                )

            path_label.config(text=f"Current Directory: {self.current_dir.location}\\")

        def on_double_click(event):
            item_id = treeview.focus()
            if not item_id:
                return

            if item_id == "parent":
                self.current_dir = self.current_dir.go_up()
                refresh_treeview()
                return

            index = int(item_id)
            selected_item = paths[index + (1 if self.current_dir.path() != Path('.') else 0)]

            if selected_item.isdir:
                self.current_dir = selected_item
                refresh_treeview()

        def on_select():
            selected_iids = treeview.selection()
            for iid in selected_iids:
                index = int(iid)
                selected_item = paths[index + (1 if self.current_dir.path() != Path('.') else 0)]
                select_paths.append(selected_item)

            root.destroy()

        root = tk.Tk()
        root.title("Select file/s")
        root.geometry("700x400")

        # Bind the on_closing function to the WM_DELETE_WINDOW protocol
        root.protocol("WM_DELETE_WINDOW", self.app_exit)

        notebook = ttk.Notebook(root)
        notebook.pack(expand=True, fill="both")

        main_frame = ttk.Frame(notebook)
        stat_frame = ttk.Frame(notebook)

        message_label = ttk.Label(main_frame, text="Write Messages here")
        message_label.pack(anchor="w", pady=5)

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
        treeview.column("Size", width=50, anchor="e")
        treeview.column("Type", width=100, anchor="center")
        treeview.column("Modified", width=150, anchor="center")

        treeview.pack(fill="both", expand=True, pady=5)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=5)

        treeview.bind("<Double-1>", on_double_click)

        # Initial population
        paths = []
        refresh_treeview()

        notebook.add(main_frame, text="Available files on server:")
        notebook.add(stat_frame, text="Statistics")

        root.mainloop()

    def get_dir(self) -> list[RelativePath]:
        out_data: bytes = Encoder.encode({KeyData.REL_PATH: self.current_dir}, Command.DIR)
        self.conn.send(out_data)

        encoded_data: bytes = self.conn.recv(SIZE)
        response: dict = Encoder.decode(encoded_data)

        rel_paths: list[RelativePath] = response.get(KeyData.REL_PATHS)

        return rel_paths


if __name__ == "__main__":
    client_gui = ClientGui()
    client_gui.run()
