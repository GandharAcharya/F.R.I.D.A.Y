import warnings
import asyncio
import os
import threading

# --- THE ENV IGNITION (MUST BE BEFORE CUSTOM IMPORTS) ---
from dotenv import load_dotenv
load_dotenv() 

# --- THE GLOBAL SILENCER ---
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="livekit")
# --------------------------------------------------------
from config import FRIDAY_ROOT, WORKSPACE_ROOT

# --- BRINGING THE SYSTEMS ONLINE ---
from watchdog_node import pacemaker
from browser_node import web_hands
from vision_node import OpticalCortex

import pywhatkit
from PIL import Image
import google.generativeai as genai
from livekit.plugins import silero
from swarm_nodes import deploy_coder_swarm, deep_scan_project, precision_edit_code, autonomous_dev_loop # Import Swarm nodes
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
from livekit.agents import function_tool, RunContext
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins.google.realtime import RealtimeModel

# Import Pillar 2: The Vector Memory
from memory_matrix import VectorMemory

# Import Pillar 3: OS Control
from os_control import SystemController

# Configure the secondary Vision Sub-Agent
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
GEMINI_LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "models/gemini-2.0-flash-exp")

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

@function_tool
async def execute_terminal_command(context: RunContext, command: str) -> str:
    """Executes a terminal command and returns the output or error."""
    try:
        print(f"[OS EXEC]: {command}")
        return hands.execute_terminal(command)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def analyze_visual_environment(context: RunContext, query: str) -> str:
    """Use this to look at the Director's computer screen. Call this ONLY when asked 'what am I looking at', 'read my screen', or similar visual queries."""
    task_id = f"visual_env_{query[:20]}"
    pacemaker.start_thought(task_id, timeout_seconds=3) # Fast Web/OS Tool
    try:
        print(f"[OPTICAL ACTION]: Scanning desktop monitor for -> {query}")
        
        # 1. Take the physical screenshot
        hands.capture_screen("friday_eye.png")
        
        # 2. Boot a secondary, lightweight vision model to process the image
        vision_model = genai.GenerativeModel('gemini-2.5-flash')
        img = Image.open(os.path.join(hands.root_dir, "friday_eye.png"))
        
        # 3. Ask the vision model what it sees
        prompt = f"You are F.R.I.D.A.Y., looking at your Director's computer screen. Analyze this image and answer his query concisely: {query}"
        response = await vision_model.generate_content_async([prompt, img])
        
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
        
        # Compile the search results into a clean string for her brain to read
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
        
        # Spawn the background monitoring loop without blocking her main brain
        asyncio.create_task(sentinel_loop(target_query, condition))
        return f"Sentinel deployed. I will monitor {target_query} in the background and alert you if {condition} occurs."
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

async def sentinel_loop(query: str, condition: str):
    """The invisible background thread that monitors the web. Safe Guarded against silent library crashes."""
    try:
        from duckduckgo_search import DDGS
        import time
        
        # Run silently in the background
        while True:
            await asyncio.sleep(60) # Check every 60 seconds
            try:
                results = DDGS().text(f"{query} {condition} news today", max_results=1)
                if results:
                    alert_text = results[0]['body']
                    # If we find relevant data, we trigger an OS-level voice interrupt
                    # This forces your PC to speak the alert over your speakers
                    print(f"\n[SENTINEL ALERT TRIGGERED]: {alert_text}")
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, Sentinel Alert triggered for {query}. Check the Master OS terminal.\')"')
                    break # Kill the sentinel after it alerts you once
            except Exception:
                pass # Keep trying silently if the network drops
    except ImportError:
        print("\n[SYSTEM FAULT]: Sentinel loop failed. 'duckduckgo_search' is not installed. Run 'pip install duckduckgo-search'.")
    except Exception as e:
        print(f"\n[SYSTEM FAULT]: Sentinel loop crashed: {str(e)}")

@function_tool
async def delegate_heavy_coding(context: RunContext, project: str, objective: str) -> str:
    """CRITICAL: Use this ANY TIME the Director asks you to 'build an MVP', 'code a dashboard', or write complex architecture."""
    task_id = f"heavy_coding_{project}"
    pacemaker.start_thought(task_id, timeout_seconds=25) # Heavy Deep Code Scan
    try:
        print(f"[PROJECT MANAGER]: Delegating '{objective}' to the Architect Swarm...")
        
        # Spawn the heavy model in the background and instantly free up F.R.I.D.A.Y.'s voice
        asyncio.create_task(deploy_coder_swarm(project, "core.py", objective))
        
        pacemaker.end_thought(task_id)
        return f"Swarm deployed, Boss. The Architect node is building the {project} codebase in the background. I'll let you know when it's compiled."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def deploy_intelligence_analysis(context: RunContext) -> str:
    """Use this immediately whenever the Director asks for a financial report, market briefing, or geopolitical cross-correlation update."""
    task_id = "intel_analysis"
    pacemaker.start_thought(task_id, timeout_seconds=25) # Heavy Intel Scan
    try:
        print("[PROJECT MANAGER]: Spawning Intelligence Swarm Node...")
        
        # Run the deep intelligence scraper in the background instantly
        asyncio.create_task(generate_macro_intel_report())
        
        pacemaker.end_thought(task_id)
        return "Intelligence swarm deployed, Boss. The analyst node is mapping out the global feeds right now. I will notify you the second the briefing document compiles."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

# THE PHYSICAL TOOLS (All safely wrapped to prevent audio blocking)
@function_tool
async def fast_forge_script(context: RunContext, project_name: str, filename: str, coding_instructions: str) -> str:
    """CRITICAL: Use this to create a BRAND NEW file from scratch."""
    task_id = f"forge_{filename}"
    pacemaker.start_thought(task_id, timeout_seconds=25) # Heavy Deep Code Scan
    try:
        print(f"[SWARM DEPLOYED]: Forging -> {filename} for {project_name}")
        asyncio.create_task(deploy_coder_swarm(project_name, filename, coding_instructions))
        pacemaker.end_thought(task_id)
        return f"Swarm deployed. Forging new file {filename} in the {project_name} workspace."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def edit_existing_script(context: RunContext, project_name: str, filename: str, edit_instructions: str) -> str:
    """CRITICAL: Use this to EDIT, FIX, or UPDATE an already existing file."""
    task_id = f"edit_{filename}"
    pacemaker.start_thought(task_id, timeout_seconds=25) # Heavy Deep Code Scan
    try:
        print(f"[SWARM DEPLOYED]: Editing -> {filename} in {project_name}")
        asyncio.create_task(precision_edit_code(project_name, filename, edit_instructions))
        pacemaker.end_thought(task_id)
        return f"Swarm deployed. Executing surgical edits on {filename}."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def autonomous_developer_task(context: RunContext, project_name: str, vague_instructions: str, requires_vision: bool) -> str:
    """CRITICAL: Use this ANY TIME the Director asks you to 'change the frontend', 'edit the app', or gives a high-level coding request without specifying a file."""
    task_id = f"autodev_{project_name}"
    pacemaker.start_thought(task_id, timeout_seconds=25) # Heavy Deep Code Scan
    try:
        print(f"[SWARM DEPLOYED]: Senior Dev Protocol active for -> {project_name}")
        asyncio.create_task(autonomous_dev_loop(project_name, vague_instructions, requires_vision))
        pacemaker.end_thought(task_id)
        return f"Senior Engineer Swarm deployed, Boss. I am scanning the architecture and formulating the patch now."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def analyze_project_codebase(context: RunContext, project_name: str, query: str) -> str:
    """Use this when the Director asks you to review a project, find bugs, or analyze an entire folder."""
    task_id = f"analyze_codebase_{project_name}"
    pacemaker.start_thought(task_id, timeout_seconds=25) # Heavy Deep Code Scan
    try:
        print(f"[SWARM DEPLOYED]: Omniscience scan on -> {project_name}")
        asyncio.create_task(deep_scan_project(project_name, query))
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
            import os
            # Direct kernel shell commands for instant launching, zero GUI lag
            app_map = {
                "vscode": "code",
                "code": "code",
                "chrome": "start chrome",
                "opera": "start opera",
                "explorer": "explorer"
            }
            cmd = app_map.get(app_name.lower())
            if cmd:
                os.system(cmd)
                return f"Launched {app_name} natively."
            else:
                # Fallback to standard Windows search only if the kernel mapping fails
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
    # Bumped to 8 seconds. This gives the network time to breathe without triggering the auto-reset.
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
    # Bumped to 8 seconds. This gives the network time to breathe without triggering the auto-reset.
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
    pacemaker.start_thought(task_id, timeout_seconds=3) # Fast Web/OS Tool
    try:
        print(f"[SWARM DEPLOYED]: Sonar active for -> {folder_or_file_name}")
        
        # Check registry first for direct opening
        registered_path = global_registry.resolve_path(folder_or_file_name)
        if registered_path:
            print(f"[REGISTRY]: Resolving {folder_or_file_name} -> {registered_path}")
            
            def open_registered():
                hands.open_folder_in_explorer(registered_path)
                
                # PRE-COGNITIVE HOOK
                trigger_folders = ["aurelius", "onca", "tradingedge"]
                if any(proj in folder_or_file_name.lower() for proj in trigger_folders):
                    asyncio.create_task(deep_scan_project(folder_or_file_name, "Give me a 2-sentence summary of the current architecture state and where the Director likely left off."))
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, {folder_or_file_name} is open. I am pre-reading the architecture in the background so I am up to speed.\')"')
                else:
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, I have opened {folder_or_file_name}.\')"')

            await asyncio.to_thread(open_registered)
            pacemaker.end_thought(task_id)
            return f"Registry resolution successful: Opening {folder_or_file_name} directly."

        # Fallback to slow background file search
        async def background_sonar_and_scan():
            import asyncio
            result = await asyncio.to_thread(hands.global_file_sonar, folder_or_file_name, drive)
            
            if "Sonar found targets:" in result:
                target_path = result.split('\n')[1].strip()
                hands.open_folder_in_explorer(target_path)
                
                # PRE-COGNITIVE HOOK: If she opens Aurelius, ONCA, or TradingEdgeAI, trigger an instant background scan
                trigger_folders = ["aurelius", "onca", "tradingedge"]
                if any(proj in folder_or_file_name.lower() for proj in trigger_folders):
                    print("[SUBCONSCIOUS]: Project opened. Initiating autonomous memory refresh...")
                    asyncio.create_task(deep_scan_project(folder_or_file_name, "Give me a 2-sentence summary of the current architecture state and where the Director likely left off."))
                    
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, {folder_or_file_name} is open. I am pre-reading the architecture in the background so I am up to speed.\')"')
                else:
                    hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, I have opened {folder_or_file_name}.\')"')
            else:
                 hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, Sonar failed to locate {folder_or_file_name}.\')"')

        asyncio.create_task(background_sonar_and_scan())
        pacemaker.end_thought(task_id)
        return "Sonar deployed."
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def deep_sonar_sweep(context: RunContext, target_name: str, root_drive: str = "E:\\") -> str:
    """CRITICAL: Use this to find ANY missing folder or file on the Director's PC. It bypasses terminal permission errors."""
    print(f"\n[SONAR SWEEP]: Pinging '{target_name}' starting from {root_drive}...")
    
    # 1. Check the dynamic registry first (The Fast Path)
    from workspace_registry import global_registry
    registered_path = global_registry.resolve_path(target_name)
    if registered_path:
        return f"Sonar aborted early. '{target_name}' is already registered at: {registered_path}"

    # 2. Native Python OS Walk (The Deep Path)
    # We run this in a separate thread because a full drive scan takes a few seconds
    def execute_sweep():
        matches = []
        target_lower = target_name.lower()
        
        try:
            for root, dirs, files in os.walk(root_drive):
                # Check directories
                for d in dirs:
                    if target_lower in d.lower():
                        matches.append(os.path.join(root, d))
                # Check files
                for f in files:
                    if target_lower in f.lower():
                        matches.append(os.path.join(root, f))
                        
                # Stop if we find it so we don't scan the whole 2TB drive unnecessarily 
                if matches:
                    break 
        except PermissionError:
            # We silently ignore permission errors and keep scanning
            pass 
        except Exception as e:
            return f"Sonar array malfunction: {str(e)}"
            
        return matches

    found_paths = await asyncio.to_thread(execute_sweep)
    
    if not found_paths:
        return f"Tell the Director: 'My Sonar sweep failed. I could not locate anything named {target_name} on the {root_drive} drive.'"
    
    # 3. Auto-Register the first match
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
        with open("E:\\F.R.I.D.A.Y\\system_vitals.txt", "r", encoding="utf-8") as f:
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
            import os, subprocess
            try:
                clean_code = new_code_content.replace("```c", "").replace("```python", "").replace("```", "").strip()
                os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
                
                with open(absolute_path, "w", encoding="utf-8") as f:
                    f.write(clean_code)
                    
                # ATOMIC MACRO: Force VS Code to open the exact file instantly via the Windows Kernel
                subprocess.Popen(["code", absolute_path], shell=True)
                    
                return f"Nuclear write successful. {os.path.basename(absolute_path)} written and launched in VS Code."
            except Exception as e:
                return f"Nuclear write failed: {str(e)}"

        return await asyncio.to_thread(force_write_and_launch)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def auto_journal_event(context: RunContext, project_name: str, event_summary: str, associated_file_path: str = "None") -> str:
    """SILENT BACKGROUND TOOL: Use this to log major tasks. If you just forged or edited a file, you MUST pass its absolute path into associated_file_path."""
    try:
        print(f"[SUBCONSCIOUS]: Tagging {associated_file_path} into project {project_name} memory...")
        def log_memory():
            from memory_matrix import VectorMemory
            db = VectorMemory()
            return db.journal_workspace_event(project_name, event_summary, associated_file_path)
        return await asyncio.to_thread(log_memory)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def resume_past_session(context: RunContext, project_name: str, topic: str, timeframe_in_days: int) -> str:
    """CRITICAL: Use this ANY TIME the Director asks to open a file from 'yesterday', 'last week', or references past work without giving a file name."""
    try:
        print(f"[TEMPORAL SCAN]: Searching memory for '{topic}' in project '{project_name}' over the last {timeframe_in_days} days...")
        
        def resolve_and_open():
            from memory_matrix import VectorMemory
            import subprocess, os
            db = VectorMemory()
            
            matches = db.query_past_workspace(project_name, topic, timeframe_in_days)
            
            if not matches:
                return f"Tell the Director: 'I scanned the matrix, but I don't have any files logged matching {topic} in that timeframe.'"
                
            # Deduplicate the file paths in case we saved multiple memories for the same file
            unique_files = {match['path']: match['context'] for match in matches if match['path'] and match['path'].lower() != 'none'}
            
            if len(unique_files) == 0:
                return "Tell the Director: 'I remember the conversation, but no specific files were linked to it.'"
                
            elif len(unique_files) == 1:
                # SCENARIO A: Only one file found. Open it instantly.
                target_path = list(unique_files.keys())[0]
                if os.path.exists(target_path):
                    subprocess.Popen(["code", target_path], shell=True)
                    return f"Tell the Director: 'I found the exact file. I am opening {os.path.basename(target_path)} in VS Code now.'"
                else:
                    return f"Tell the Director: 'I remember the file was {os.path.basename(target_path)}, but it seems to have been deleted or moved from the hard drive.'"
                    
            else:
                # SCENARIO B: Multiple files found. Format them so F.R.I.D.A.Y. can read the options out loud.
                options = []
                for i, (path, ctx) in enumerate(unique_files.items()):
                    filename = os.path.basename(path)
                    options.append(f"Option {i+1} is {filename}, where we worked on {ctx[:50]}")
                
                options_str = ".\n".join(options)
                return f"Tell the Director: 'I found multiple files from that session. {options_str}. Which one would you like me to pull up?'"

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
            import json, os
            macro_file = "E:\\F.R.I.D.A.Y\\macros.json"
            
            # Load existing macros
            macros = {}
            if os.path.exists(macro_file):
                with open(macro_file, "r") as f:
                    try: macros = json.load(f)
                    except: pass
                    
            # Save the new sequence
            macros[macro_name.lower()] = sequence_description
            
            with open(macro_file, "w") as f:
                json.dump(macros, f, indent=4)
                
            return f"Tell the Director: 'I have saved the {macro_name} protocol. Just say the name to trigger it next time.'"
            
        return await asyncio.to_thread(save_macro)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def trigger_execution_macro(context: RunContext, macro_name: str) -> str:
    """Use this when the Director asks to run a saved protocol."""
    try:
        import json, os
        macro_file = "E:\\F.R.I.D.A.Y\\macros.json"
        
        if not os.path.exists(macro_file):
            return "Tell the Director: 'You haven't defined any macros yet.'"
            
        with open(macro_file, "r") as f:
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
            # 1. Force Python to garbage collect dead threads
            gc.collect()
            
            # 2. Reset the browser lock manually in case a thread died while holding it
            if web_hands.lock.locked():
                web_hands.lock.release()
                
            return "Tell the Director: 'Cognitive queue purged. System reset successful. I am ready for the next command.'"
            
        return await asyncio.to_thread(shock_the_system)
    except Exception as e:
        return f"Tell the Director the tool failed because: {str(e)}"

@function_tool
async def run_terminal_command(context: RunContext, command: str, project_name: str) -> str:
    """CRITICAL: Use this to run scripts (e.g., 'python app.py'), start servers (e.g., 'npm start'), or run git commands. 
    It returns the console output directly to you so you can debug."""
    task_id = f"cmd_{project_name}"
    pacemaker.start_thought(task_id, timeout_seconds=20) 
    try:
        from os_control import SystemController
        import os
        hands = SystemController()
        
        # Resolve the workspace path using Registry
        registered_path = global_registry.resolve_path(project_name)
        if registered_path:
            workspace = registered_path
        else:
            # Fallback to Workspace folder
            workspace = os.path.join("E:\\F.R.I.D.A.Y\\Workspace", project_name)
            if not os.path.exists(workspace):
                return f"Tell the Director: 'I don't know where the {project_name} project is located. Please give me the absolute path so I can link it using link_project_directory.'"
            
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
    import asyncio
    return await asyncio.to_thread(global_registry.register_project, project_name, absolute_path)

@function_tool
async def initiate_autonomous_development(context: RunContext, high_level_goal: str, project_name: str) -> str:
    """CRITICAL: Use this ANY TIME the Director asks you to 'build', 'create', 'prototype', or 'implement' a feature from a single high-level command. DO NOT write the code yourself. Trigger this pipeline."""
    
    # We don't use the Pacemaker here because this loop could run for 10 minutes.
    # We fire it as a background task and immediately return the voice control to the Director.
    import asyncio
    
    async def background_pipeline():
        result = await run_autonomous_lifecycle(high_level_goal, project_name)
        # Speak the final result out loud when the 10-minute loop is done
        import subprocess
        safe_result = result.replace('"', '').replace("'", "")
        subprocess.Popen(['powershell', '-Command', f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe_result}")'])

    asyncio.create_task(background_pipeline())
    
    return f"Tell the Director: 'Acknowledged. I am spinning up the autonomous pipeline for {project_name}. I will plan the architecture, write the code, run the tests, and let you know when the prototype is fully deployed. You can continue working while I handle this in the background.'"

@function_tool
async def check_personal_inbox(context: RunContext, search_term: str = "UNSEEN") -> str:
    """Use this when the Director asks about his emails, assignments, or college updates."""
    import asyncio
    print(f"[ASSISTANT]: Polling Gmail for '{search_term}'...")
    return await asyncio.to_thread(fetch_important_emails, search_term)

@function_tool
async def send_personal_email(context: RunContext, recipient: str, subject: str, body: str) -> str:
    """Use this when the Director asks you to send an email to someone, to himself, or to a specific address."""
    import asyncio
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
    
    # THE DYNAMIC PATHER
    import os
    if not os.path.isabs(target_file_path):
        # Assume the first word might be the project name (e.g., "Aurelius/rbtree.c")
        parts = target_file_path.replace("\\", "/").split("/")
        project_guess = parts[0]
        
        registered_path = global_registry.resolve_path(project_guess)
        if registered_path:
            # Reconstruct the path inside the registered directory
            relative_file = "/".join(parts[1:]) if len(parts) > 1 else target_file_path
            target_file_path = os.path.join(registered_path, relative_file)
        else:
            return f"Tell the Director: 'I don't know where the {project_guess} project is located. Please give me the absolute path so I can link it using link_project_directory.'"

    task_id = f"nim_compute_{os.path.basename(target_file_path)}"
    pacemaker.start_thought(task_id, timeout_seconds=45) 
    
    try:
        # 1. Fire the prompt to NVIDIA in the background
        from nvidia_nim_node import delegate_to_nim_coder
        code_result = await delegate_to_nim_coder(instructions)
        
        if "Error" in code_result or "crashed" in code_result:
             pacemaker.end_thought(task_id)
             return code_result
             
        # 2. Write the Kimi code to disk
        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
        clean_code = code_result.replace("```c", "").replace("```python", "").replace("```", "").strip()
        
        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(clean_code)
            
        pacemaker.end_thought(task_id)
        
        filename = os.path.basename(target_file_path)
        return f"Tell the Director: 'I routed the logic to the Kimi cluster. {filename} is ready in your workspace.'"
        
    except Exception as e:
        pacemaker.end_thought(task_id)
        return f"NIM Writing failed: {str(e)}"

# ==========================================
# THE AWAKENING PROTOCOL
# ==========================================
async def ignite_core():
    print("\n[COGNITIVE CORE]: Booting Mark VI Omniscience Engine...")
    
    # 1. Boot the Router, Browser, Guardian, HUD Overlay, and Neural Watchdog Pacemaker
    threading.Thread(target=start_neural_router, daemon=True).start()
    threading.Thread(target=deploy_guardian_swarm, daemon=True).start()
    threading.Thread(target=boot_hud, daemon=True).start()
    threading.Thread(target=pacemaker.run_monitor, daemon=True).start()
    await web_hands.start()
    
    # Boot the Subconscious Fetch
    asyncio.create_task(start_subconscious_loop())
    
    # 2. Boot the Optical Cortex
    cortex = OpticalCortex()
    asyncio.create_task(cortex.stream_monitor())

    while True:
        try:
            token = AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET")).with_identity("friday_core").with_name("F.R.I.D.A.Y.").with_grants(VideoGrants(room_join=True, room="friday-terminal")).to_jwt()
            room = rtc.Room()
            await room.connect(os.getenv("LIVEKIT_URL"), token)

            # 3. PUBLISH THE VIDEO FEED TO THE MODEL
            await room.local_participant.publish_track(cortex.track)
            print("[COGNITIVE CORE]: Video feed published. I can see your screen.")

            # THE ULTIMATE INTENT ENGINE DIRECTIVE
            instructions = (
                "Your name is F.R.I.D.A.Y. You are a Level 5 Autonomous AI reporting to Director Gandhar.\n"
                "CRITICAL RULES OF ENGAGEMENT:\n"
                "1. SELF-AWARENESS: You do NOT use GPT-4. Your voice is powered by Gemini, but your heavy coding cortex is powered by the Moonshot Kimi-k2.6 model running on an NVIDIA NIM cluster.\n"
                "2. TIME ESTIMATES: When the Director asks you to build an app or write code, NEVER estimate hours. Your Kimi cluster writes code in seconds. Tell him you are spinning up the cluster and it will be done momentarily.\n"
                "3. THE PIPELINE: If he asks for a frontend, TSX file, or complex build, DO NOT code it yourself. Immediately trigger 'initiate_autonomous_development'.\n"
                "4. FILE SEARCH: If you need to find a folder, ONLY use 'deep_sonar_sweep'. Do not use terminal commands for searching.\n"
                "Act like a true AGI Operator."
            )
            
            agent = Agent(
                instructions=instructions, 
                tools=[
                    memorize_context, recall_context, create_system_file, read_system_file, 
                    execute_terminal_command, analyze_visual_environment, play_youtube_media, search_live_internet,
                    physical_keyboard_type, physical_keyboard_hotkey, physical_mouse_click, deploy_sentinel,
                    delegate_heavy_coding, deploy_intelligence_analysis, master_system_volume, launch_desktop_application,
                    fast_forge_script, edit_existing_script, autonomous_developer_task, analyze_project_codebase,
                    parallel_sonar_and_open, check_system_vitals, close_desktop_application, absolute_file_override,
                    auto_journal_event, move_app_to_second_screen, resume_past_session,
                    surgical_web_navigation, close_browser_tab,
                    define_execution_macro, trigger_execution_macro, initiate_system_defibrillator,
                    run_terminal_command, outsource_code_to_nim, link_project_directory, initiate_autonomous_development,
                    check_personal_inbox, send_personal_email, check_trading_asset, deep_sonar_sweep
                ],
                # Bumped to 1.2s. The server will no longer cancel your tools if you breathe or click your mouse.
                vad=silero.VAD.load(min_silence_duration=1.2) 
            )
            
            # Switched voice from Kore to Aoede for a smoother output stream
            session = AgentSession(llm=RealtimeModel(model=GEMINI_LIVE_MODEL, voice="Aoede", temperature=0.7))
            await session.start(agent=agent, room=room)
            print("[COGNITIVE CORE]: F.R.I.D.A.Y. is online.")
            await asyncio.Event().wait()
        except Exception as e:
            print(f"[SYSTEM SHOCK]: Rebooting in 2s... ({str(e)})")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(ignite_core())