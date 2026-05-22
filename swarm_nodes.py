import os
import asyncio
from google import genai
import requests
import PIL.Image
import re
from os_control import SystemController

hands = SystemController()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
# DOWNGRADED TO FLASH FOR MAXIMUM SPEED AS REQUESTED
MODEL_NAME = 'gemini-2.0-flash'
EDITOR_MODEL = 'gemini-2.0-pro-exp-02-05'

def broadcast_status(node_name: str, message: str):
    """Pings the Master Hive Router with a real-time status update."""
    try:
        requests.post("http://127.0.0.1:8000/update", json={"node": node_name, "status": message}, timeout=1)
    except:
        pass

# 1. THE ISOLATED WORKSPACE GENERATOR
def get_secure_workspace(project_name: str) -> str:
    """Forces all code into a secure, predictable directory to bypass Windows Desktop/OneDrive bugs."""
    from config import WORKSPACE_ROOT
    workspace_path = os.path.join(WORKSPACE_ROOT, project_name)
    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path)
    return workspace_path

# 2. THE FAST-FORGE (Creation)
async def deploy_coder_swarm(project_name: str, filename: str, objective: str):
    print(f"\n[SWARM NODE]: Forging {filename} in {project_name} workspace...")
    broadcast_status("Architect", f"Forging {filename}...")
    try:
        # Smart routing: If the Director explicitly says "Desktop", target it. Otherwise, use Workspace.
        if project_name.lower() == "desktop":
            import os
            project_path = hands.get_desktop_path()
        else:
            project_path = get_secure_workspace(project_name)

        prompt = f"Write a complete script for {project_name}. Goal: {objective}. Return ONLY raw code."
        
        response = await client.aio.models.generate_content(model=MODEL_NAME, contents=prompt)
        code_content = response.text.replace("```python", "").replace("```html", "").replace("```", "").strip()

        file_path = os.path.join(project_path, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_content)
            
        hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, {filename} is ready in the {project_name} workspace.\')"')
    except Exception as e:
        print(f"\n[SWARM FATAL ERROR]: {str(e)}")
    finally:
        broadcast_status("Architect", "IDLE")

# 3. THE PRECISION EDITOR (Modification)
async def precision_edit_code(project_name: str, filename: str, edit_instructions: str):
    print(f"\n[SWARM NODE]: Executing SURGICAL PATCH on {filename}...")
    broadcast_status("Architect", f"Editing {filename}...")
    import json
    
    try:
        # Smart routing: If the Director explicitly says "Desktop", target it. Otherwise, use Workspace.
        if project_name.lower() == "desktop":
            import os
            project_path = hands.get_desktop_path()
        else:
            project_path = get_secure_workspace(project_name)

        file_path = os.path.join(project_path, filename)
        
        if not os.path.exists(file_path):
            print(f"[SWARM NODE ERROR]: {file_path} does not exist in workspace. Cannot edit.")
            return

        # 1. Read the existing code safely
        with open(file_path, "r", encoding="utf-8") as f:
            existing_code = f.read()

        # 2. Force the LLM to output a precise Search-and-Replace JSON block, NOT a full rewrite
        prompt = (
            f"You are a surgical code patcher for the {project_name} project.\n"
            f"Here is the current code for {filename}:\n\n{existing_code}\n\n"
            f"The Director's Edit Instructions: {edit_instructions}\n"
            "CRITICAL: Do NOT return the entire file. Return ONLY a JSON array containing the exact old code block to remove, and the new code block to insert in its place.\n"
            "You MUST match the old code's whitespace and indentation exactly so the Python string replacement works.\n"
            "Format exactly like this: [{\"search\": \"exact old lines\", \"replace\": \"new lines\"}]\n"
            "RETURN ONLY RAW JSON. NO MARKDOWN. NO CODE BLOCKS."
        )
        
        # We use the deep-thinking Pro model specifically for editing to guarantee whitespace accuracy
        response = await client.aio.models.generate_content(model=EDITOR_MODEL, contents=prompt)
        
        # 3. Clean the response and parse the JSON patch (BULLETPROOF JSON EXTRACTION)
        raw_text = response.text
        # Use Regex to hunt down the JSON array, ignoring any markdown or conversational filler the LLM hallucinated
        match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if not match:
            print(f"\n[SWARM FATAL ERROR]: Could not find a valid JSON array in the Architect's response.")
            return
            
        patch_data = match.group(0)
        edits = json.loads(patch_data)

        # 4. Apply the patches natively in Python without overwriting untouched code
        new_code = existing_code
        changes_made = 0
        
        for edit in edits:
            if edit['search'] in new_code:
                new_code = new_code.replace(edit['search'], edit['replace'], 1)
                changes_made += 1
            else:
                print(f"\n[SWARM NODE WARNING]: Could not find exact match for target block. Whitespace mismatch.")
                print(f"TARGET BLOCK:\n{edit['search']}")

        if changes_made > 0:
            # 5. Save ONLY if a safe patch was applied
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, {changes_made} surgical patches applied to {filename}. The rest of the file is untouched.\')"')
        else:
            hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, the patch failed to lock onto the target code. No overwrites were made.\')"')

    except json.JSONDecodeError:
        print(f"\n[SWARM FATAL ERROR]: Architect failed to return valid JSON patch.")
    except Exception as e:
        print(f"\n[SWARM FATAL ERROR]: {str(e)}")
    finally:
        broadcast_status("Architect", "IDLE")

async def deep_scan_project(project_name: str, query: str):
    """Ingests an entire codebase to answer complex architectural questions."""
    import os
    print(f"\n[SWARM NODE]: Initiating Deep-Scan on {project_name}...")
    
    # Smart routing: If the Director explicitly says "Desktop", target it. Otherwise, use Workspace.
    if project_name.lower() == "desktop":
        import os
        project_path = hands.get_desktop_path()
    else:
        project_path = get_secure_workspace(project_name)
    
    if not os.path.exists(project_path):
        hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, the {project_name} directory does not exist in your workspace.\')"')
        return

    # 1. Compile the entire codebase into one massive string
    all_files = []
    for root, dirs, files in os.walk(project_path):
        # Ignore git and environment folders
        if '.git' in root or '__pycache__' in root or 'venv' in root:
            continue
        for file in files:
            if file.endswith(('.py', '.html', '.css', '.js', '.json', '.c', '.cpp', '.h')):
                all_files.append(os.path.join(root, file))

    MAX_CONTEXT_CHARS = 180_000  # ~45k tokens — safe for Gemini Flash context window
    full_codebase = ""
    skipped_files = []

    for file_path in all_files:
        if len(full_codebase) >= MAX_CONTEXT_CHARS:
            skipped_files.append(file_path)
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                chunk = f"\n\n# FILE: {file_path}\n{f.read()}"
                if len(full_codebase) + len(chunk) > MAX_CONTEXT_CHARS:
                    skipped_files.append(file_path)
                    continue
                full_codebase += chunk
        except Exception:
            skipped_files.append(file_path)

    if skipped_files:
        full_codebase += (
            f"\n\n# [BUDGET EXCEEDED]: {len(skipped_files)} files omitted "
            f"to stay within context limits: {skipped_files[:5]}"
        )

    compiled_code = full_codebase

    if not compiled_code:
        print("[SWARM NODE]: No readable code found.")
        return

    # 2. Pass the massive codebase to the deep-reasoning Architect
    print("[SWARM NODE]: Codebase ingested. Analyzing architecture...")
    prompt = f"You are analyzing the {project_name} codebase. The Director asks: {query}\n\nHere is the full codebase context:\n{compiled_code}"
    
    try:
        response = await client.aio.models.generate_content(model=MODEL_NAME, contents=prompt)
        
        # 3. Save the report and alert the Director
        from config import WORKSPACE_ROOT
        report_path = os.path.join(WORKSPACE_ROOT, f"{project_name}_Analysis_Report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, the Omniscience scan is complete. The architectural report for {project_name} is in your workspace.\')"')
    except Exception as e:
        print(f"[SWARM FATAL ERROR]: {str(e)}")

async def autonomous_dev_loop(project_name: str, vague_instructions: str, visual_check: bool = False):
    """The Senior Engineer. Reads the whole project, looks at the screen, and autonomously patches the correct files."""
    import json
    print(f"\n[SWARM NODE - SENIOR DEV]: Analyzing '{vague_instructions}' for {project_name}...")
    broadcast_status("Architect", "Analyzing Code...")
    
    try:
        # Smart routing: If the Director explicitly says "Desktop", target it. Otherwise, use Workspace.
        if project_name.lower() == "desktop":
            import os
            project_path = hands.get_desktop_path()
        else:
            project_path = get_secure_workspace(project_name)

        if not os.path.exists(project_path):
            print(f"[SWARM NODE ERROR]: Workspace {project_name} not found.")
            return

        # 1. READ THE ENTIRE CODEBASE
        compiled_code = ""
        file_map = [] # Keep track of valid files
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith(('.py', '.html', '.css', '.js', '.c', '.cpp', '.h')):
                    file_path = os.path.join(root, file)
                    file_map.append(file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            compiled_code += f"\n\n--- FILE: {file} ---\n{f.read()}"
                    except: pass

        if not compiled_code:
            print("[SWARM NODE]: No code found to edit.")
            return

        # 2. OPTIONAL OPTICAL CORTEX INJECTION
        prompt_content = [
            f"You are the Senior Architect for {project_name}.\n"
            f"The Director's Intent: '{vague_instructions}'\n"
            f"Here is the entire current codebase:\n{compiled_code}\n\n"
            "CRITICAL DIRECTIVE:\n"
            "1. Deduce WHICH file(s) need to be edited to achieve the Director's intent.\n"
            "2. Generate the precise Search-and-Replace patches for those files.\n"
            "3. You must match the old whitespace perfectly.\n"
            "Format EXACTLY as a JSON array: [{\"file\": \"filename.ext\", \"search\": \"old exact code\", \"replace\": \"new code\"}]\n"
            "Return ONLY raw JSON. No markdown."
        ]

        if visual_check:
            print("[SWARM NODE]: Optical Cortex engaged. Scanning Director's monitor...")
            broadcast_status("Architect", "Scanning Screen...")
            hands.capture_screen("friday_dev_eye.png")
            img = PIL.Image.open(os.path.join(hands.root_dir, "friday_dev_eye.png"))
            prompt_content.insert(0, "Look at this screenshot of the current UI/App. Compare it to the codebase to understand what visual elements the Director wants changed.")
            prompt_content.append(img) # Feed the image to the multimodal brain

        # 3. USE THE PRO REASONING MODEL (Required for cross-referencing vision + code)
        print("[SWARM NODE]: Code & Vision ingested. Formulating autonomous patch...")
        broadcast_status("Architect", "Patches Engine...")
        response = await client.aio.models.generate_content(model=EDITOR_MODEL, contents=prompt_content)
        
        # 4. PARSE AND APPLY MULTI-FILE PATCHES (BULLETPROOF JSON EXTRACTION)
        raw_text = response.text
        # Use Regex to hunt down the JSON array, ignoring any markdown or conversational filler the LLM hallucinated
        match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if not match:
            print(f"\n[SWARM FATAL ERROR]: Could not find a valid JSON array in the Architect's response.")
            return
            
        patch_data = match.group(0)
        edits = json.loads(patch_data)
        
        changes_made = 0
        files_touched = set()

        for edit in edits:
            target_file = edit.get('file')
            if target_file not in file_map:
                continue # Skip if model hallucinates a file
                
            file_path = os.path.join(project_path, target_file)
            with open(file_path, "r", encoding="utf-8") as f:
                current_code = f.read()
                
            if edit['search'] in current_code:
                new_code = current_code.replace(edit['search'], edit['replace'], 1)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                changes_made += 1
                files_touched.add(target_file)
            else:
                print(f"[SWARM WARNING]: Whitespace mismatch in {target_file}. Patch aborted for that block.")

        if changes_made > 0:
            touched_str = ", ".join(files_touched)
            hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, intent translated. I autonomously modified {touched_str} to meet your requirements.\')"')
        else:
            hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, I could not safely map the intent to the codebase. No files were changed.\')"')

    except json.JSONDecodeError:
        print(f"\n[SWARM FATAL ERROR]: Model failed to output valid JSON.")
    except Exception as e:
        print(f"\n[SWARM FATAL ERROR]: {str(e)}")
    finally:
        broadcast_status("Architect", "IDLE")