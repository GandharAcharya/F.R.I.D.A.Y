import threading
from core.models import get_realtime_model
from livekit.agents import Agent

# Thread-safe singleton holder
_agent_instance = None
_lock = threading.Lock()

def get_agent(fnc_ctx):
    """Return a cached Agent instance.
    The first call creates the agent using the safe RealtimeModel and the provided
    function-tool context (friday_functions). Subsequent calls return the same
    instance to avoid duplicate LiveKit connections.
    """
    global _agent_instance
    with _lock:
        if _agent_instance is None:
            _agent_instance = Agent(
                fnc_ctx=fnc_ctx,
            )
        return _agent_instance
