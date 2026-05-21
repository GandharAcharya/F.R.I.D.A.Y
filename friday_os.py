import customtkinter as ctk
import subprocess
import sys
import threading
import time
import os
import requests
import pygetwindow as gw
import psutil
import asyncio
import webbrowser
from concurrent.futures import ThreadPoolExecutor
# Force the system to allow up to 32 parallel threads instead of the default 4
asyncio.get_event_loop().set_default_executor(ThreadPoolExecutor(max_workers=32))

def boot_react_hud():
    """Silently boots the React OS and opens the browser."""
    print("[IGNITION]: Spinning up React Visual OS in the background...")
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "friday-os")
    
    # Run the Vite server invisibly
    subprocess.Popen(
        "npm run dev", 
        cwd=ui_path, 
        shell=True, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    
    # Give Vite 3 seconds to boot, then pop the browser
    time.sleep(3)
    print("[IGNITION]: HUD Online. Opening neural interface...")
    webbrowser.open("http://localhost:5173")
    
    # --- THE AUDIO HOTWIRE ---
    print("[IGNITION]: Booting LiveKit Voice Bridge...")
    comm_link_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comm_link.html")
    formatted_path = comm_link_path.replace('\\', '/')
    webbrowser.open(f"file:///{formatted_path}")
    # -------------------------

# Set the brutalist aesthetic you requested
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class FridayHUD(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- WINDOW SETUP ---
        self.title("F.R.I.D.A.Y. Mark IV - Master Control")
        self.geometry("900x600")
        self.configure(fg_color="#0a0a0a") # Deep brutalist black
        
        # --- PROCESS TRACKERS ---
        self.brain_process = None
        self.ui_process = None
        self.is_online = False

        self.build_ui()

    def build_ui(self):
        """Constructs the visual interface."""
        # 1. The Header
        self.header = ctk.CTkLabel(self, text="F.R.I.D.A.Y. NUCLEUS", font=("Courier New", 28, "bold"), text_color="#00ffff")
        self.header.pack(pady=(30, 10))

        # 2. System Status Matrix
        self.status_frame = ctk.CTkFrame(self, fg_color="#111111", border_color="#333333", border_width=1)
        self.status_frame.pack(pady=20, padx=40, fill="x")

        self.brain_status = ctk.CTkLabel(self.status_frame, text="Cognitive Core: OFFLINE", font=("Courier New", 14), text_color="#ff4444")
        self.brain_status.pack(pady=5, anchor="w", padx=20)

        self.comms_status = ctk.CTkLabel(self.status_frame, text="Neural Bridge: OFFLINE", font=("Courier New", 14), text_color="#ff4444")
        self.comms_status.pack(pady=5, anchor="w", padx=20)

        self.context_status = ctk.CTkLabel(self.status_frame, text="Active Context: NONE", font=("Courier New", 12), text_color="#aaaaaa")
        self.context_status.pack(pady=5, anchor="w", padx=20)

        # --- THE SWARM TELEMETRY MATRIX ---
        self.swarm_frame = ctk.CTkFrame(self, fg_color="#0a0a0a", border_color="#005555", border_width=1)
        self.swarm_frame.pack(pady=10, padx=40, fill="x")
        
        self.swarm_title = ctk.CTkLabel(self.swarm_frame, text="SWARM NODE TELEMETRY", font=("Courier New", 14, "bold"), text_color="#55aaaa")
        self.swarm_title.pack(pady=(10, 5))

        # Node Status Indicators
        self.node_architect = ctk.CTkLabel(self.swarm_frame, text="[ARCHITECT]: OFFLINE", font=("Courier New", 12), text_color="#555555")
        self.node_architect.pack(anchor="w", padx=20)
        
        self.node_intel = ctk.CTkLabel(self.swarm_frame, text="[INTEL]: OFFLINE", font=("Courier New", 12), text_color="#555555")
        self.node_intel.pack(anchor="w", padx=20)
        
        self.node_sentinel = ctk.CTkLabel(self.swarm_frame, text="[SENTINEL]: OFFLINE", font=("Courier New", 12), text_color="#555555")
        self.node_sentinel.pack(anchor="w", padx=20, pady=(0, 10))

        # 3. Terminal Output Window (For reading her physical actions)
        self.terminal_label = ctk.CTkLabel(self, text="SYSTEM LOGS", font=("Courier New", 12, "bold"), text_color="#555555")
        self.terminal_label.pack(anchor="w", padx=40)
        
        self.terminal = ctk.CTkTextbox(self, height=200, fg_color="#050505", text_color="#00dd00", font=("Consolas", 12))
        self.terminal.pack(pady=5, padx=40, fill="both", expand=True)
        self.terminal.insert("0.0", "Awaiting ignition sequence...\n")
        self.terminal.configure(state="disabled")

        # 4. The Ignition Switch
        self.boot_btn = ctk.CTkButton(self, text="IGNITE SYSTEMS", font=("Courier New", 16, "bold"), 
                                      fg_color="#222222", hover_color="#005555", border_color="#00ffff", border_width=1,
                                      command=self.toggle_ignition)
        self.boot_btn.pack(pady=30)

    def poll_hive_mind(self):
        """Silently pings the local Hive Router for Swarm status updates."""
        if not self.is_online: return
        
        try:
            response = requests.get("http://127.0.0.1:8000/status", timeout=1)
            if response.status_code == 200:
                data = response.json()
                
                # Dynamic Color Logic: Gray = Offline, Cyan = Idle, Green = Active/Working
                def update_label(label, node_name, status):
                    color = "#00dd00" if status != "IDLE" else "#00ffff"
                    label.configure(text=f"[{node_name.upper()}]: {status}", text_color=color)

                update_label(self.node_architect, "ARCHITECT", data.get("Architect", "IDLE"))
                update_label(self.node_intel, "INTEL", data.get("Intel", "IDLE"))
                update_label(self.node_sentinel, "SENTINEL", data.get("Sentinel", "IDLE"))
        except:
            # If the router drops, default to gray offline text
            self.node_architect.configure(text="[ARCHITECT]: SIGNAL LOST", text_color="#555555")
            self.node_intel.configure(text="[INTEL]: SIGNAL LOST", text_color="#555555")
            self.node_sentinel.configure(text="[SENTINEL]: SIGNAL LOST", text_color="#555555")

        # Loop this check every 1000 milliseconds (1 second)
        self.after(1000, self.poll_hive_mind)

    def track_active_context(self):
        """The Leech: Silently tracks active UI, CPU, and Memory usage."""
        if not self.is_online: return
        
        try:
            # 1. Hardware Telemetry
            cpu_usage = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            ram_usage = ram.percent
            
            # 2. UI Context
            active_window = gw.getActiveWindow()
            title = active_window.title[:50] if active_window and active_window.title else "Desktop"
            
            status_text = f"Context: {title} | CPU: {cpu_usage}% | RAM: {ram_usage}%"
            self.context_status.configure(text=status_text)
            
            # 3. Write the state to her subconscious file
            state_data = f"ACTIVE WINDOW: {title}\nCPU USAGE: {cpu_usage}%\nRAM USAGE: {ram_usage}%\n"
            with open("E:\\F.R.I.D.A.Y\\system_vitals.txt", "w", encoding="utf-8") as f:
                f.write(state_data)
        except:
            pass
            
        self.after(3000, self.track_active_context) # Pulse every 3 seconds

    def log(self, message):
        """Pushes text to the UI terminal cleanly."""
        self.terminal.configure(state="normal")
        self.terminal.insert("end", f"> {message}\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def toggle_ignition(self):
        """The Master Switch."""
        if not self.is_online:
            self.boot_sequence()
        else:
            self.shutdown_sequence()

    def boot_sequence(self):
        """Fires up Opera GX and the Python Brain concurrently."""
        self.is_online = True
        self.boot_btn.configure(text="SHUTDOWN SYSTEMS", fg_color="#550000", hover_color="#ff0000", border_color="#ff4444")
        self.header.configure(text_color="#00ffff")
        
        self.log("Initiating Mark IV Boot Sequence...")
        
        # 1. Boot the Opera GX Bridge
        self.comms_status.configure(text="Neural Bridge: CONNECTING...", text_color="#aaaa00")
        self.ui_process = subprocess.Popen([sys.executable, "boot_ui.py"])
        self.log("Comm-link dispatched to Opera GX.")
        self.comms_status.configure(text="Neural Bridge: ONLINE", text_color="#00ffff")

        # 1.5 Boot the Hive Mind Router
        self.log("Igniting Hive Mind Router on Port 8000...")
        self.hive_process = subprocess.Popen([sys.executable, "hive_router.py"], creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Start the radar ping
        self.after(2000, self.poll_hive_mind) # Wait 2 seconds for server to spin up before pinging

        # 2. Boot the Cognitive Core (With Neural Log Piping)
        self.brain_status.configure(text="Cognitive Core: BOOTING...", text_color="#aaaa00")
        
        # We capture her stdout so we can print it to the UI
        self.brain_process = subprocess.Popen(
            [sys.executable, "cognitive_core.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW # Keeps it truly hidden
        )
        
        # THIS IS THE LINE THAT FIXES YOUR LINTER WARNING:
        threading.Thread(target=self.monitor_brain, daemon=True).start()
        
        self.log("Cognitive Core initialized. Streaming logs...")
        self.brain_status.configure(text="Cognitive Core: ONLINE", text_color="#00ffff")
        
        self.log("ALL SYSTEMS NOMINAL. Awaiting voice input.")
        self.after(3000, self.track_active_context)

    def monitor_brain(self):
        """Reads F.R.I.D.A.Y.'s terminal logs and pipes them to the UI matrix."""
        if not self.brain_process: return
        
        # Read the terminal output line by line as she thinks
        for line in iter(self.brain_process.stdout.readline, ''):
            if line:
                # Use .after() to safely push the text to the main UI thread
                self.after(0, self.log, line.strip())

    def shutdown_sequence(self):
        """Kills all background processes cleanly so you don't get zombie Python tasks."""
        self.is_online = False
        self.boot_btn.configure(text="IGNITE SYSTEMS", fg_color="#222222", hover_color="#005555", border_color="#00ffff")
        self.header.configure(text_color="#555555")

        self.log("Initiating system shutdown...")
        
        if hasattr(self, 'hive_process') and self.hive_process:
            self.hive_process.terminate()
            self.log("Hive Mind Router severed.")
            
        # Reset the UI labels to offline
        self.node_architect.configure(text="[ARCHITECT]: OFFLINE", text_color="#555555")
        self.node_intel.configure(text="[INTEL]: OFFLINE", text_color="#555555")
        self.node_sentinel.configure(text="[SENTINEL]: OFFLINE", text_color="#555555")
        
        if self.brain_process:
            self.brain_process.terminate()
            self.brain_status.configure(text="Cognitive Core: OFFLINE", text_color="#ff4444")
        
        if self.ui_process:
            self.ui_process.terminate()
            self.comms_status.configure(text="Neural Bridge: OFFLINE", text_color="#ff4444")

        self.log("System powered down.")

if __name__ == "__main__":
    # 1. Purge old React instances to prevent Port 8000 collisions
    os.system("taskkill /F /IM node.exe >nul 2>&1")
    
    # 2. Fire the UI Bootloader in a background thread
    ui_thread = threading.Thread(target=boot_react_hud, daemon=True)
    ui_thread.start()

    app = FridayHUD()
    app.mainloop()