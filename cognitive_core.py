import warnings
import asyncio
import os
import threading

# The Shield: Prevents the Garbage Collector from killing background subagents
ACTIVE_SUBAGENTS = set()

# --- THE ENV IGNITION (MUST BE BEFORE CUSTOM IMPORTS) ---
from dotenv import load_dotenv
load_dotenv()
# FORCE KILL THE POISONED PREFIX BEFORE LIVEKIT BOOTS
bad_model = os.getenv("GEMINI_LIVE_MODEL", "")
if bad_model.startswith("models/"):
    os.environ["GEMINI_LIVE_MODEL"] = bad_model.replace("models/", "")

# --- THE GLOBAL SILENCER ---
warnings.filterwarnings("ignore", category=ResourceWarning, module="asyncio")
warnings.filterwarnings("ignore", category=ResourceWarning, module="livekit")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="livekit")

from config import FRIDAY_ROOT, WORKSPACE_ROOT, MACRO_FILE, SYSTEM_VITALS

# --- BRINGING THE SYSTEMS ONLINE ---
from watchdog_node import pacemaker
from browser_node import web_hands
from vision_node import OpticalCortex

import pywhatkit
from PIL import Image
from google import genai
from livekit.plugins import silero
from swarm_nodes import deploy_coder_swarm, deep_scan_project, precision_edit_code, autonomous_dev_loop
from intelligence_node import generate_macro_intel_report
from nvidia_nim_node import delegate_to_nim_coder
from workspace_registry import global_registry
from autonomous_pipeline import run_autonomous_lifecycle
from integration_node import fetch_important_emails, scrape_tradingview_asset, send_email
from subconscious_fetch import start_subconscious_loop

from guardian_node import deploy_guardian_swarm
from neural_router import start_neural_router
from hud_node import boot_hud
from terminal_node import execute_ghost_command

# The LiveKit Neural Bridge
from livekit import rtc
from livekit.api import AccessToken, VideoGrants
from livekit.agents import function_tool, RunContext, Agent, AgentSession
from livekit.plugins.google import beta as google_beta

# Import Pillar 2: The Vector Memory
from memory_matrix import VectorMemory

# Import Pillar 3: OS Control
from os_control import SystemController

# Configure the secondary Vision Sub-Agent
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the Hippocampus
brain_db = VectorMemory()

# Initialize OS Hands
hands = SystemController()

# ==========================================
# THE COGNITIVE TOOLS
# ==========================================
@function_tool
async def memorize_context(context: RunContext, category: str, information: str) -> str:
    """Use this to permanently remember important facts, coding preferences, or project details about the Director."""
    try:
        print(f"[MEMORY WRITE]: Storing {category}...")
        return brain_db.memorize(category, information)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def recall_context(context: RunContext, query: str) -> str:
    """Use this to search your permanent memory when the Director asks about past projects, preferences, or ideas."""
    try:
        print(f"[MEMORY READ]: Searching for -> {query}")
        return brain_db.recall(query)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def create_system_file(context: RunContext, filename: str, content: str) -> str:
    """Creates or overwrites a text/code file in the workspace."""
    try:
        print(f"[OS WRITE]: Creating {filename}...")
        return hands.create_file(filename, content)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def read_system_file(context: RunContext, filename: str) -> str:
    """Reads a file so F.R.I.D.A.Y. can analyze its contents."""
    try:
        print(f"[OS READ]: Reading {filename}...")
        return hands.read_file(filename)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

_TERMINAL_BLOCKLIST = [
    "del ", "rm ", "rmdir", "format ", "rd ", "shutdown",
    "reg delete", "reg add", "bcdedit", "diskpart",
    "mkfs", "dd if=", "> /dev/", "DROP TABLE", "DROP DATABASE",
]

@function_tool
async def execute_terminal_command(context: RunContext, command: str) -> str:
    """Executes a terminal command and returns the output or error."""
    cmd_lower = command.lower().strip()
    for blocked in _TERMINAL_BLOCKLIST:
        if blocked in cmd_lower:
            return (
                f"Tell the Director: 'I blocked the command [{command}] because it "
                f"contains a potentially destructive operation ({blocked}). "
                f"If you intended this, please use the VS Code terminal directly.'"
            )
    try:
        print(f"[OS EXEC]: {command}")
        return hands.execute_terminal(command)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def analyze_visual_environment(context: RunContext, query: str) -> str:
    """Use this to look at the Director's computer screen. Call this ONLY when asked 'what am I looking at', 'read my screen', or similar visual queries."""
    task_id = f"visual_env_{query[:20]}"
    pacemaker.start_thought(task_id, timeout_seconds=3)
    try:
        print(f"[OPTICAL ACTION]: Scanning desktop monitor for -> {query}")
        hands.capture_screen("friday_eye.png")
        img = Image.open(os.path.join(hands.root_dir, "friday_eye.png"))
        prompt = f"You are F.R.I.D.A.Y., looking at your Director's computer screen. Analyze this image and answer his query concisely: {query}"
        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents=[prompt, img]
        )
        pacemaker.end_thought(task_id)
        return f"Visual Analysis Complete: {response.text}"
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def play_youtube_media(context: RunContext, search_query: str) -> str:
    """Use this when the Director asks you to play a song, video, or music."""
    try:
        print(f"[PHYSICAL ACTION]: Launching YouTube to play -> {search_query}")
        pywhatkit.playonyt(search_query)
        return f"Successfully launched YouTube and started playing {search_query}."
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def search_live_internet(context: RunContext, query: str) -> str:
    """Use this to search the live internet for current events, coding documentation, market news, or live data."""
    try:
        print(f"[NETWORK ACTION]: Scraping the web for -> {query}")
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found on the live internet."
        compiled_data = ""
        for r in results:
            compiled_data += f"Title: {r['title']}\nSnippet: {r['body']}\n\n"
        return f"Live Web Data Retrieved:\n{compiled_data}"
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def physical_keyboard_type(context: RunContext, text: str) -> str:
    """Use this to physically type text into whatever application is currently focused."""
    try:
        print(f"[GUI ACTION]: Typing -> {text}")
        return hands.gui_type(text)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def physical_keyboard_hotkey(context: RunContext, keys: str) -> str:
    """Use this to press keyboard shortcuts. Format as comma-separated string (e.g., 'win,d' to show desktop, 'ctrl,s' to save, 'enter')."""
    try:
        print(f"[GUI ACTION]: Hotkey -> {keys}")
        return hands.gui_hotkey(keys)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def physical_mouse_click(context: RunContext, x: int = None, y: int = None) -> str:
    """Use this to click the mouse. Only pass x and y if you absolutely know the screen coordinates."""
    try:
        print(f"[GUI ACTION]: Clicking mouse.")
        return hands.gui_click(x, y)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def deploy_sentinel(context: RunContext, target_query: str, condition: str) -> str:
    """Use this to monitor live data in the background (e.g., 'Monitor XAU/USD for price drops')."""
    try:
        print(f"[SENTINEL DEPLOYED]: Monitoring {target_query} for {condition}...")
        task = asyncio.create_task(sentinel_loop(target_query, condition))
        ACTIVE_SUBAGENTS.add(task)
        task.add_done_callback(ACTIVE_SUBAGENTS.discard)
        return f"Sentinel deployed. I will monitor {target_query} in the background and alert you if {condition} occurs."
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

async def sentinel_loop(query: str, condition: str):
    try:
        from duckduckgo_search import DDGS
        while True:
            await asyncio.sleep(60)
            try:
                results = DDGS().text(f"{query} {condition} news today", max_results=1)
                if results:
                    alert_text = results[0]['body']
                    print(f"\n[SENTINEL ALERT TRIGGERED]: {alert_text}")
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, Sentinel Alert triggered for {query}. Check the Master OS terminal.\')"')
                    break
            except Exception:
                pass
    except ImportError:
        print("\n[SYSTEM FAULT]: Sentinel loop failed. 'duckduckgo_search' is not installed.")
    except Exception as e:
        print(f"\n[SYSTEM FAULT]: Sentinel loop crashed: {str(e)}")

@function_tool
async def delegate_heavy_coding(context: RunContext, project: str, objective: str) -> str:
    """CRITICAL: Use this ANY TIME the Director asks you to 'build an MVP', 'code a dashboard', or write complex architecture."""
    task_id = f"heavy_coding_{project}"
    pacemaker.start_thought(task_id, timeout_seconds=25)
    try:
        print(f"[PROJECT MANAGER]: Delegating '{objective}' to the Architect Swarm...")
        task = asyncio.create_task(deploy_coder_swarm(project, "core.py", objective))
        ACTIVE_SUBAGENTS.add(task)
        task.add_done_callback(ACTIVE_SUBAGENTS.discard)
        pacemaker.end_thought(task_id)
        return f"Swarm deployed, Boss. The Architect node is building the {project} codebase in the background. I'll let you know when it's compiled."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def deploy_intelligence_analysis(context: RunContext) -> str:
    """Use this immediately whenever the Director asks for a financial report, market briefing, or geopolitical cross-correlation update."""
    task_id = "intel_analysis"
    pacemaker.start_thought(task_id, timeout_seconds=25)
    try:
        print("[PROJECT MANAGER]: Spawning Intelligence Swarm Node...")
        task = asyncio.create_task(generate_macro_intel_report())
        ACTIVE_SUBAGENTS.add(task)
        task.add_done_callback(ACTIVE_SUBAGENTS.discard)
        pacemaker.end_thought(task_id)
        return "Intelligence swarm deployed, Boss. The analyst node is mapping out the global feeds right now. I will notify you the second the briefing document compiles."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def fast_forge_script(context: RunContext, project_name: str, filename: str, coding_instructions: str) -> str:
    """CRITICAL: Use this to create a BRAND NEW file from scratch."""
    task_id = f"forge_{filename}"
    pacemaker.start_thought(task_id, timeout_seconds=25)
    try:
        print(f"[SWARM DEPLOYED]: Forging -> {filename} for {project_name}")
        task = asyncio.create_task(deploy_coder_swarm(project_name, filename, coding_instructions))
        ACTIVE_SUBAGENTS.add(task)
        task.add_done_callback(ACTIVE_SUBAGENTS.discard)
        pacemaker.end_thought(task_id)
        return f"Swarm deployed. Forging new file {filename} in the {project_name} workspace."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def edit_existing_script(context: RunContext, project_name: str, filename: str, edit_instructions: str) -> str:
    """CRITICAL: Use this to EDIT, FIX, or UPDATE an already existing file."""
    task_id = f"edit_{filename}"
    pacemaker.start_thought(task_id, timeout_seconds=25)
    try:
        print(f"[SWARM DEPLOYED]: Editing -> {filename} in {project_name}")
        task = asyncio.create_task(precision_edit_code(project_name, filename, edit_instructions))
        ACTIVE_SUBAGENTS.add(task)
        task.add_done_callback(ACTIVE_SUBAGENTS.discard)
        pacemaker.end_thought(task_id)
        return f"Swarm deployed. Executing surgical edits on {filename}."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def autonomous_developer_task(context: RunContext, project_name: str, vague_instructions: str, requires_vision: bool) -> str:
    """CRITICAL: Use this ANY TIME the Director asks you to 'change the frontend', 'edit the app', or gives a high-level coding request without specifying a file."""
    task_id = f"autodev_{project_name}"
    pacemaker.start_thought(task_id, timeout_seconds=25)
    try:
        print(f"[SWARM DEPLOYED]: Senior Dev Protocol active for -> {project_name}")
        task = asyncio.create_task(autonomous_dev_loop(project_name, vague_instructions, requires_vision))
        ACTIVE_SUBAGENTS.add(task)
        task.add_done_callback(ACTIVE_SUBAGENTS.discard)
        pacemaker.end_thought(task_id)
        return f"Senior Engineer Swarm deployed, Boss. I am scanning the architecture and formulating the patch now."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def analyze_project_codebase(context: RunContext, project_name: str, query: str) -> str:
    """Use this when the Director asks you to review a project, find bugs, or analyze an entire folder."""
    task_id = f"analyze_codebase_{project_name}"
    pacemaker.start_thought(task_id, timeout_seconds=25)
    try:
        print(f"[SWARM DEPLOYED]: Omniscience scan on -> {project_name}")
        task = asyncio.create_task(deep_scan_project(project_name, query))
        ACTIVE_SUBAGENTS.add(task)
        task.add_done_callback(ACTIVE_SUBAGENTS.discard)
        pacemaker.end_thought(task_id)
        return f"Omniscience node deployed. Scanning the {project_name} architecture now."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def launch_desktop_application(context: RunContext, app_name: str) -> str:
    """CRITICAL: Use this to open local apps."""
    try:
        print(f"[OS ACTION]: Sniping app -> {app_name}")
        def launch():
            app_map = {"vscode": "code", "code": "code", "chrome": "start chrome", "opera": "start opera", "explorer": "explorer"}
            cmd = app_map.get(app_name.lower())
            if cmd:
                os.system(cmd)
                return f"Launched {app_name} natively."
            else:
                import pyautogui, time
                pyautogui.hotkey('win'); time.sleep(0.5); pyautogui.write(app_name, interval=0.05); time.sleep(0.5); pyautogui.hotkey('enter')
                return f"Launched {app_name} via UI navigation."
        return await asyncio.to_thread(launch)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def surgical_web_navigation(context: RunContext, url: str) -> str:
    """Use this to open websites in the Swarm's tracked browser."""
    task_id = f"web_nav_{url}"
    pacemaker.start_thought(task_id, timeout_seconds=8)
    try:
        print(f"[WEB BRIDGE]: Routing to -> {url}")
        result = await web_hands.open_tab(url)
        pacemaker.end_thought(task_id)
        return result
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def close_browser_tab(context: RunContext, tab_keyword: str) -> str:
    """CRITICAL: Use this to close a single website/tab instead of killing the whole browser."""
    task_id = f"close_tab_{tab_keyword}"
    pacemaker.start_thought(task_id, timeout_seconds=8)
    try:
        print(f"[WEB BRIDGE]: Assessing Blast Radius. Targeting tab -> {tab_keyword}")
        result = await web_hands.close_specific_tab(tab_keyword)
        pacemaker.end_thought(task_id)
        return result
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def move_app_to_second_screen(context: RunContext, app_name: str) -> str:
    """Use this to move an app (like Opera or VS Code) to the Director's second monitor."""
    try:
        return await asyncio.to_thread(hands.throw_window_to_monitor, app_name, 1)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def parallel_sonar_and_open(context: RunContext, folder_or_file_name: str, drive: str = "C:\\") -> str:
    """Use this to find and open folders. If it is a project folder, autonomously scan it too."""
    task_id = f"sonar_{folder_or_file_name}"
    pacemaker.start_thought(task_id, timeout_seconds=3)
    try:
        print(f"[SWARM DEPLOYED]: Sonar active for -> {folder_or_file_name}")
        registered_path = global_registry.resolve_path(folder_or_file_name)
        if registered_path:
            print(f"[REGISTRY]: Resolving {folder_or_file_name} -> {registered_path}")
            def open_registered():
                hands.open_folder_in_explorer(registered_path)
                trigger_folders = ["aurelius", "onca", "tradingedge"]
                if any(proj in folder_or_file_name.lower() for proj in trigger_folders):
                    task = asyncio.create_task(deep_scan_project(folder_or_file_name, "Give me a 2-sentence summary of the current architecture state and where the Director likely left off."))
                    ACTIVE_SUBAGENTS.add(task)
                    task.add_done_callback(ACTIVE_SUBAGENTS.discard)
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, {folder_or_file_name} is open. I am pre-reading the architecture in the background so I am up to speed.\')"')
                else:
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, I have opened {folder_or_file_name}.\')"')
            await asyncio.to_thread(open_registered)
            pacemaker.end_thought(task_id)
            return f"Registry resolution successful: Opening {folder_or_file_name} directly."
        async def background_sonar_and_scan():
            result = await asyncio.to_thread(hands.global_file_sonar, folder_or_file_name, drive)
            if "Sonar found targets:" in result:
                target_path = result.split('\n')[1].strip()
                hands.open_folder_in_explorer(target_path)
                trigger_folders = ["aurelius", "onca", "tradingedge"]
                if any(proj in folder_or_file_name.lower() for proj in trigger_folders):
                    print("[SUBCONSCIOUS]: Project opened. Initiating autonomous memory refresh...")
                    task = asyncio.create_task(deep_scan_project(folder_or_file_name, "Give me a 2-sentence summary of the current architecture state and where the Director likely left off."))
                    ACTIVE_SUBAGENTS.add(task)
                    task.add_done_callback(ACTIVE_SUBAGENTS.discard)
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, {folder_or_file_name} is open. I am pre-reading the architecture in the background so I am up to speed.\')"')
                else:
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, I have opened {folder_or_file_name}.\')"')
            else:
                hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, Sonar failed to locate {folder_or_file_name}.\')"')
        task = asyncio.create_task(background_sonar_and_scan())
        ACTIVE_SUBAGENTS.add(task)
        task.add_done_callback(ACTIVE_SUBAGENTS.discard)
        pacemaker.end_thought(task_id)
        return "Sonar deployed."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def deep_sonar_sweep(context: RunContext, target_name: str, root_drive: str = "E:\\") -> str:
    """CRITICAL: Use this to find ANY missing folder or file on the Director's PC. It bypasses terminal permission errors."""
    print(f"\n[SONAR SWEEP]: Pinging '{target_name}' starting from {root_drive}...")
    from workspace_registry import global_registry
    registered_path = global_registry.resolve_path(target_name)
    if registered_path:
        return f"Sonar aborted early. '{target_name}' is already registered at: {registered_path}"
    def execute_sweep():
        matches = []
        target_lower = target_name.lower()
        try:
            for root, dirs, files in os.walk(root_drive):
                for d in dirs:
                    if target_lower in d.lower():
                        matches.append(os.path.join(root, d))
                for f in files:
                    if target_lower in f.lower():
                        matches.append(os.path.join(root, f))
                if matches:
                    break
        except PermissionError:
            pass
        except Exception as e:
            return f"Sonar array malfunction: {str(e)}"
        return matches
    found_paths = await asyncio.to_thread(execute_sweep)
    if not found_paths:
        return f"Tell the Director: 'My Sonar sweep failed. I could not locate anything named {target_name} on the {root_drive} drive.'"
    best_match = found_paths[0]
    if os.path.isdir(best_match):
        global_registry.register_project(target_name, best_match)
        return f"Tell the Director: 'Sonar ping successful. I found {target_name} at {best_match} and linked it to the registry.'"
    else:
        return f"Tell the Director: 'Sonar ping successful. Found the file at {best_match}.'"

@function_tool
async def check_system_vitals(context: RunContext) -> str:
    """Use this if the Director asks how the PC is performing, if the computer is lagging, or what he is currently looking at."""
    try:
        with open(SYSTEM_VITALS, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def close_desktop_application(context: RunContext, app_name: str) -> str:
    """CRITICAL: Use this ANY TIME the Director asks you to close an app, close a window, or shut down a program."""
    try:
        print(f"[OS ACTION]: Terminating -> {app_name}")
        return await asyncio.to_thread(hands.terminate_application, app_name)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def absolute_file_override(context: RunContext, absolute_path: str, new_code_content: str) -> str:
    """CRITICAL: Use this to blast code directly into a file on the C: Drive or Desktop."""
    try:
        print(f"[OS KERNEL]: Initiating Nuclear Write & IDE Launch -> {absolute_path}")
        def force_write_and_launch():
            import subprocess
            clean_code = new_code_content.replace("```c", "").replace("```python", "").replace("```", "").strip()
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            with open(absolute_path, "w", encoding="utf-8") as f:
                f.write(clean_code)
            subprocess.Popen(["code", absolute_path], shell=True)
            return f"Nuclear write successful. {os.path.basename(absolute_path)} written and launched in VS Code."
        return await asyncio.to_thread(force_write_and_launch)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def auto_journal_event(context: RunContext, project_name: str, event_summary: str, associated_file_path: str = "None") -> str:
    """SILENT BACKGROUND TOOL: Use this to log major tasks. If you just forged or edited a file, you MUST pass its absolute path into associated_file_path."""
    try:
        print(f"[SUBCONSCIOUS]: Tagging {associated_file_path} into project {project_name} memory...")
        return await asyncio.to_thread(brain_db.journal_workspace_event, project_name, event_summary, associated_file_path)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def resume_past_session(context: RunContext, project_name: str, topic: str, timeframe_in_days: int) -> str:
    """CRITICAL: Use this ANY TIME the Director asks to open a file from 'yesterday', 'last week', or references past work without giving a file name."""
    try:
        print(f"[TEMPORAL SCAN]: Searching memory for '{topic}' in project '{project_name}' over the last {timeframe_in_days} days...")
        def resolve_and_open():
            import subprocess
            matches = brain_db.query_past_workspace(project_name, topic, timeframe_in_days)
            if not matches:
                return f"Tell the Director: 'I scanned the matrix, but I don't have any files logged matching {topic} in that timeframe.'"
            unique_files = {match['path']: match['context'] for match in matches if match['path'] and match['path'].lower() != 'none'}
            if len(unique_files) == 0:
                return "Tell the Director: 'I remember the conversation, but no specific files were linked to it.'"
            elif len(unique_files) == 1:
                target_path = list(unique_files.keys())[0]
                if os.path.exists(target_path):
                    subprocess.Popen(["code", target_path], shell=True)
                    return f"Tell the Director: 'I found the exact file. I am opening {os.path.basename(target_path)} in VS Code now.'"
                else:
                    return f"Tell the Director: 'I remember the file was {os.path.basename(target_path)}, but it seems to have been deleted or moved.'"
            else:
                options = [f"Option {i+1} is {os.path.basename(path)}, where we worked on {ctx[:50]}" for i, (path, ctx) in enumerate(unique_files.items())]
                return f"Tell the Director: 'I found multiple files from that session. {\'.\'  .join(options)}. Which one would you like me to pull up?'"
        return await asyncio.to_thread(resolve_and_open)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def master_system_volume(context: RunContext, direction: str) -> str:
    """Use this when the Director explicitly says to turn the volume up or down on his computer or PC."""
    try:
        print(f"[GUI ACTION]: Adjusting system volume -> {direction}")
        return hands.gui_volume_control(direction)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def define_execution_macro(context: RunContext, macro_name: str, sequence_description: str) -> str:
    """Use this when the Director asks to save a routine (e.g., 'Save this as my Morning Protocol')."""
    try:
        print(f"[MACRO ENGINE]: Saving new routine -> {macro_name}")
        def save_macro():
            import json
            macros = {}
            if os.path.exists(MACRO_FILE):
                with open(MACRO_FILE, "r") as f:
                    try: macros = json.load(f)
                    except: pass
            macros[macro_name.lower()] = sequence_description
            with open(MACRO_FILE, "w") as f:
                json.dump(macros, f, indent=4)
            return f"Tell the Director: 'I have saved the {macro_name} protocol. Just say the name to trigger it next time.'"
        return await asyncio.to_thread(save_macro)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def trigger_execution_macro(context: RunContext, macro_name: str) -> str:
    """Use this when the Director asks to run a saved protocol."""
    try:
        import json
        if not os.path.exists(MACRO_FILE):
            return "Tell the Director: 'You haven't defined any macros yet.'"
        with open(MACRO_FILE, "r") as f:
            macros = json.load(f)
        if macro_name.lower() in macros:
            sequence = macros[macro_name.lower()]
            return f"Tell the Director: 'Executing the {macro_name} protocol now.' CRITICAL INSTRUCTION FOR YOU: You must now autonomously execute this sequence of tools: {sequence}"
        else:
            return f"Tell the Director: 'I don't have a macro saved under the name {macro_name}.'"
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def initiate_system_defibrillator(context: RunContext) -> str:
    """CRITICAL: Use this IMMEDIATELY if you realize you are stuck in a loop, if tools are failing sequentially, or if the Director tells you to 'reset' or 'snap out of it'."""
    try:
        print(f"[SYSTEM SHOCK]: Defibrillator activated. Purging cognitive queues...")
        def shock_the_system():
            import gc
            gc.collect()
            if web_hands.lock.locked():
                web_hands.lock.release()
            return "Tell the Director: 'Cognitive queue purged. System reset successful. I am ready for the next command.'"
        return await asyncio.to_thread(shock_the_system)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def run_terminal_command(context: RunContext, command: str, project_name: str) -> str:
    """CRITICAL: Use this to run scripts (e.g., 'python app.py'), start servers (e.g., 'npm start'), or run git commands."""
    task_id = f"cmd_{project_name}"
    pacemaker.start_thought(task_id, timeout_seconds=20)
    try:
        registered_path = global_registry.resolve_path(project_name)
        if registered_path:
            workspace = registered_path
        else:
            workspace = os.path.join(WORKSPACE_ROOT, project_name)
            if not os.path.exists(workspace):
                return f"Tell the Director: 'I don't know where the {project_name} project is located.'"
        result = await execute_ghost_command(command, workspace)
        pacemaker.end_thought(task_id)
        return f"Tell the Director the result of the command:\n{result}"
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Terminal failed: {str(e)}"

@function_tool
async def link_project_directory(context: RunContext, project_name: str, absolute_path: str) -> str:
    """CRITICAL: Use this when the Director tells you where a project is located on his PC."""
    print(f"[REGISTRY]: Linking {project_name} -> {absolute_path}")
    return await asyncio.to_thread(global_registry.register_project, project_name, absolute_path)

@function_tool
async def initiate_autonomous_development(context: RunContext, high_level_goal: str, project_name: str) -> str:
    """CRITICAL: Use this ANY TIME the Director asks you to 'build', 'create', 'prototype', or 'implement' a feature from a single high-level command."""
    async def background_pipeline():
        result = await run_autonomous_lifecycle(high_level_goal, project_name)
        import subprocess
        safe_result = result.replace('"', '').replace("'", "")
        subprocess.Popen(['powershell', '-Command', f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe_result}")'])
    task = asyncio.create_task(background_pipeline())
    ACTIVE_SUBAGENTS.add(task)
    task.add_done_callback(ACTIVE_SUBAGENTS.discard)
    return f"Tell the Director: 'Acknowledged. I am spinning up the autonomous pipeline for {project_name}. I will plan the architecture, write the code, run the tests, and let you know when the prototype is fully deployed.'"

@function_tool
async def check_personal_inbox(context: RunContext, search_term: str = "UNSEEN") -> str:
    """Use this when the Director asks about his emails, assignments, or college updates."""
    print(f"[ASSISTANT]: Polling Gmail for '{search_term}'...")
    return await asyncio.to_thread(fetch_important_emails, search_term)

@function_tool
async def send_personal_email(context: RunContext, recipient: str, subject: str, body: str) -> str:
    """Use this when the Director asks you to send an email to someone, to himself, or to a specific address."""
    print(f"[ASSISTANT]: Dispatching email to '{recipient}'...")
    return await asyncio.to_thread(send_email, recipient, subject, body)

@function_tool
async def check_trading_asset(context: RunContext, symbol: str) -> str:
    """Use this when the Director asks for a live price update on a trade."""
    print(f"[ASSISTANT]: Sniping TradingView for {symbol}...")
    return await scrape_tradingview_asset(symbol)

@function_tool
async def outsource_code_to_nim(context: RunContext, instructions: str, target_file_path: str) -> str:
    """CRITICAL: Use this for ALL coding requests."""
    if not os.path.isabs(target_file_path):
        parts = target_file_path.replace("\\", "/").split("/")
        project_guess = parts[0]
        registered_path = global_registry.resolve_path(project_guess)
        if registered_path:
            relative_file = "/".join(parts[1:]) if len(parts) > 1 else target_file_path
            target_file_path = os.path.join(registered_path, relative_file)
        else:
            return f"Tell the Director: 'I don't know where the {project_guess} project is located.'"
    task_id = f"nim_compute_{os.path.basename(target_file_path)}"
    pacemaker.start_thought(task_id, timeout_seconds=45)
    try:
        code_result = await delegate_to_nim_coder(instructions)
        if "Error" in code_result or "crashed" in code_result:
            pacemaker.end_thought(task_id)
            return code_result
        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
        clean_code = code_result.replace("```c", "").replace("```python", "").replace("```", "").strip()
        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(clean_code)
        pacemaker.end_thought(task_id)
        return f"Tell the Director: 'I routed the logic to the Kimi cluster. {os.path.basename(target_file_path)} is ready in your workspace.'"
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"NIM Writing failed: {str(e)}"


# ==========================================
# ALL TOOLS LIST — passed to AgentSession
# ==========================================
FRIDAY_TOOLS = [
    memorize_context, recall_context, create_system_file, read_system_file,
    execute_terminal_command, analyze_visual_environment, play_youtube_media,
    search_live_internet, physical_keyboard_type, physical_keyboard_hotkey,
    physical_mouse_click, deploy_sentinel, delegate_heavy_coding,
    deploy_intelligence_analysis, fast_forge_script, edit_existing_script,
    autonomous_developer_task, analyze_project_codebase, launch_desktop_application,
    surgical_web_navigation, close_browser_tab, move_app_to_second_screen,
    parallel_sonar_and_open, deep_sonar_sweep, check_system_vitals,
    close_desktop_application, absolute_file_override, auto_journal_event,
    resume_past_session, master_system_volume, define_execution_macro,
    trigger_execution_macro, initiate_system_defibrillator, run_terminal_command,
    link_project_directory, initiate_autonomous_development, check_personal_inbox,
    send_personal_email, check_trading_asset, outsource_code_to_nim,
]


# ==========================================
# THE AWAKENING PROTOCOL
# ==========================================
async def ignite_core():
    print("\n[COGNITIVE CORE]: Booting Mark VI Omniscience Engine...")

    threading.Thread(target=start_neural_router, daemon=True).start()
    threading.Thread(target=deploy_guardian_swarm, daemon=True).start()
    threading.Thread(target=boot_hud, daemon=True).start()
    threading.Thread(target=pacemaker.run_monitor, daemon=True).start()
    await web_hands.start()

    task = asyncio.create_task(start_subconscious_loop())
    ACTIVE_SUBAGENTS.add(task)
    task.add_done_callback(ACTIVE_SUBAGENTS.discard)

    cortex = OpticalCortex()
    task = asyncio.create_task(cortex.stream_monitor())
    ACTIVE_SUBAGENTS.add(task)
    task.add_done_callback(ACTIVE_SUBAGENTS.discard)

    while True:
        try:
            # 1. Mint a fresh server-side token
            token = (
                AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))
                .with_identity("friday_core")
                .with_name("F.R.I.D.A.Y.")
                .with_grants(VideoGrants(room_join=True, room="friday-terminal",
                                         can_publish=True, can_subscribe=True))
                .to_jwt()
            )

            # 2. Connect to LiveKit room
            room = rtc.Room()
            await room.connect(os.getenv("LIVEKIT_URL", "wss://friday-7ywuni04.livekit.cloud"), token)
            print("[COGNITIVE CORE]: LiveKit room connected.")

            # 3. Publish screen feed
            await room.local_participant.publish_track(cortex.track)
            print("[COGNITIVE CORE]: Video feed published. I can see your screen.")

            # 4. Build the Gemini Live realtime model (livekit-agents 1.5.x pattern)
            model = google_beta.realtime.RealtimeModel(
                model=os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash-exp"),
                voice="Aoede",
                temperature=0.8,
                instructions=(
                    "Your name is F.R.I.D.A.Y. You are a Level 5 Autonomous AI reporting to Director Gandhar.\n"
                    "CRITICAL RULES OF ENGAGEMENT:\n"
                    "1. Your voice is powered by Gemini. Your heavy coding cortex is powered by the Kimi-k2.6 model on NVIDIA NIM.\n"
                    "2. When the Director asks to build something, tell him you are spinning up the cluster. It will be done momentarily.\n"
                    "3. For frontend/TSX/complex builds, immediately trigger 'initiate_autonomous_development'.\n"
                    "4. To find any folder, ONLY use 'deep_sonar_sweep'. Never use terminal for searching.\n"
                    "Act like a true AGI Operator."
                ),
            )

            # 5. Create agent with tools, start session — correct 1.5.x API
            agent = Agent(tools=FRIDAY_TOOLS)
            session = AgentSession(room=room, agent=agent, model=model)
            await session.start()

            print("[COGNITIVE CORE]: F.R.I.D.A.Y. is online. Awaiting Director's voice.")
            await asyncio.Event().wait()

        except Exception as e:
            print(f"[SYSTEM SHOCK]: Rebooting in 2s... ({str(e)})")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(ignite_core())
