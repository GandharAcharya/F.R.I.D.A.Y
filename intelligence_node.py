import os
import asyncio
import google.generativeai as genai
import urllib.request
import xml.etree.ElementTree as ET
import requests
from os_control import SystemController

def broadcast_status(node_name: str, message: str):
    """Pings the Master Hive Router with a real-time status update."""
    try:
        requests.post("http://127.0.0.1:8000/update", json={"node": node_name, "status": message}, timeout=1)
    except:
        pass

hands = SystemController()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
analyst_brain = genai.GenerativeModel('gemini-2.5-flash')

def fetch_rss_feed(url: str, limit: int = 5) -> str:
    """Armored network request to bypass anti-bot firewalls instantly."""
    import requests
    import xml.etree.ElementTree as ET
    try:
        # Mimic a real Chrome browser on Windows 11
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        # Hard 5-second timeout so she never gets stuck idle
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status() # Instantly flag if we hit a wall
        
        root = ET.fromstring(response.content)
        compiled_headlines = []
        for item in root.findall('.//item')[:limit]:
            title = item.find('title').text if item.find('title') is not None else ""
            compiled_headlines.append(f"- {title}")
        return "\n".join(compiled_headlines)
    except Exception as e:
        return f"Stream blocked or timed out: {str(e)}"


async def generate_macro_intel_report():
    """Compiles global macro data and updates the Hive UI."""
    print("\n[SWARM NODE - INTEL]: Activating Global Communications Scraper...")
    
    # 1. PING THE UI TO TURN IT GREEN
    broadcast_status("Intel", "Scraping Macro Feeds...")
    
    finance_feed = "https://www.investing.com/rss/news_25.rss"
    world_news_feed = "https://news.yahoo.com/rss/world"
    
    loop = asyncio.get_event_loop()
    fin_data = await loop.run_in_executor(None, fetch_rss_feed, finance_feed)
    geo_data = await loop.run_in_executor(None, fetch_rss_feed, world_news_feed)
    
    print("[SWARM NODE - INTEL]: Cross-referencing data arrays...")
    # 2. PING THE UI TO SHOW REASONING STATE
    broadcast_status("Intel", "Cross-Referencing Data...")
    
    prompt = (
        "You are the Lead Macro-Driven Quantitative Analyst for TradingEdgeAI.\n" # Firewall respected
        "Analyze the following live financial data and geopolitical raw news streams.\n"
        f"--- RAW FINANCIAL DATA ---\n{fin_data}\n\n"
        f"--- RAW GEOPOLITICAL DATA ---\n{geo_data}\n\n"
        "Generate a highly technical, aggressive, operational briefing for the Director. "
    )
    
    try:
        response = await analyst_brain.generate_content_async(prompt)
        report_path = os.path.join("E:\\F.R.I.D.A.Y", "macro_intelligence_briefing.txt")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        hands.execute_terminal(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'Director, the Intelligence Swarm has compiled your macro cross-correlation report.\')"')
    except Exception as e:
        print(f"[INTEL COGNITIVE ERROR]: {str(e)}")
    finally:
        # 3. PING THE UI TO RETURN TO IDLE (CYAN)
        broadcast_status("Intel", "IDLE")