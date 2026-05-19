import os
from dotenv import load_dotenv

load_dotenv()

# Automatically detects where F.R.I.D.A.Y. is installed, no matter the drive.
FRIDAY_ROOT = os.getenv("FRIDAY_ROOT", os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_ROOT = os.path.join(FRIDAY_ROOT, "Workspace")
MACROS_FILE = os.path.join(FRIDAY_ROOT, "macros.json")
VITALS_FILE = os.path.join(FRIDAY_ROOT, "system_vitals.txt")