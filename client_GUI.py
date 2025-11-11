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
        self.stat_str = None
        self.stat_label = None
        self.message_str = None
        self.paths: list[RelativePath] = []
        self.select_paths = None
        self.prog_label_str = None
        self.prog_name = None
        self.btn_frame = None
        self.treeview = None
        self.notebook = None
        self.main_frame = None
        self.stat_frame = None
        self.path_label = None
        self.message_label = None
        self.root = None
        self.prog_var = None
        self.received_first_msg = False

        self.prog_label = None
        self.prog_bar = None
        self.prog_frame = None
        self.stored_command: Command|None = None
        self.set_command: bool = False


    def clear_screen(self) -> None:
        pass # not to be implemented or used for GUI

    def app_exit(self) -> None:
        sys.exit(os.EX_OK)

    def app_error(self, status: ResCode) -> None:
        self.message_str.set(status.desc)

    def app_print(self, msg: str) -> None:
        if self.received_first_msg:
            self.message_str.set(msg)
        else:
            self.received_first_msg = True
            self.main_gui()
            self.message_str.set(msg)

    def app_error_print(self, msg: str) -> None:
        self.message_str.set(msg)

    def app_print_statistics(self, msg: str) -> None:
        self.stat_str.set(msg)

    def command_input(self) -> Command:
        while not self.set_command:
            pass

        return self.stored_command


    def show_dir(self, rel_paths: list[RelativePath]) -> None:
        pass # not to be implemented or used for GUI

    def receive_user_pass(self) -> None:
        root = tk.Tk()
        root.title("Password Prompt")
        root.geometry("300x200")

        messages_str = tk.StringVar(value="Enter your username and password.")
        tk.Label(root, textvariable=messages_str).pack(pady=10)

        user_str = tk.StringVar()
        ttk.Entry(root, textvariable=user_str).pack(pady=5)

        pass_str = tk.StringVar()
        ttk.Entry(root, textvariable=pass_str, show="*").pack(pady=5)

        def on_submit():
            self.user_name = user_str.get()
            self.password = user_str.get()

            response_code: ResCode = self.verify_userpass()
            if response_code == ResCode.OK:
                root.destroy()
            else:
                messages_str.set(response_code.desc)

        ttk.Button(root, text="Submit", command=on_submit).pack(pady=10)

        root.mainloop()

    def select_server_dir(self, exists: bool, skip_verification: bool = False) -> RelativePath | None:
        return self.current_dir

    def select_server_files(self) -> list[RelativePath]:
        server_files: list[RelativePath] = []
        for path in self.paths:
            if path.isfile:
                server_files.append(path)
        return server_files

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


    def hide_progress_bar(self):
        self.prog_name.pack_forget()
        self.prog_label.pack_forget()
        self.prog_bar.pack_forget()

    def show_progress_bar(self):
        self.prog_name.pack()
        self.prog_label.pack()
        self.prog_bar.pack()

    def progress_bar(self, progress: int, byte_per_sec: int, num_bytes: int) -> None:
        if progress > 99:
            self.hide_progress_bar()
            return

        self.show_progress_bar()

        self.prog_var.set(progress)
        self.prog_label_str.set(self.progress_str(progress, byte_per_sec, num_bytes))



    def main_gui(self):
        self.select_paths: list[RelativePath] = []

        self.root = tk.Tk()
        self.root.title("Select file/s")
        self.root.geometry("700x500")

        # Bind the on_closing function to the WM_DELETE_WINDOW protocol
        self.root.protocol("WM_DELETE_WINDOW", self.app_exit)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.main_frame = ttk.Frame(self.notebook)
        self.stat_frame = ttk.Frame(self.notebook)

        self.message_str = tk.StringVar()
        self.message_str.set("Message Here")
        self.message_label = ttk.Label(self.main_frame, textvariable=self.message_str)
        self.message_label.pack(anchor="w", pady=5)

        self.path_label = ttk.Label(self.main_frame, text="")
        self.path_label.pack(anchor="w", pady=5)

        # Treeview setup
        columns = ("Size", "Modified")
        self.treeview = ttk.Treeview(self.main_frame, columns=columns, show="tree headings", selectmode="extended")
        self.treeview.heading("#0", text="Name")
        self.treeview.heading("Size", text="Size")
        self.treeview.heading("Modified", text="Modified")

        self.treeview.column("#0", width=250, anchor="w")
        self.treeview.column("Size", width=50, anchor="e")
        self.treeview.column("Modified", width=150, anchor="center")

        self.treeview.pack(fill="both", expand=True, pady=5)

        # Buttons
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(pady=5)

        self.treeview.bind("<Double-1>", self.on_double_click)

        # Initial population
        self.paths = []
        self.refresh_treeview()

        self.notebook.add(self.main_frame, text="Available files on server:")
        self.notebook.add(self.stat_frame, text="Statistics")

        self.stat_str = tk.StringVar()
        self.stat_label = ttk.Label(self.stat_frame, textvariable=self.stat_str)
        self.stat_str.set("Network Statistics")

        self.prog_frame = ttk.Frame(self.root)
        self.prog_frame.pack(pady=5)

        self.prog_name = ttk.Label(self.prog_frame, text="Transferring:")
        self.prog_name.pack(side=tk.LEFT, padx=5)

        self.prog_var = tk.IntVar()
        self.prog_bar = ttk.Progressbar(self.prog_frame, variable=self.prog_var, maximum=100, length=200,
                                        mode="determinate", style='success.Striped.Horizontal.TProgressbar')
        self.prog_bar.pack(side=tk.LEFT, padx=5)

        self.prog_label_str = tk.StringVar()
        self.prog_label_str.set(self.progress_str(0,0,0))
        self.prog_label = ttk.Label(self.prog_frame, textvariable=self.prog_label_str)
        self.prog_label.pack(side=tk.LEFT, padx=5)

        self.hide_progress_bar()

        self.root.mainloop()

    def set_dir(self) -> None:
        out_data: bytes = Encoder.encode({KeyData.REL_PATH: self.current_dir}, Command.DIR)
        self.conn.send(out_data)

        encoded_data: bytes = self.conn.recv(SIZE)
        response: dict = Encoder.decode(encoded_data)

        self.paths: list[RelativePath] = response.get(KeyData.REL_PATHS)

    def on_select(self, event):
        selected_ids = self.treeview.selection()
        for iid in selected_ids:
            index = int(iid)
            selected_item = self.paths[index + (1 if self.current_dir.path() != Path('.') else 0)]
            self.select_paths.append(selected_item)

        self.root.destroy()

    def refresh_treeview(self):
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        self.set_dir()

        # Add parent directory option
        if self.current_dir.path() != Path('.'):
            parent_item = self.current_dir.go_up()
            self.paths.insert(0, parent_item)
            self.treeview.insert(
                "", "end", iid="parent", text="📁 .. (Parent Directory)",
                values=("", "", "")
            )

        # Insert current directory content
        for i, p in enumerate(self.paths[1:] if self.current_dir.path() != Path('.') else self.paths):
            prefix = "📁" if p.isdir else "📄"
            self.treeview.insert(
                "",
                "end",
                iid=str(i),
                text=f"{prefix} {p.true_name}",
                values=(f"{p.str_bytes}", p.time_str)
            )

        self.path_label.config(text=f"Current Directory: {self.current_dir.location}\\")


    def right_click_menu(self):
        root = tk.Tk()
        root.title("Right Click Menu Example")
        context_menu = tk.Menu(root, tearoff=0)

        def download():
            self.stored_command = Command.DOWNLOAD

        def upload():
            self.stored_command = Command.UPLOAD

        def delete():
            self.stored_command = Command.DELETE

        def mkdir():
            self.stored_command = Command.MKDIR

        context_menu.add_command(label="Download", command=download)
        context_menu.add_command(label="Upload", command=upload)
        context_menu.add_command(label="Delete", command=delete)
        context_menu.add_command(label="Create Directory", command=mkdir)
        context_menu.add_command(label="Quit", command=self.app_exit)


    def on_double_click(self, event):
        item_id = self.treeview.focus()
        if not item_id:
            return

        if item_id == "parent":
            self.current_dir = self.current_dir.go_up()
            self.refresh_treeview()
            return

        index = int(item_id)
        selected_item = self.paths[index + (1 if self.current_dir.path() != Path('.') else 0)]

        if selected_item.isdir:
            self.current_dir = selected_item
            self.refresh_treeview()


if __name__ == "__main__":
    client_gui = ClientGui()
    client_gui.run()
