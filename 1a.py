import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import shutil  # For shutil.which to find Java
import uuid    # For generating UUIDs for offline play
import random  # For fallback username
import threading  # To run installations/launching in a separate thread
import logging    # For logging debug information

try:
    import minecraft_launcher_lib as mclib
except ImportError:
    messagebox.showerror("喵! Error", "minecraft-launcher-lib is not installed!\nPlease install it by running: pip install minecraft-launcher-lib")
    exit()

# Set up logging
logging.basicConfig(filename='catclient.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class CatClient:
    def __init__(self, root):
        self.root = root
        root.title("CatClient")
        root.minsize(500, 450)

        # Variables
        self.source_var = tk.StringVar(value="Official")  # Default source
        self.version_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.status_var.set("Ready, nya~ Fetch versions to start!")
        self.username_var = tk.StringVar(value=f"Player{random.randint(100, 999)}")
        self.dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Documents", "Minecraft"))
        self.ram_var = tk.StringVar(value="2G")
        self.forge_var = tk.BooleanVar(value=False)
        self.versions_cache = []

        # --- UI Elements ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Source Selection
        ttk.Label(main_frame, text="Source:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.source_combo = ttk.Combobox(main_frame, textvariable=self.source_var, values=["Official", "TLauncher"], state="readonly")
        self.source_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.source_combo.bind("<<ComboboxSelected>>", self.on_source_selected)

        # Username
        ttk.Label(main_frame, text="Username 喵:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(main_frame, textvariable=self.username_var, width=30).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Minecraft Directory
        ttk.Label(main_frame, text="Minecraft Directory:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=25)
        self.dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.browse_button = ttk.Button(dir_frame, text="Browse...", command=self.browse_directory)
        self.browse_button.pack(side=tk.LEFT, padx=(5, 0))

        # Version Selection
        ttk.Label(main_frame, text="Select Minecraft Version:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.version_combo = ttk.Combobox(main_frame, textvariable=self.version_var, state="readonly", width=28)
        self.version_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.version_combo.bind("<<ComboboxSelected>>", self.on_version_selected)

        # RAM Allocation
        ttk.Label(main_frame, text="RAM Allocation (e.g., 2G, 4096M):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(main_frame, textvariable=self.ram_var, width=30).grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Forge Checkbox
        self.forge_check = ttk.Checkbutton(main_frame, text="Install/Use Forge? 喵w喵", variable=self.forge_var, command=self.toggle_forge_versions)
        self.forge_check.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Refresh Versions 喵!", command=self.fetch_versions_thread).pack(side=tk.LEFT, padx=5)
        self.launch_button = ttk.Button(button_frame, text="Launch Minecraft! >ω<", command=self.launch_minecraft_thread, state=tk.DISABLED)
        self.launch_button.pack(side=tk.LEFT, padx=5)

        # Status Bar
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=5)
        self.status_label.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        main_frame.grid_columnconfigure(1, weight=1)

        self.check_java()
        self.on_source_selected()  # Initialize based on default source

    def check_java(self):
        java_path = shutil.which("java") or shutil.which("javaw")
        if not java_path:
            self.status_var.set("Warning: Java not found in PATH! Minecraft might not launch. Install Java, nya!")
            messagebox.showwarning("Java Not Found 喵!", "Java executable not found in PATH. Install Java to launch Minecraft.")
        else:
            self.status_var.set(f"Java found at: {java_path}. Ready, nya~")

    def browse_directory(self):
        directory = filedialog.askdirectory(title="Select Minecraft Directory")
        if directory:
            self.dir_var.set(directory)
            self.status_var.set(f"Directory set to: {directory}")
            self.fetch_versions_thread()

    def on_source_selected(self, event=None):
        source = self.source_var.get()
        if source == "Official":
            self.dir_entry.config(state="normal")
            self.browse_button.config(state="normal")
            if not self.dir_var.get():
                self.dir_var.set(os.path.join(os.path.expanduser("~"), "Documents", "Minecraft"))
            self.forge_check.config(state="normal")
        elif source == "TLauncher":
            tlauncher_dir = os.path.join(os.getenv('APPDATA') if os.name == 'nt' else os.path.expanduser("~"), ".tlauncher")
            if not os.path.isdir(tlauncher_dir):
                messagebox.showerror("Error 喵!", "TLauncher directory not found! Please install TLauncher or check the directory path.")
                self.source_var.set("Official")
                self.on_source_selected()
                return
            self.dir_var.set(tlauncher_dir)
            self.dir_entry.config(state="readonly")
            self.browse_button.config(state="disabled")
            self.forge_check.config(state="disabled")
            self.forge_var.set(False)  # Disable Forge for TLauncher
        self.fetch_versions_thread()

    def _fetch_versions_task(self):
        self.status_var.set("Fetching versions, purrrr...")
        self.launch_button.config(state=tk.DISABLED)
        try:
            source = self.source_var.get()
            minecraft_dir = self.dir_var.get()
            if source == "Official":
                all_versions_list = mclib.utils.get_version_list()
                self.versions_cache = all_versions_list
                installed_versions = set(mclib.utils.get_installed_versions(minecraft_dir))
                display_versions = []
                for v in all_versions_list:
                    suffix = " (installed)" if v["id"] in installed_versions else ""
                    if self.forge_var.get():
                        if v["type"] == "release":
                            display_versions.append(f"{v['id']}{suffix}")
                    else:
                        display_versions.append(f"{v['id']} ({v['type']}){suffix}")
            elif source == "TLauncher":
                installed_versions = mclib.utils.get_installed_versions(minecraft_dir)
                self.versions_cache = installed_versions
                display_versions = [v["id"] for v in installed_versions]
                if not display_versions:
                    self.status_var.set("No versions found in TLauncher directory. Install versions via TLauncher, nya!")

            if display_versions:
                self.version_combo['values'] = display_versions
                self.version_combo.set(display_versions[0])
                self.status_var.set(f"Versions fetched from {source}! Select one and launch, nya~")
                self.launch_button.config(state=tk.NORMAL)
            else:
                self.version_combo['values'] = []
                self.version_combo.set('')
                self.status_var.set("No versions found. Meow :(")
        except Exception as e:
            logging.error(f"Error fetching versions: {e}")
            self.status_var.set(f"Error fetching versions: {e}")
            messagebox.showerror("Error 喵!", f"Could not fetch versions: {e}")
        finally:
            if not self.version_var.get() or not self.versions_cache:
                self.launch_button.config(state=tk.DISABLED)
            else:
                self.launch_button.config(state=tk.NORMAL)

    def fetch_versions_thread(self):
        threading.Thread(target=self._fetch_versions_task, daemon=True).start()

    def on_version_selected(self, event=None):
        selected_display_name = self.version_var.get()
        self.status_var.set(f"Selected: {selected_display_name}. Ready to launch! ^_^")

    def toggle_forge_versions(self):
        self.status_var.set("Toggled Forge! Refreshing versions, purrfect!")
        self.fetch_versions_thread()

    def _launch_minecraft_task(self):
        self.launch_button.config(state=tk.DISABLED)
        self.status_var.set("Preparing to launch... hold on to your whiskers!")

        selected_display_name = self.version_var.get()
        if not selected_display_name:
            self.status_var.set("No version selected, nya!")
            messagebox.showerror("Error 냥!", "Please select a Minecraft version first!")
            self.launch_button.config(state=tk.NORMAL)
            return

        # Extract version ID from display name (remove suffixes like "(release)")
        version_id = selected_display_name.split(" ")[0]
        minecraft_directory = self.dir_var.get()
        source = self.source_var.get()

        if not os.path.isdir(minecraft_directory):
            try:
                os.makedirs(minecraft_directory, exist_ok=True)
                self.status_var.set(f"Created Minecraft directory: {minecraft_directory}")
            except Exception as e:
                logging.error(f"Error creating directory: {e}")
                self.status_var.set(f"Error creating directory: {e}")
                messagebox.showerror("Directory Error 喵!", f"Could not create directory: {minecraft_directory}\n{e}")
                self.launch_button.config(state=tk.NORMAL)
                return

        username = self.username_var.get() or f"Player{random.randint(100, 999)}"
        ram_allocation = self.ram_var.get()

        options = {
            "username": username,
            "uuid": str(uuid.uuid4()),
            "token": "",  # Offline mode
            "jvmArguments": [
                f"-Xmx{ram_allocation}",
                f"-Xms{ram_allocation}",
                "-Duser.language=en",
                "-Duser.country=US"
            ],
            "launcherName": "CatClient",
            "launcherVersion": "0.1"
        }

        try:
            version_to_launch = version_id
            if source == "Official":
                self.status_var.set(f"Installing Minecraft {version_id}, please wait... nya!")
                mclib.install.install_minecraft_version(versionid=version_id, minecraft_directory=minecraft_directory)
                self.status_var.set(f"Minecraft {version_id} is installed! Meowvellous!")
                if self.forge_var.get():
                    self.status_var.set(f"Looking for Forge for {version_id}...")
                    try:
                        forge_version_name = mclib.forge.find_forge_version(version_id)
                        if forge_version_name:
                            self.status_var.set(f"Found Forge: {forge_version_name}. Installing...")
                            mclib.forge.install_forge_version(forge_version_name, minecraft_directory,
                                                              callback={'setStatus': lambda text: self.status_var.set(f"Forge: {text}")})
                            self.status_var.set(f"Forge {forge_version_name} installed!")
                            version_to_launch = forge_version_name
                        else:
                            self.status_var.set(f"No Forge for {version_id}. Launching vanilla.")
                            messagebox.showwarning("Forge Not Found 喵~", f"No Forge version found for {version_id}. Launching vanilla.")
                    except Exception as e:
                        logging.error(f"Forge error for {version_id}: {e}")
                        self.status_var.set(f"Forge error: {e}. Launching vanilla.")
                        messagebox.showerror("Forge Error 냥!", f"Forge setup failed:\n{e}\nLaunching vanilla.")

            # Generate and log the launch command
            self.status_var.set(f"Getting command for {version_to_launch}...")
            command = mclib.command.get_minecraft_command(version=version_to_launch,
                                                          minecraft_directory=minecraft_directory,
                                                          options=options)
            logging.info(f"Launch command: {' '.join(command)}")
            self.status_var.set(f"Launching {version_to_launch} as {username}! Pew pew!")
            subprocess.Popen(command, cwd=minecraft_directory)

        except Exception as e:
            logging.error(f"Launch Error: {e}")
            self.status_var.set(f"Launch Error: {e}")
            messagebox.showerror("Launch Error 냥!", f"Failed to launch Minecraft:\n{e}")
        finally:
            self.launch_button.config(state=tk.NORMAL)

    def launch_minecraft_thread(self):
        threading.Thread(target=self._launch_minecraft_task, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = CatClient(root)
    root.mainloop()
