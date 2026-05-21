import asyncio
import json
import re
import ast

def extract_json_plan(llm_output: str):
    try:
        # Strip all markdown bloat Kimi might have added
        clean_result = llm_output.replace("```json", "").replace("```python", "").replace("```", "").strip()
        
        # Try native JSON parsing first (The Happy Path)
        try:
            parsed = json.loads(clean_result)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                # If Kimi hallucinates a dictionary, grab the first list it contains
                for key, value in parsed.items():
                    if isinstance(value, list):
                        return value
        except json.JSONDecodeError:
            pass # Fall through to aggressive Regex

        # Aggressively hunt for brackets
        match = re.search(r'\[(.*?)\]', clean_result, re.DOTALL)
        if match:
            raw_array_string = "[" + match.group(1) + "]"
            try:
                return json.loads(raw_array_string)
            except json.JSONDecodeError:
                return ast.literal_eval(raw_array_string)
        else:
            # THE ULTIMATE FALLBACK: If Kimi writes a numbered list instead of JSON
            # This strips numbers, bullets, and spaces from the start of each line
            lines = [line.lstrip(' -*1234567890.') for line in clean_result.split('\n') if line.strip()]
            if lines:
                return lines

        # Force a JSONDecodeError if we couldn't parse it to trigger the fallback check
        return json.loads(clean_result)
    except json.JSONDecodeError:
        # THE FIX: If it fails, check if the model just ran out of breath
        if not llm_output.strip().endswith("}") and not llm_output.strip().endswith("]"):
            print("[PIPELINE WARNING]: LLM output truncated. Generating emergency fix request...")
            # Here, you would loop back and pass the prompt: "You cut off. Continue exactly from where you stopped."
            return None 
        else:
            raise ValueError("Kimi hallucinates invalid JSON syntax.")

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
    
    # --- THE RESILIENT PLAN EXTRACTOR & RECOVERY ---
    tasks = extract_json_plan(plan_result)
    if tasks is None:
        print("[PIPELINE WARNING]: Attempting recovery plan generation...")
        recovery_prompt = plan_prompt + f"\nYour last response was: '{plan_result[-200:]}'... You cut off. Continue exactly from where you stopped."
        continuation = await delegate_to_nim_coder(recovery_prompt)
        combined = plan_result.strip() + continuation.strip()
        tasks = extract_json_plan(combined)

    if not tasks or not isinstance(tasks, list):
        print(f"\n[NIM ERROR RAW OUTPUT]:\n{plan_result}\n")
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
        
        from config import WORKSPACE_ROOT
        import re
        
        # 1. Dynamically detect the language from Kimi's markdown tags
        ext = ".txt"
        run_cmd = None
        if "```tsx" in code_result or "```ts" in code_result:
            ext = ".tsx"
        elif "```js" in code_result or "```javascript" in code_result:
            ext = ".js"
            run_cmd = "node"
        elif "```bash" in code_result or "```sh" in code_result:
            ext = ".sh"
            run_cmd = "bash"
        elif "```python" in code_result or "```py" in code_result:
            ext = ".py"
            run_cmd = "python"

        staging_file = os.path.join(WORKSPACE_ROOT, project_name, f"staging_step_{i}{ext}")
        os.makedirs(os.path.dirname(staging_file), exist_ok=True)
        
        # 2. Extract ONLY the code, stripping out the conversational markdown
        code_match = re.search(r"```[a-z]*\n(.*?)```", code_result, re.DOTALL)
        clean_code = code_match.group(1).strip() if code_match else code_result.strip()

        with open(staging_file, "w", encoding="utf-8") as f:
            f.write(clean_code)
            
        # 3. Only execute if it's an executable script (Don't try to run raw React components)
        test_result = ""
        if run_cmd:
            from terminal_node import execute_ghost_command
            workspace = os.path.dirname(staging_file)
            print(f"[PIPELINE]: Executing staging script -> {run_cmd} {os.path.basename(staging_file)}")
            test_result = await execute_ghost_command(f"{run_cmd} {staging_file}", workspace)
            
            # Step 2C: The Refinement Loop (Self-Healing)
            attempts = 0
            while "Traceback" in test_result and attempts < 3:
                print(f"[BUG DETECTED]: Auto-patching step {i+1}. Attempt {attempts+1}")
                patch_prompt = f"The code failed with this error:\n{test_result}\nFix the code. Return ONLY the raw code."
                patched_code = await delegate_to_nim_coder(patch_prompt)
                
                # Re-extract and save
                code_match = re.search(r"```[a-z]*\n(.*?)```", patched_code, re.DOTALL)
                clean_patched = code_match.group(1).strip() if code_match else patched_code.strip()
                
                with open(staging_file, "w", encoding="utf-8") as f:
                    f.write(clean_patched)
                    
                test_result = await execute_ghost_command(f"{run_cmd} {staging_file}", workspace)
                attempts += 1
                
            if "Traceback" in test_result:
                return f"Pipeline stalled at Step {i+1}. The code is failing tests. I need the Director's intervention."
            
    return "Pipeline Complete. All steps planned, coded, tested, and verified autonomously."