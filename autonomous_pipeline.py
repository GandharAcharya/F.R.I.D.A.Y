import asyncio
import json

async def run_autonomous_lifecycle(goal: str, project_name: str):
    """The God-Loop: Plans, Executes, Verifies, and Refines until the goal is met."""
    print(f"\n[AUTONOMOUS PIPELINE]: Director requested feature -> {goal} for {project_name}")
    
    # We will use the NIM router to generate the architecture plan, not code
    from nvidia_nim_node import delegate_to_nim_coder
    from terminal_node import execute_ghost_command
    import os
    
    # 1. THE PLANNING PHASE
    plan_prompt = (
        f"Goal: {goal}. Project: {project_name}. "
        "Break this down into a strict step-by-step technical plan. "
        "Return ONLY a valid JSON list of strings representing the steps. No markdown."
    )
    
    plan_result = await delegate_to_nim_coder(plan_prompt)
    # --- THE IRONCLAD JSON EXTRACTOR ---
    import re
    import ast
    
    tasks = []
    try:
        # 1. Strip all markdown bloat Kimi might have added
        clean_result = plan_result.replace("```json", "").replace("```python", "").replace("```", "").strip()
        
        # 2. Try native JSON parsing first (The Happy Path)
        try:
            parsed = json.loads(clean_result)
            if isinstance(parsed, list):
                tasks = parsed
            elif isinstance(parsed, dict):
                # If Kimi hallucinates a dictionary, grab the first list it contains
                for key, value in parsed.items():
                    if isinstance(value, list):
                        tasks = value
                        break
        except json.JSONDecodeError:
            pass # Fall through to aggressive Regex

        # 3. If native fails, aggressively hunt for brackets and force-parse
        if not tasks:
            match = re.search(r'\[(.*?)\]', clean_result, re.DOTALL)
            if match:
                raw_array_string = "[" + match.group(1) + "]"
                try:
                    tasks = json.loads(raw_array_string)
                except json.JSONDecodeError:
                    # Absolute last resort: Python AST evaluation (handles single quotes and trailing commas)
                    tasks = ast.literal_eval(raw_array_string)

        if not tasks or not isinstance(tasks, list):
            raise ValueError("Extraction yielded empty or non-list data.")

    except Exception as e:
        print(f"\n[NIM ERROR RAW OUTPUT]:\n{plan_result}\n")
        print(f"[PARSER TRACEBACK]: {str(e)}")
        return "Pipeline Failed: The NIM cluster returned unparseable architecture. Check the terminal logs."
    # ---------------------------------------------------

    print(f"[AUTONOMOUS PIPELINE]: Generated {len(tasks)} steps. Initiating Execution Loop.")
    
    # Announce the plan to the Director
    import subprocess
    subprocess.Popen(['powershell', '-Command', f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("Boss, I have generated a {len(tasks)}-step architecture plan. Initiating autonomous development now.")'])

    # 2. THE EXECUTION & VERIFICATION LOOP
    for i, task in enumerate(tasks):
        print(f"\n[EXECUTING STEP {i+1}/{len(tasks)}]: {task}")
        
        # Step 2A: Generate the Code for this specific step
        code_prompt = f"Executing Step: {task}. Write the necessary code. Return ONLY the raw code."
        code_result = await delegate_to_nim_coder(code_prompt)
        
        # We assume the NIM coder tells us the filename in a comment at the top, or we default it
        # For this pipeline, we will save it to a staging file in the project workspace
        from workspace_registry import global_registry
        workspace = global_registry.resolve_path(project_name) or "E:\\F.R.I.D.A.Y\\Workspace"
        staging_file = os.path.join(workspace, f"staging_step_{i}.py")
        
        with open(staging_file, "w", encoding="utf-8") as f:
            f.write(code_result.replace("```python", "").replace("```", "").strip())
            
        # Step 2B: The Verification (CI/CD)
        print(f"[VERIFYING STEP {i+1}]: Running tests on {staging_file}...")
        test_result = await execute_ghost_command(f"python {staging_file}", workspace)
        
        # Step 2C: The Refinement Loop (Self-Healing)
        attempts = 0
        while "Traceback" in test_result and attempts < 3:
            print(f"[BUG DETECTED]: Auto-patching step {i+1}. Attempt {attempts+1}")
            patch_prompt = f"The code failed with this error:\n{test_result}\nFix the code. Return ONLY the raw code."
            patched_code = await delegate_to_nim_coder(patch_prompt)
            
            with open(staging_file, "w", encoding="utf-8") as f:
                f.write(patched_code.replace("```python", "").replace("```", "").strip())
                
            test_result = await execute_ghost_command(f"python {staging_file}", workspace)
            attempts += 1
            
        if "Traceback" in test_result:
            return f"Pipeline stalled at Step {i+1}. The code is failing tests. I need the Director's intervention."
            
    return "Pipeline Complete. All steps planned, coded, tested, and verified autonomously."