import time
import asyncio
from integration_node import fetch_important_emails, scrape_tradingview_asset
from memory_matrix import VectorMemory

async def start_subconscious_loop():
    """The background fetch. Delayed on boot so she doesn't hijack the OS."""
    print("[SUBCONSCIOUS NODE]: Chron initialized. First fetch in 2 minutes.")
    db = VectorMemory()
    
    # 1. Give the system (and the Director) 2 minutes to breathe before starting background tasks
    await asyncio.sleep(120) 
    
    while True:
        try:
            # Fetch University / Inbox Updates
            emails = fetch_important_emails("UNSEEN")
            if "missing" not in emails and "failed" not in emails:
                db.journal_workspace_event("General", f"Latest Inbox Sync:\n{emails}")
                
            # Fetch Macro/Trading Updates
            xau_price = await scrape_tradingview_asset("XAUUSD")
            db.journal_workspace_event("TradingEdgeAI", f"Market Sync: {xau_price}")
            
        except Exception as e:
            print(f"[SUBCONSCIOUS ERROR]: {str(e)}")
            
        # Sleep for 20 minutes
        await asyncio.sleep(1200)