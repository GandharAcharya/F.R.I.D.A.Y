import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY") 

async def delegate_to_nim_coder(prompt: str, context_files: str = "") -> str:
    """Outsources heavy coding tasks to the Moonshot Kimi model via NVIDIA NIM."""
    print(f"\n[NIM ROUTER]: Delegating heavy compute to Moonshot Kimi-k2.6...")
    
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    api_key = NVIDIA_API_KEY
    if api_key.startswith("Bearer "):
        api_key = api_key[len("Bearer "):]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    system_prompt = "You are a senior systems architect. Write production-grade code. Return ONLY the raw code, no markdown formatting, no explanations."
    full_prompt = f"Context:\n{context_files}\n\nTask:\n{prompt}"
    
    payload = {
        "model": "moonshotai/kimi-k2.6",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ],
        "max_tokens": 16384,
        "temperature": 0.2,  # Forced down for strict coding accuracy
        "top_p": 1.00,
        "stream": False,     # We need the full string to write to disk
        "chat_template_kwargs": {"thinking": True} # Keeping your custom kwargs
    }
    
    try:
        # Asynchronous HTTP request (Will not freeze F.R.I.D.A.Y.)
        async with aiohttp.ClientSession() as session:
            async with session.post(invoke_url, headers=headers, json=payload, timeout=45) as response:
                response.raise_for_status()
                data = await response.json()
                
                raw_code = data['choices'][0]['message']['content']
                return raw_code.strip()
                
    except aiohttp.ClientError as e:
        return f"NIM Network Error: {str(e)}"
    except Exception as e:
        return f"NIM Pipeline crashed: {str(e)}"