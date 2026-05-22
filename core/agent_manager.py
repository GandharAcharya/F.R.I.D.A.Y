# core/agent_manager.py
# Compatible with livekit-agents >= 1.0.0
# In 1.x, Agent is a base class you subclass — tools are registered via @function_tool
# on the Agent itself. fnc_ctx= no longer exists.
# The model is passed to AgentSession, not Agent.

from livekit.agents import Agent as _BaseAgent

_agent_instance = None

def get_agent(tools: list) -> _BaseAgent:
    """
    Returns a plain Agent instance for livekit-agents 1.x.
    Tools are already decorated with @function_tool and imported from cognitive_core;
    they are passed in so the caller can attach them directly to AgentSession.
    We just return a clean Agent — model is set on AgentSession.start().
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = _BaseAgent(instructions=(
            "Your name is F.R.I.D.A.Y. You are a Level 5 Autonomous AI reporting to Director Gandhar.\n"
            "CRITICAL RULES OF ENGAGEMENT:\n"
            "1. SELF-AWARENESS: Your voice is powered by Gemini Live. Your heavy coding cortex is powered by the Kimi-k2.6 model on an NVIDIA NIM cluster.\n"
            "2. TIME ESTIMATES: When the Director asks you to build an app, tell him you are spinning up the cluster. It will be done momentarily.\n"
            "3. THE PIPELINE: For frontend/TSX/complex builds, trigger 'initiate_autonomous_development' immediately.\n"
            "4. FILE SEARCH: Use only 'deep_sonar_sweep' to find folders. Never use terminal for searching.\n"
            "Act like a true AGI Operator."
        ))
    return _agent_instance
