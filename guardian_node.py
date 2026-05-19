import os
import ast
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GuardianHandler(FileSystemEventHandler):
    """The silent watcher that stalks your code edits."""
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            self.lint_code(event.src_path)

    def lint_code(self, filepath):
        """Instantly checks for fatal Python crashes the second you save the file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            # Compile it in memory to check for syntax errors
            ast.parse(source)
            # If it passes, stay silent.
        except SyntaxError as e:
            # If it fails, trigger an OS voice interrupt to warn the Director
            filename = os.path.basename(filepath)
            warning = f"Director, Guardian Swarm anomaly detected. You just created a fatal syntax error in {filename} on line {e.lineno}. The system will crash if you run it."
            print(f"\n[GUARDIAN ALERT]: {warning}")
            import subprocess
            subprocess.Popen(['powershell', '-Command', f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{warning}")'])

def deploy_guardian_swarm(workspace_path: str="E:\\F.R.I.D.A.Y\\Workspace"):
    """Boots the watcher thread."""
    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path)
        
    event_handler = GuardianHandler()
    observer = Observer()
    observer.schedule(event_handler, path=workspace_path, recursive=True)
    observer.start()
    print(f"[GUARDIAN NODE]: Proactive anomaly detection online for {workspace_path}")