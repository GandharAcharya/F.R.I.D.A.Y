import tkinter as tk
import threading
import psutil

class FridayHUD:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("F.R.I.D.A.Y. HUD")
        
        # Make it borderless, transparent, and always on top
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.8) # 80% opacity
        self.root.config(bg='black')
        
        # Position in the top-right corner of the screen
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"300x150+{screen_width - 320}+20")
        
        # Make the window click-through (Windows specific)
        # This allows you to click things underneath the HUD
        self.root.wm_attributes("-transparentcolor", "black")

        # UI Elements (Iron Man aesthetic)
        self.status_label = tk.Label(self.root, text="MARK VI SYSTEMS ONLINE", font=("Courier", 12, "bold"), fg="#00ffcc", bg="black")
        self.status_label.pack(anchor="w", padx=10, pady=5)
        
        self.cpu_label = tk.Label(self.root, text="CPU: --%", font=("Courier", 10), fg="#ff3366", bg="black")
        self.cpu_label.pack(anchor="w", padx=10)
        
        self.swarm_label = tk.Label(self.root, text="SWARM THREADS: IDLE", font=("Courier", 10), fg="#00ffcc", bg="black")
        self.swarm_label.pack(anchor="w", padx=10)

        self.update_vitals()

    def update_vitals(self):
        """Pulls live telemetry to animate the HUD."""
        cpu = psutil.cpu_percent()
        self.cpu_label.config(text=f"SYS LOAD: {cpu}%")
        
        # You can expand this later to read actual Swarm status from a shared state file
        if cpu > 60:
            self.swarm_label.config(text="SWARM THREADS: HEAVY COMPUTE", fg="#ffcc00")
        else:
            self.swarm_label.config(text="SWARM THREADS: MONITORING", fg="#00ffcc")
            
        self.root.after(1000, self.update_vitals)

    def run(self):
        self.root.mainloop()

def boot_hud():
    hud = FridayHUD()
    hud.run()

if __name__ == "__main__":
    boot_hud()