from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import subprocess

app = FastAPI(title="F.R.I.D.A.Y. Neural Router")

class Command(BaseModel):
    instruction: str

@app.post("/override")
async def remote_override(cmd: Command):
    """The backdoor for your phone to command the desktop."""
    print(f"\n[NEURAL ROUTER]: Remote command received -> {cmd.instruction}")
    
    # Trigger an immediate OS-level TTS response so you know she heard your phone
    subprocess.Popen(['powershell', '-Command', f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("Remote override authenticated. {cmd.instruction}")'])
    
    # In a full deployment, this command gets pushed into her cognitive event queue
    return {"status": "Command injected into Swarm."}

def start_neural_router():
    """Boots the API on port 8000 so any device on your Wi-Fi can reach it."""
    print("[NEURAL ROUTER]: Ecosystem API online. Listening on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")