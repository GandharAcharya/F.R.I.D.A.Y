import os
import subprocess
from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants

load_dotenv()

# Generate the Director's secure access token
token = AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET")) \
    .with_identity("Director") \
    .with_name("Gandhar") \
    .with_grants(VideoGrants(room_join=True, room="friday-terminal")) \
    .to_jwt()

ws_url = os.getenv("LIVEKIT_URL")
html_path = os.path.abspath("comm_link.html")

# Construct the secure local URL
secure_url = f"file:///{html_path}?url={ws_url}&token={token}"

# Dynamically locate Opera GX on your Windows machine
opera_path = os.path.join(os.environ['USERPROFILE'], r"AppData\Local\Programs\Opera GX\opera.exe")

print("[SYSTEM]: Keys injected. Booting Opera GX Comm-Link...")

try:
    # Bypass the OS and launch Opera GX directly with the secure URL
    subprocess.Popen([opera_path, secure_url])
except FileNotFoundError:
    print(f"[ERROR]: Could not find Opera GX at {opera_path}")