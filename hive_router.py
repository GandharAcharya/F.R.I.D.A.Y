from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# In-memory status board
swarm_status = {
    "Architect": "IDLE",
    "Intel": "IDLE",
    "Sentinel": "IDLE"
}

class StatusUpdate(BaseModel):
    node: str
    status: str

@app.post("/update")
async def update_node(data: StatusUpdate):
    swarm_status[data.node] = data.status
    print(f"[HIVE NETWORK] {data.node} updated: {data.status}")
    return {"status": "received"}

@app.get("/status")
async def get_status():
    return swarm_status

if __name__ == "__main__":
    print("[HIVE MIND] Network Router Online on Port 8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")