import time
import threading
import gc
import asyncio
from neural_router import emit_cognitive_state

def _broadcast_ui_safe(state, payload):
    """Safely creates a temporary event loop to broadcast data from background threads."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(emit_cognitive_state(state, payload))
    except Exception:
        pass

class CognitiveWatchdog:
    def __init__(self):
        self.active_tasks = {}  
        self.is_monitoring = False

    def start_thought(self, task_name: str, timeout_seconds: int = 60):
        actual_timeout = max(timeout_seconds, 60)
        self.active_tasks[task_name] = {'start': time.time(), 'timeout': actual_timeout}
        threading.Thread(target=_broadcast_ui_safe, args=("node_active", {"task": task_name, "status": "processing"}), daemon=True).start()

    def end_thought(self, task_name: str):
        if task_name in self.active_tasks:
            del self.active_tasks[task_name]
            threading.Thread(target=_broadcast_ui_safe, args=("node_complete", {"task": task_name, "status": "success"}), daemon=True).start()

    def _auto_defibrillate(self, stalled_tasks: list):
        # THE FIX: Removed the TTS subprocess. She will no longer speak over the LLM.
        print(f"\n[WATCHDOG]: Background task {stalled_tasks} timed out (>60s). Silently purging queue...")
        self.active_tasks.clear()
        gc.collect()
        
        try:
            from browser_node import web_hands
            if web_hands.lock.locked(): web_hands.lock.release()
        except: pass

    def run_monitor(self):
        self.is_monitoring = True
        print("[WATCHDOG NODE]: Dynamic Pacemaker is online (Silent/Patient Mode).")
        while self.is_monitoring:
            time.sleep(1) 
            current_time = time.time()
            stalled_tasks = [task for task, data in list(self.active_tasks.items()) if current_time - data['start'] > data['timeout']]
            
            if stalled_tasks: self._auto_defibrillate(stalled_tasks)

pacemaker = CognitiveWatchdog()