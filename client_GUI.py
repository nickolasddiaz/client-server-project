import copy
import os
import queue
import sys
import threading
import time
from pathlib import Path

from client_interface import ClientInterface
from relativepath import RelativePath
from type import Command, ResCode
import tkinter as tk
from tkinter import filedialog, ttk


class ClientGui(ClientInterface):
    def __init__(self):
        super().__init__()
        self.try_login: bool = False
        self.try_connect: bool = False
        self.PORT_str = None
        self.IP_str = None
        self.connect_str = None
        self.connect_frame = None
        self.chosen_dir: None | str = None
        self.rename_str = None
        self.rename_initial = None
        self.rename_msg = None
        self.rename_frame = None
        self.messages_str = None
        self.user_str = None
        self.pass_str = None
        self.login_frame = None
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
        self.stored_command: Command|None = None

    def welcome_connection(self):
        """Show connection screen and reset state"""
        self.try_connect = False
        self.connect_show()

    def get_connection(self) -> tuple[str, str]:
        """Wait for user to submit connection details"""
        while not self.try_connect:
            time.sleep(.1)

        self.try_connect = False
        return copy.deepcopy(self.IP_str.get()), copy.deepcopy(self.PORT_str.get())

    def print_connection_success(self):
        """Hide connection screen after successful connection"""
        self.app_print("Connected to server")
        self.connect_hide()

    def connect_show(self):
        """Display only the connection frame"""
        self.notebook.hide(self.main_frame)
        self.notebook.hide(self.stat_frame)
        self.notebook.hide(self.login_frame)
        self.notebook.hide(self.rename_frame)
        self.notebook.tab(self.connect_frame, state='normal')
        self.notebook.select(self.connect_frame)

    def connect_hide(self):
        """Hide connection frame - login will be shown next"""
        self.notebook.hide(self.connect_frame)

    def connect_submit(self):
        """User clicked submit on connection screen"""
        self.try_connect = True

    def connect_enter(self, event):
        """Handle Enter key on connection screen"""
        self.connect_submit()

    def welcome_login(self):
        """Show login screen and reset state"""
        self.try_login = False
        self.show_login()

    def get_login(self) -> tuple[str, str]:
        """Wait for user to submit login credentials"""
        while not self.try_login:
            time.sleep(.1)

        self.try_login = False
        return copy.deepcopy(self.user_str.get()), copy.deepcopy(self.pass_str.get())

    def print_login_success(self):
        """Show main app after successful login"""
        self.app_print("Login successful")
        self.hide_login()
        # Trigger initial directory listing
        self.stored_command = Command.DIR

    def show_login(self):
        """Display only the login frame"""
        self.notebook.hide(self.main_frame)
        self.notebook.hide(self.stat_frame)
        self.notebook.hide(self.connect_frame)
        self.notebook.hide(self.rename_frame)
        self.notebook.tab(self.login_frame, state='normal')
        self.notebook.select(self.login_frame)

    def hide_login(self):
        """Hide login and show main application"""
        self.notebook.hide(self.login_frame)
        self.notebook.tab(self.main_frame, state='normal')
        self.notebook.tab(self.stat_frame, state='normal')
        self.notebook.select(self.main_frame)

    def login_submit(self):
        """User clicked submit on login screen"""
        self.try_login = True

    def login_enter(self, event):
        """Handle Enter key on login screen"""
        self.login_submit()

    def app_print(self, msg: str) -> None:
        """Display message in the UI"""
        self.message_str.set(msg)


    def clear_screen(self) -> None:
        pass # not to be implemented or used for GUI

    def app_exit(self) -> None:
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        if self.root:
            self.root.quit()
        sys.exit(os.EX_OK)

    def app_error(self, status: ResCode) -> None:
        self.message_str.set(status.desc)


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

    def select_server_dir(self, exists: bool, skip_verification: bool = False) -> RelativePath | None:
        self.rename_show()
        while True:
            time.sleep(.1)

            if self.chosen_dir is not None:
                dir_in = copy.deepcopy(self.current_dir) / self.chosen_dir
                response: ResCode = self.verify_resource(skip_verification, exists, dir_in)
                self.chosen_dir = None

                if response == ResCode.OK:
                    break
                else:
                    self.rename_initial.set(response.desc)


        self.rename_hide()
        return dir_in

    def select_server_files(self) -> list[RelativePath]:
        selected_ids = self.treeview.selection()
        server_files: list[RelativePath] = []

        for iid in selected_ids:
            if iid == "parent":
                continue
            index = int(iid)
            selected_item = self.paths[index + (1 if self.current_dir.path() != Path('.') else 0)]
            server_files.append(selected_item)

        temp_paths: list[RelativePath] = []
        copy_path:  list[RelativePath] = copy.deepcopy(server_files)
        current_dir: RelativePath = copy.deepcopy(self.current_dir)

        for path in copy_path:
            if path.isdir:
                temp_paths.append(copy.deepcopy(current_dir) / path)
            else:
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
        if progress == 100:
            self.hide_progress_bar()
            return
        elif progress > 100:
            progress = 99

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

        # ------------------- creating the notebook and frame
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.main_frame = ttk.Frame(self.notebook)
        self.stat_frame = ttk.Frame(self.notebook)
        self.login_frame = ttk.Frame(self.notebook)
        self.rename_frame = ttk.Frame(self.notebook)
        self.connect_frame = ttk.Frame(self.notebook)

        self.message_str = tk.StringVar()
        self.message_str.set("Message Here")
        self.message_label = ttk.Label(self.root, textvariable=self.message_str)
        self.message_label.pack(anchor="w", pady=5)

        self.path_label = ttk.Label(self.main_frame, text="")
        self.path_label.pack(anchor="w", pady=5)

        # ------------------- Treeview file selector
        columns = ("Size", "Modified")
        self.treeview = ttk.Treeview(self.main_frame, columns=columns, show="tree headings", selectmode="extended")
        self.treeview.heading("#0", text="Name")
        self.treeview.heading("Size", text="Size")
        self.treeview.heading("Modified", text="Modified")

        self.treeview.column("#0", width=250, anchor="w")
        self.treeview.column("Size", width=50, anchor="e")
        self.treeview.column("Modified", width=150, anchor="center")

        self.treeview.pack(fill="both", expand=True, pady=5)

        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(pady=5)

        # bind function for double-clicking items
        self.treeview.bind("<Double-1>", self.on_double_click)

        # ------------------- context menu

        self.context_menu = self.create_context_menu()

        # Bind right-click to show context menu
        self.treeview.bind("<Button-3>", self.show_context_menu)  # For Windows/Linux
        self.treeview.bind("<Button-2>", self.show_context_menu)  # For macOS

        # Initial population
        self.paths = []
        self.refresh_treeview()

        # ------------------- adding frames into the notebook

        self.notebook.add(self.main_frame, text="Available files on server:")
        self.notebook.add(self.stat_frame, text="Statistics")
        self.notebook.add(self.login_frame, text="Login")
        self.notebook.add(self.rename_frame, text="Naming")
        self.notebook.add(self.connect_frame, text="Connect")

        # ------------------- connect screen
        self.connect_str = tk.StringVar(value="Enter the IP address and port.")
        tk.Label(self.connect_frame, textvariable=self.connect_str).pack(pady=10)

        tk.Label(self.connect_frame, text="IP address:").pack()
        self.IP_str = tk.StringVar(value=self.sett.CLIENT_IP)
        ttk.Entry(self.connect_frame, textvariable=self.IP_str).pack(pady=5)

        tk.Label(self.connect_frame, text="Port:").pack()
        self.PORT_str = tk.StringVar(value=str(self.sett.PORT))
        ttk.Entry(self.connect_frame, textvariable=self.PORT_str).pack(pady=5)

        self.connect_frame.bind('<Return>', self.connect_enter)
        ttk.Button(self.connect_frame, text="Submit", command=self.connect_submit).pack(pady=10)

        # ------------------- rename screen
        
        self.rename_msg = tk.StringVar(value="Name your file/directory")
        tk.Label(self.rename_frame, textvariable=self.rename_msg).pack(pady=10)

        self.rename_initial = tk.StringVar(value="")
        tk.Label(self.rename_frame, textvariable=self.rename_initial).pack(pady=10)

        tk.Label(self.rename_frame, text="Name:").pack()
        self.rename_str = tk.StringVar()
        ttk.Entry(self.rename_frame, textvariable=self.rename_str).pack(pady=5)

        ttk.Button(self.rename_frame, text="Submit", command=self.rename_submit).pack(pady=10)


        # ------------------- login screen 

        self.messages_str = tk.StringVar(value="Enter your username and password.")
        tk.Label(self.login_frame, textvariable=self.messages_str).pack(pady=10)

        tk.Label(self.login_frame, text="Username:").pack()
        self.user_str = tk.StringVar(value=self.sett.USERNAME)
        ttk.Entry(self.login_frame, textvariable=self.user_str).pack(pady=5)

        tk.Label(self.login_frame, text="Password:").pack()
        self.pass_str = tk.StringVar() # password is not shown
        ttk.Entry(self.login_frame, textvariable=self.pass_str, show="*").pack(pady=5)

        self.login_frame.bind('<Return>', self.login_enter)
        ttk.Button(self.login_frame, text="Submit", command=self.login_submit).pack(pady=10)

        # ------------------- Network Statistics

        self.stat_str = tk.StringVar(value="Network Statistics")
        self.stat_label = ttk.Label(self.stat_frame, textvariable=self.stat_str)
        self.stat_label.pack(pady=10)

        # ------------------- progress bar

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

        # ------------------- hiding the frames
        self.notebook.hide(self.main_frame)
        self.notebook.hide(self.stat_frame)
        self.notebook.hide(self.rename_frame)
        self.notebook.hide(self.login_frame)
        # Select the login tab
        self.notebook.select(self.connect_frame)
        # Hide the progress bar
        self.hide_progress_bar()

        # ------------------- creating a new thread for the two event loops

        self.network_thread = threading.Thread(target=self.run, daemon=True)
        self.network_thread.start()

        self.root.mainloop()

    def rename_submit(self):
        self.chosen_dir =  copy.deepcopy(self.rename_str.get())

    def rename_show(self):
        self.notebook.hide(self.main_frame)
        self.notebook.hide(self.stat_frame)
        self.notebook.tab(self.rename_frame, state='normal')
        self.notebook.select(self.rename_frame)

    def rename_hide(self):
        self.notebook.tab(self.main_frame, state='normal')
        self.notebook.tab(self.stat_frame, state='normal')
        self.notebook.hide(self.rename_frame)
        self.notebook.select(self.main_frame)

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
        context_menu.add_separator()
        context_menu.add_command(label="Disconnect", command=self.disconnect)
        context_menu.add_command(label="Log Out", command=self.logout)
        context_menu.add_separator()
        context_menu.add_command(label="Quit", command=self.app_exit)

        return context_menu

    def disconnect(self):
        self.stored_command = Command.DISCONNECT

    def logout(self):
        self.stored_command = Command.LOGOUT

    def set_dir(self):
        self.stored_command = Command.DIR

    def menu_download(self):
        """Handle download cmd from context menu"""
        self.stored_command = Command.DOWNLOAD

    def menu_upload(self):
        """Handle upload cmd from context menu"""
        self.stored_command = Command.UPLOAD

    def menu_delete(self):
        """Handle delete cmd from context menu"""
        selected_ids = self.treeview.selection()
        if not selected_ids:
            self.message_str.set("No items selected for deletion")
            return

        self.stored_command = Command.DELETE

    def menu_mkdir(self):
        """Handle mkdir cmd from context menu"""
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
            self.current_dir = self.current_dir /selected_item
            self.stored_command = Command.DIR


if __name__ == "__main__":
    client_gui = ClientGui()
    client_gui.main_gui()