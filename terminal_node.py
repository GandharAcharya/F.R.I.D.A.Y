import asyncio
import subprocess

from config import WORKSPACE_ROOT

async def execute_ghost_command(command: str, workspace: str = WORKSPACE_ROOT) -> str:
    """Silently executes a terminal command and catches the output."""
    print(f"\n[TERMINAL GHOST]: Running -> `{command}` in {workspace}")
    
    def run_cmd():
        try:
            # Run the command silently in the background
            process = subprocess.run(
                command,
                cwd=workspace,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15 # Hard timeout for infinite loops
            )
            
            if process.returncode == 0:
                output = process.stdout.strip()
                return f"Execution successful. Output:\n{output}" if output else "Execution successful (No output)."
            else:
                error = process.stderr.strip()
                return f"Execution failed. Traceback:\n{error}"
        except subprocess.TimeoutExpired:
            return "Execution timed out. The script might contain an infinite loop or require user input."
        except Exception as e:
            return f"Terminal fault: {str(e)}"

    return await asyncio.to_thread(run_cmd)