import asyncio
import urllib.request
import os
import subprocess
from playwright.async_api import async_playwright
import psutil

class BrowserNode:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page_map = {}
        self.lock = asyncio.Lock() # THE TRAFFIC COP

    async def is_port_open(self):
        """Checks the port asynchronously so it doesn't freeze the brain."""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:9222/json/version", timeout=1) as resp:
                    return resp.status == 200
        except: return False

    async def force_boot_opera(self):
        """Asynchronously kills and boots Opera with contextual awareness."""
        import os, subprocess, asyncio, psutil
        
        # 1. Check if the user is already using Opera
        opera_is_running = any('opera.exe' in p.name().lower() for p in psutil.process_iter(['name']))
        
        if opera_is_running:
            print("[BROWSER NODE]: Opera is running, but the bridge is locked. Warning Director...")
            warning = "Director, your browser is running without the neural bridge. I am force-restarting it to establish the connection. Your tabs will be restored."
            await asyncio.to_thread(subprocess.run, ['powershell', '-Command', f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{warning}")'])
            await asyncio.sleep(4) # Give the TTS time to finish speaking
            
        print("[BROWSER NODE]: Auto-igniting Opera GX...")
        
        # Run the kill command in a separate thread to prevent freezing
        await asyncio.to_thread(os.system, "taskkill /f /im opera.exe >nul 2>&1")
        await asyncio.sleep(1.5) 
        
        opera_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\launcher.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe")
        ]
        
        valid_path = next((p for p in opera_paths if os.path.exists(p)), None)
        if not valid_path:
            print("[FATAL WEB ERROR]: Could not locate Opera GX on your hard drive.")
            return False
            
        subprocess.Popen([valid_path, "--remote-debugging-port=9222"])
        return True

    async def start(self):
        async with self.lock:
            if self.context: return 
            
            port_open = await self.is_port_open()
            if not port_open:
                success = await self.force_boot_opera()
                if not success: return
                print("[BROWSER NODE]: Waiting 8 seconds for Opera engine to fully spin up...")
                await asyncio.sleep(8) # Bumped to 8 seconds to prevent the death loop

            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
                self.context = self.browser.contexts[0] 
                
                for page in self.context.pages:
                    try:
                        title = await page.title()
                        if title: self.page_map[title] = page
                    except: pass
                print("[BROWSER NODE]: CDP Bridge connected successfully.")
            except Exception as e:
                print(f"\n[FATAL WEB ERROR]: Bridge connection failed.\nError: {str(e)}")

    async def open_tab(self, url: str) -> str:
        """Opens a tab. Shrinks the lock scope so multiple websites can download in parallel."""
        if not self.context: 
            await self.start()
            if not self.context:
                return "Tell the Director: 'My CDP bridge to Opera is severed.'"
            
        # 1. ONLY LOCK THE TAB CREATION (Takes 0.1 seconds)
        async with self.lock: 
            try:
                page = await self.context.new_page()
            except Exception as e:
                return f"Failed to spawn tab: {str(e)}"

        # 2. RELEASE THE LOCK IMMEDIATELY. Download the heavy website outside the lock!
        try:
            if not url.startswith('http'): url = 'https://' + url
            
            # CRITICAL FIX: wait_until="domcontentloaded" stops Playwright from waiting for heavy ads/images.
            # It considers the page loaded the second the raw HTML arrives.
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            
            # Grab the title quickly
            await asyncio.sleep(0.5)
            tab_title = await page.title()
            
            # Safely add it to the map
            self.page_map[tab_title] = page
            return f"Tell the Director: 'I opened {tab_title} in Opera.'"
        except Exception as e:
            return f"Tab spawned, but failed to load URL: {str(e)}"

    async def close_specific_tab(self, tab_keyword: str) -> str:
        """Surgically closes a tab safely."""
        if not self.context: 
            await self.start()
            if not self.context:
                 return "Tell the Director: 'My web bridge is down. I cannot close the tab.'"
                 
        async with self.lock:
            target_title = None
            for title in list(self.page_map.keys()):
                if tab_keyword.lower() in title.lower():
                    target_title = title
                    break
                    
            if target_title:
                try:
                    await self.page_map[target_title].close()
                    del self.page_map[target_title]
                    return f"Tell the Director: 'I surgically closed the {target_title} tab.'"
                except Exception as e:
                    return f"Failed to close tab: {str(e)}"
            return f"Tell the Director: 'I couldn't find a tab matching {tab_keyword}.'"

web_hands = BrowserNode()