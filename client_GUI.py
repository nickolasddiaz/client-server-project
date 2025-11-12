import copy
import os
import queue
import sys
import threading
import time
from pathlib import Path

from client_interface import ClientInterface
from encoder import Encoder
from relativepath import RelativePath
from type import Command, ResCode
import tkinter as tk
from tkinter import filedialog, ttk


class ClientGui(ClientInterface):
    def __init__(self):
        super().__init__()
        self.network_thread = None
        self.context_menu = None
        self.command_queue = queue.Queue()
        self.running = None
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
        self.stored_command: Command|None = Command.DIR


    def clear_screen(self) -> None:
        pass # not to be implemented or used for GUI

    def app_exit(self) -> None:
        self.running = False
        if self.conn:
            try:
                out_data: bytes = Encoder.encode({}, Command.LOGOUT)
                self.conn.send(out_data)
                self.conn.close()
            except:
                pass
        if self.root:
            self.root.quit()
        sys.exit(os.EX_OK)

    def app_error(self, status: ResCode) -> None:
        self.message_str.set(status.desc)

    def app_print(self, msg: str) -> None:
        self.message_str.set(msg)

    def app_error_print(self, msg: str) -> None:
        self.message_str.set(msg)

    def app_print_statistics(self, msg: str) -> None:
        self.stat_str.set(msg)

    def command_input(self) -> Command | None:

        while self.stored_command is None:
            time.sleep(.1)


        temp, self.stored_command = self.stored_command, None

        return copy.deepcopy(temp)

    def show_dir(self, rel_paths: list[RelativePath]) -> None:
        self.paths = copy.deepcopy(rel_paths)
        self.refresh_treeview()

    def receive_user_pass(self) -> None:
        login_window = tk.Tk()
        login_window.title("Password Prompt")
        login_window.geometry("300x200")

        messages_str = tk.StringVar(value="Enter your username and password.")
        tk.Label(login_window, textvariable=messages_str).pack(pady=10)

        tk.Label(login_window, text="Username:").pack()
        user_str = tk.StringVar()
        ttk.Entry(login_window, textvariable=user_str).pack(pady=5)

        tk.Label(login_window, text="Password:").pack()
        pass_str = tk.StringVar()
        ttk.Entry(login_window, textvariable=pass_str, show="*").pack(pady=5)

        def on_submit():
            self.user_name = user_str.get()
            self.password = pass_str.get()

            response_code: ResCode = self.verify_userpass()
            if response_code == ResCode.OK:
                login_window.destroy()
            else:
                messages_str.set(response_code.desc)

        def on_enter(event):
            on_submit()

        login_window.bind('<Return>', on_enter)
        ttk.Button(login_window, text="Submit", command=on_submit).pack(pady=10)

        login_window.mainloop()

    def select_server_dir(self, exists: bool, skip_verification: bool = False) -> RelativePath | None:
        return copy.deepcopy(self.current_dir)

    def select_server_files(self) -> list[RelativePath]:
        selected_ids = self.treeview.selection()
        server_files: list[RelativePath] = []

        for iid in selected_ids:
            if iid == "parent":
                continue
            index = int(iid)
            selected_item = self.paths[index + (1 if self.current_dir.path() != Path('.') else 0)]
            if selected_item.isfile:
                server_files.append(selected_item)

        temp_paths: list[RelativePath] = []
        copy_path:  list[RelativePath] = copy.deepcopy(server_files)
        current_dir: RelativePath = copy.deepcopy(self.current_dir)

        for path in copy_path:
            temp_paths.append(copy.deepcopy(current_dir) / path.name)

        return temp_paths

    def select_client_files(self) -> list[tuple[Path, str]]:
        file_paths = filedialog.askopenfilenames(
            title="Select Multiple Files",
            filetypes=[("All files", "*.*")]
        )
        paths: list[tuple[Path, str]] = []
        if file_paths:
            for file_path in file_paths:
                p = Path(file_path)
                paths.append((p, p.name))

        return copy.deepcopy(paths)


    def select_client_dir(self) -> Path | None:
        directory_path: str = filedialog.askdirectory(
            initialdir="/",
            title="Select a Directory"
        )
        if directory_path:
            return copy.deepcopy(Path(directory_path))
        else:
            return None


    def hide_progress_bar(self):
        self.root.after(0, lambda: self.prog_name.pack_forget())
        self.root.after(0, lambda: self.prog_label.pack_forget())
        self.root.after(0, lambda: self.prog_bar.pack_forget())

    def show_progress_bar(self):
        self.root.after(0, lambda: self.prog_name.pack())
        self.root.after(0, lambda: self.prog_label.pack())
        self.root.after(0, lambda: self.prog_bar.pack())

    def progress_bar(self, progress: int, byte_per_sec: int, num_bytes: int) -> None:
        if progress > 99:
            self.hide_progress_bar()
            return

        self.show_progress_bar()
        self.root.after(0, lambda: self.prog_var.set(progress))
        self.root.after(0, lambda: self.prog_label_str.set(self.progress_str(progress, byte_per_sec, num_bytes)))

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

        # Create context menu
        self.context_menu = self.create_context_menu()

        # Bind right-click to show context menu
        self.treeview.bind("<Button-3>", self.show_context_menu)  # For Windows/Linux
        self.treeview.bind("<Button-2>", self.show_context_menu)  # For macOS

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
        self.prog_label_str.set(self.progress_str(0, 0, 0))
        self.prog_label = ttk.Label(self.prog_frame, textvariable=self.prog_label_str)
        self.prog_label.pack(side=tk.LEFT, padx=5)

        self.hide_progress_bar()

        self.network_thread = threading.Thread(target=self.run, daemon=True)
        self.network_thread.start()

        self.root.mainloop()


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

    def create_context_menu(self):
        """Create the right-click context menu"""
        context_menu = tk.Menu(self.root, tearoff=0)

        context_menu.add_command(label="Download", command=self.menu_download)
        context_menu.add_command(label="Upload", command=self.menu_upload)
        context_menu.add_command(label="Delete", command=self.menu_delete)
        context_menu.add_separator()
        context_menu.add_command(label="Create Directory", command=self.menu_mkdir)
        context_menu.add_separator()
        context_menu.add_command(label="Refresh", command=self.set_dir)
        context_menu.add_command(label="Quit", command=self.app_exit)

        return context_menu

    def set_dir(self):
        self.stored_command = Command.DIR

    def menu_download(self):
        """Handle download command from context menu"""
        self.stored_command = Command.DOWNLOAD

    def menu_upload(self):
        """Handle upload command from context menu"""
        self.stored_command = Command.UPLOAD

    def menu_delete(self):
        """Handle delete command from context menu"""
        selected_ids = self.treeview.selection()
        if not selected_ids:
            self.message_str.set("No items selected for deletion")
            return

        self.stored_command = Command.DELETE

    def menu_mkdir(self):
        """Handle mkdir command from context menu"""
        self.stored_command = Command.MKDIR

    def show_context_menu(self, event):
        """Display context menu at cursor position"""
        try:
            # Select the item under the cursor
            item_id = self.treeview.identify_row(event.y)
            if item_id:
                self.treeview.selection_set(item_id)
                self.treeview.focus(item_id)

            # Display the menu at the cursor position
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Release the grab
            self.context_menu.grab_release()


    def on_double_click(self, event):
        item_id = self.treeview.focus()
        if not item_id:
            return

        if item_id == "parent":
            self.current_dir = self.current_dir.go_up()
            self.stored_command = Command.DIR
            return

        index = int(item_id)
        selected_item = self.paths[index + (1 if self.current_dir.path() != Path('.') else 0)]

        if selected_item.isdir:
            self.current_dir = selected_item
            self.stored_command = Command.DIR


if __name__ == "__main__":
    client_gui = ClientGui()
    client_gui.main_gui()