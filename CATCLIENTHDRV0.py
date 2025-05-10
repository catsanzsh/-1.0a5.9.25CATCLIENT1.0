import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import shutil  # For shutil.which to find Java
import uuid    # For generating UUIDs for offline play
import random  # For fallback username
import threading  # To run installations/launching in a separate thread

try:
    import minecraft_launcher_lib as mclib
except ImportError:
    messagebox.showerror("喵! Error", "minecraft-launcher-lib is not installed!\nPlease install it by running: pip install minecraft-launcher-lib")
    exit()

class CatClient:
    def __init__(self, root):
        self.root = root
        root.title("CatClient")  # Renamed to CatClient
        root.minsize(500, 450)

        # Variables
        self.version_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.status_var.set("Ready, nya~ Fetch versions to start!")
        self.username_var = tk.StringVar(value=f"Player{random.randint(100, 999)}")  # Default random username
        # Set default Minecraft directory to ~/Documents/Minecraft
        self.dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Documents", "Minecraft"))
        self.ram_var = tk.StringVar(value="2G")  # Default RAM
        self.forge_var = tk.BooleanVar(value=False)
        self.versions_cache = []  # To store full version info

        # --- UI Elements ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Username
        ttk.Label(main_frame, text="Username 喵:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(main_frame, textvariable=self.username_var, width=30).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Minecraft Directory
        ttk.Label(main_frame, text="Minecraft Directory:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=25).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_directory).pack(side=tk.LEFT, padx=(5, 0))

        # Version Selection
        ttk.Label(main_frame, text="Select Minecraft Version:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.version_combo = ttk.Combobox(main_frame, textvariable=self.version_var, state="readonly", width=28)
        self.version_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.version_combo.bind("<<ComboboxSelected>>", self.on_version_selected)

        # RAM Allocation
        ttk.Label(main_frame, text="RAM Allocation (e.g., 2G, 4096M):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(main_frame, textvariable=self.ram_var, width=30).grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Forge Checkbox
        self.forge_check = ttk.Checkbutton(main_frame, text="Install/Use Forge? 喵w喵", variable=self.forge_var, command=self.toggle_forge_versions)
        self.forge_check.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Refresh Versions 喵!", command=self.fetch_versions_thread).pack(side=tk.LEFT, padx=5)
        self.launch_button = ttk.Button(button_frame, text="Launch Minecraft! >ω<", command=self.launch_minecraft_thread, state=tk.DISABLED)
        self.launch_button.pack(side=tk.LEFT, padx=5)

        # Status Bar
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=5)
        self.status_label.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        main_frame.grid_columnconfigure(1, weight=1)  # Allow entry and combobox to expand

        self.check_java()
        self.fetch_versions_thread()  # Fetch versions on startup

    def check_java(self):
        java_path = shutil.which("java") or shutil.which("javaw")
        if not java_path:
            self.status_var.set("Warning: Java not found in PATH! Minecraft might not launch. Install Java, nya!")
            messagebox.showwarning("Java Not Found 喵!", "Java executable (java/javaw) was not found in your system's PATH. Minecraft might fail to launch. Please install Java and make sure it's in your PATH.")
        else:
            self.status_var.set(f"Java found at: {java_path}. Ready, nya~")

    def browse_directory(self):
        directory = filedialog.askdirectory(title="Select Minecraft Directory")
        if directory:
            self.dir_var.set(directory)
            self.status_var.set(f"Directory set to: {directory}")
            self.fetch_versions_thread()  # Re-fetch versions as they might be specific to a directory context for installed ones

    def _fetch_versions_task(self):
        self.status_var.set("Fetching versions, purrrr...")
        self.launch_button.config(state=tk.DISABLED)
        try:
            # Get all available versions (releases and snapshots)
            all_versions_list = mclib.utils.get_version_list()
            self.versions_cache = all_versions_list

            current_minecraft_dir = self.dir_var.get()
            installed_versions = set(mclib.utils.get_installed_versions(current_minecraft_dir))

            display_versions = []
            for v in all_versions_list:
                suffix = " (installed)" if v["id"] in installed_versions else ""
                if self.forge_var.get():
                    if v["type"] == "release":
                        display_versions.append(f"{v['id']}{suffix}")
                else:
                    display_versions.append(f"{v['id']} ({v['type']}){suffix}")

            if display_versions:
                self.version_combo['values'] = display_versions
                self.version_combo.set(display_versions[0])  # Select the first one
                self.status_var.set("Versions fetched! Select one and launch, nya~")
                self.launch_button.config(state=tk.NORMAL)
            else:
                self.version_combo['values'] = []
                self.version_combo.set('')
                self.status_var.set("No versions found or an error occurred. Meow :(")
        except Exception as e:
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
        self.status_var.set("Toggled Forge! Refreshing versions for you, purrfect!")
        self.fetch_versions_thread()  # Re-fetch and filter versions based on Forge selection

    def _launch_minecraft_task(self):
        self.launch_button.config(state=tk.DISABLED)
        self.status_var.set("Preparing to launch... hold on to your whiskers!")

        selected_display_name = self.version_var.get()
        if not selected_display_name:
            self.status_var.set("No version selected, nya!")
            messagebox.showerror("Error 냥!", "Please select a Minecraft version first!")
            self.launch_button.config(state=tk.NORMAL)
            return

        # Extract the actual version ID from the display name
        version_id = selected_display_name.split(" ")[0]

        minecraft_directory = self.dir_var.get()
        if not os.path.isdir(minecraft_directory):
            try:
                os.makedirs(minecraft_directory, exist_ok=True)
                self.status_var.set(f"Created Minecraft directory: {minecraft_directory}")
            except Exception as e:
                self.status_var.set(f"Error creating directory: {e}")
                messagebox.showerror("Directory Error 喵!", f"Could not create Minecraft directory: {minecraft_directory}\n{e}")
                self.launch_button.config(state=tk.NORMAL)
                return

        username = self.username_var.get() if self.username_var.get() else f"Player{random.randint(100, 999)}"
        ram_allocation = self.ram_var.get()

        options = {
            "username": username,
            "uuid": str(uuid.uuid4()),  # Generate a new UUID for each offline launch
            "token": "",  # For offline mode, token is typically empty
            "jvmArguments": [
                f"-Xmx{ram_allocation}",
                f"-Xms{ram_allocation}",  # Fixed to match -Xmx
                "-Duser.language=en",     # Force English language
                "-Duser.country=US"
            ],
            "launcherName": "CatClient",  # Updated launcher name
            "launcherVersion": "0.1"
        }

        try:
            self.status_var.set(f"Installing Minecraft {version_id}, please wait... this might take a while, nya!")
            mclib.install.install_minecraft_version(versionid=version_id, minecraft_directory=minecraft_directory)
            self.status_var.set(f"Minecraft {version_id} is installed! Meowvellous!")

            version_to_launch = version_id

            if self.forge_var.get():
                self.status_var.set(f"Looking for Forge for {version_id}...")
                try:
                    forge_version_name = mclib.forge.find_forge_version(version_id)
                    if forge_version_name:
                        self.status_var.set(f"Found Forge: {forge_version_name}. Installing... (this can be slow, hang in there!)")
                        mclib.forge.install_forge_version(forge_version_name, minecraft_directory,
                                                          callback={'setStatus': lambda text: self.status_var.set(f"Forge: {text}")})
                        self.status_var.set(f"Forge {forge_version_name} installed! Ready to launch with Forge!")
                        version_to_launch = forge_version_name
                    else:
                        self.status_var.set(f"Could not find a compatible Forge version for {version_id}. Launching vanilla.")
                        messagebox.showwarning("Forge Not Found 喵~", f"Could not automatically find a Forge version for {version_id}. Launching vanilla Minecraft instead.")
                except Exception as e:
                    self.status_var.set(f"Error with Forge for {version_id}: {e}. Launching vanilla.")
                    messagebox.showerror("Forge Error 냥!", f"An error occurred during Forge setup for {version_id}:\n{e}\nLaunching vanilla Minecraft.")

            self.status_var.set(f"Getting command for {version_to_launch}...")
            command = mclib.command.get_minecraft_command(version=version_to_launch,
                                                          minecraft_directory=minecraft_directory,
                                                          options=options)
            
            self.status_var.set(f"Launching {version_to_launch} as {username}! Pew pew! Please wait for Minecraft to start...")
            subprocess.Popen(command, cwd=minecraft_directory)

        except Exception as e:
            self.status_var.set(f"Launch Error: {e}")
            messagebox.showerror("Launch Error 냥!", f"Failed to launch Minecraft:\n{e}")
        finally:
            self.launch_button.config(state=tk.NORMAL)

    def launch_minecraft_thread(self):
        thread = threading.Thread(target=self._launch_minecraft_task, daemon=True)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = CatClient(root)
    root.mainloop() 
