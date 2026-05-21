from openai import OpenAI
import os

def delegate_to_nim_coder(prompt: str, model_name: str = "meta/llama-3.1-70b-instruct"):
    """Dynamically routes the prompt to the correct API infrastructure."""
    
    # --- THE ROUTING SWITCH ---
    if "kimi" in model_name.lower() or "moonshot" in model_name.lower():
        base_url = "https://api.moonshot.cn/v1"
        api_key = os.getenv("MOONSHOT_API_KEY") 
        actual_model = "moonshot-v1-32k" # Force the correct internal model ID
    else:
        # Default to NVIDIA NIM
        base_url = "https://integrate.api.nvidia.com/v1"
        api_key = os.getenv("NVIDIA_NIM_API_KEY")
        actual_model = model_name

    if not api_key:
        print(f"[FATAL]: API Key missing for {base_url}")
        return None

    # --- THE EXECUTION ---
    client = OpenAI(base_url=base_url, api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=actual_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[API FRACTURE]: {str(e)}")
        return None