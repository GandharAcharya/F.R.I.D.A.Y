import subprocess
import os
import mss
import pyautogui
import webbrowser
pyautogui.FAILSAFE = False


class SystemController:
    def __init__(self, root_dir=None):
        from config import FRIDAY_ROOT
        if root_dir is None:
            root_dir = FRIDAY_ROOT
        print("[SYSTEM] Initializing OS Control API (Safety Sandbox Active)...")
        self.root_dir = root_dir
        
        # SCOPED GOD-MODE: If F.R.I.D.A.Y. tries to run these, the API hard-blocks her.
        self.forbidden_commands = ["del", "rm", "rmdir", "rd", "format", "diskpart", "wipe", "shutdown", "remove-item", "reg delete", "bcdedit", "dd if="]

    def execute_terminal(self, command: str) -> str:
        """Executes a terminal command and returns the output or error."""
        print(f"[OS API] Attempting Execution: {command}")
        
        # The Security Check
        if any(bad_word in command.lower() for bad_word in self.forbidden_commands):
            return f"CRITICAL OVERRIDE: Command '{command}' violates safety protocols. Execution blocked."
            
        try:
            # We use shell=True for standard commands, but wrap it in a try/except to catch explosions
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=self.root_dir)
            if result.returncode == 0:
                return f"Success: {result.stdout}" if result.stdout else "Command executed silently with success."
            else:
                return f"Error: {result.stderr}"
        except Exception as e:
            return f"System Failure: {str(e)}"

    def create_file(self, filename: str, content: str) -> str:
        """Creates or overwrites a text/code file in the workspace."""
        file_path = os.path.join(self.root_dir, filename)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File '{filename}' successfully created."
        except Exception as e:
            return f"Failed to create file: {str(e)}"

    def read_file(self, filename: str) -> str:
        """Reads a file so F.R.I.D.A.Y. can analyze its contents."""
        file_path = os.path.join(self.root_dir, filename)
        if not os.path.exists(file_path):
            return f"File '{filename}' does not exist."
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Failed to read file: {str(e)}"

    def capture_screen(self, filename="friday_eye.png") -> str:
        """Takes a high-speed screenshot of the Director's primary monitor."""
        file_path = os.path.join(self.root_dir, filename)
        try:
            with mss.mss() as sct:
                # mon=1 usually targets the primary monitor. Change to mon=2 if you have dual monitors and want the other one.
                sct.shot(mon=1, output=file_path)
            return f"Screen captured successfully and saved to {filename}."
        except Exception as e:
            return f"Optical sensor failure: {str(e)}"

    def gui_type(self, text: str) -> str:
        """Physically types text on the Director's keyboard."""
        try:
            # We add a tiny interval so it looks human and doesn't crash apps
            pyautogui.write(text, interval=0.02)
            return f"Physically typed: {text}"
        except Exception as e:
            return f"Keyboard control failed: {str(e)}"

    def gui_hotkey(self, keys: str) -> str:
        """Presses a combination of keys (e.g., 'ctrl,c' or 'win,r')."""
        try:
            # Splits the comma-separated string into actual key presses
            key_list = [k.strip() for k in keys.split(',')]
            pyautogui.hotkey(*key_list)
            return f"Executed keyboard hotkey: {keys}"
        except Exception as e:
            return f"Hotkey execution failed: {str(e)}"

    def gui_click(self, x: int = None, y: int = None) -> str:
        """Clicks the mouse. If no coordinates are given, clicks the center of the screen."""
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y)
                return f"Mouse clicked at coordinates X:{x}, Y:{y}"
            else:
                # If she doesn't know where to click, default to center to gain window focus
                screen_width, screen_height = pyautogui.size()
                pyautogui.click(screen_width / 2, screen_height / 2)
                return "Mouse clicked at screen center."
        except Exception as e:
            return f"Mouse control failed: {str(e)}"

    def open_webpage(self, url: str) -> str:
        """Opens a URL directly in the default browser natively, avoiding GUI hotkey errors."""
        try:
            # Ensure URL is properly formatted
            if not url.startswith('http'):
                url = 'https://' + url
            webbrowser.open(url)
            return f"Successfully opened {url} in the native browser."
        except Exception as e:
            return f"Failed to open webpage natively: {str(e)}"

    def get_desktop_path(self) -> str:
        """Autonomously locates the true Windows Desktop path."""
        import os
        standard_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        onedrive_path = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop')
        
        # Return whichever one actually exists on your machine
        return onedrive_path if os.path.exists(onedrive_path) else standard_path

    def global_file_sonar(self, filename: str, drive: str = "E:\\") -> str:
        """Smart Sonar: Checks known workspaces instantly before falling back to a global brute-force scan."""
        import os, subprocess
        print(f"[OS RADAR]: Scanning for '{filename}'...")
        
        # 1. THE INSTANT WORKSPACE CHECK (Fixes the wrong folder and the 5-minute lag)
        from config import WORKSPACE_ROOT
        workspace_guess = os.path.join(WORKSPACE_ROOT, filename)
        if os.path.exists(workspace_guess):
            print("[OS RADAR]: Target found instantly in Workspace.")
            return f"Sonar found targets:\n{workspace_guess}"

        # 2. THE SLOW GLOBAL FALLBACK (Only triggers if it's truly lost)
        print("[OS RADAR]: Target not in workspace. Initiating deep drive scan...")
        try:
            ps_command = f"Get-ChildItem -Path {drive} -Filter '*{filename}*' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 5 -ExpandProperty FullName"
            result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, timeout=25)
            
            paths = result.stdout.strip()
            if paths:
                return f"Sonar found targets:\n{paths}"
            else:
                return f"Sonar returned empty. '{filename}' not found."
        except subprocess.TimeoutExpired:
            return "Sonar scan timed out. The directory is too massive."
        except Exception as e:
            return f"Sonar failure: {str(e)}"


    def terminate_application(self, app_name: str) -> str:
        """Native OS-level process termination. Bypasses GUI hotkeys entirely."""
        import os
        print(f"[OS KERNEL]: Terminating process -> {app_name}")
        try:
            # Map common spoken names to actual Windows executable names
            exe_map = {
                "file explorer": "explorer.exe",
                "opera": "opera.exe",
                "chrome": "chrome.exe",
                "vscode": "code.exe",
                "tradingview": "TradingView.exe"
            }
            
            target_exe = exe_map.get(app_name.lower(), f"{app_name}.exe")
            
            # Using Windows taskkill to safely terminate the process
            result = os.system(f"taskkill /f /im {target_exe}")
            if result == 0:
                return f"Successfully terminated {target_exe} at the OS level."
            else:
                return f"Could not find or terminate {target_exe}. It may already be closed."
        except Exception as e:
            return f"Kernel termination failed: {str(e)}"

    def open_folder_in_explorer(self, target_path: str) -> str:
        """Natively forces Windows to open File Explorer at the exact path."""
        import os, subprocess
        print(f"[OS KERNEL]: Launching Explorer -> {target_path}")
        try:
            if os.path.exists(target_path):
                # The native Windows command to open a folder
                subprocess.Popen(f'explorer "{target_path}"')
                return f"Successfully opened {target_path} in File Explorer."
            else:
                return f"Path does not exist on this machine: {target_path}"
        except Exception as e:
            return f"Explorer launch failed: {str(e)}"

    def throw_window_to_monitor(self, app_name: str, target_screen: int = 1) -> str:
        """Actively hunts for an app to open, then moves it to the target monitor."""
        import pygetwindow as gw
        from screeninfo import get_monitors
        import time
        
        print(f"[OS SPATIAL]: Hunting for '{app_name}' to move to Monitor {target_screen + 1}...")
        try:
            monitors = get_monitors()
            if len(monitors) <= target_screen:
                return f"Spatial error: You only have {len(monitors)} monitor(s) detected."
            
            target_display = monitors[target_screen]
            
            # THE HUNTER-SEEKER LOOP: Wait up to 10 seconds for the app to actually boot
            target_window = None
            for _ in range(20): # 20 attempts, 0.5s apart
                windows = [w for w in gw.getAllWindows() if w.title and app_name.lower() in w.title.lower()]
                if windows:
                    target_window = windows[0]
                    break
                time.sleep(0.5)
                
            if not target_window:
                return f"Tell the Director: '{app_name}' took too long to open, or it launched in the background. I couldn't move it."
            
            # Un-snap, move, and re-maximize
            if target_window.isMaximized:
                target_window.restore()
            target_window.moveTo(target_display.x + 50, target_display.y + 50)
            target_window.maximize()
            
            return f"Successfully threw {app_name} to the secondary monitor."
        except Exception as e:
            return f"Spatial move failed: {str(e)}"


# ==========================================
# ISOLATED TESTING BLOCK
# ==========================================
if __name__ == "__main__":
    # Test the sandbox without booting the brain
    hands = SystemController()
    
    print("\n--- Testing File Creation ---")
    print(hands.create_file("test_protocol.txt", "This is a test of the Mark IV API."))
    
    print("\n--- Testing File Reading ---")
    print(hands.read_file("test_protocol.txt"))
    
    print("\n--- Testing Safe Terminal ---")
    print(hands.execute_terminal("echo F.R.I.D.A.Y. Hands Online"))
    
    print("\n--- Testing Security Override ---")
    print(hands.execute_terminal("del test_protocol.txt"))