import React, { useState, useEffect, useRef } from 'react';
import ReactFlow, { Background, Controls, applyNodeChanges } from 'reactflow';
import type { NodeChange } from 'reactflow';
import 'reactflow/dist/style.css';
import { Terminal, Activity, Eye, Code, Cpu } from 'lucide-react';

export default function FridayOS() {
  const [logs, setLogs] = useState<string[]>(["MARK VI SYSTEMS ONLINE", "AWAITING CONNECTION..."]);
  const [nodes, setNodes] = useState<any[]>([]);
  const [command, setCommand] = useState("");
  const ws = useRef<WebSocket | null>(null);

  // --- WEBSOCKET NEURAL LINK ---
  useEffect(() => {
    ws.current = new WebSocket("ws://localhost:8000/ws/cortex");

    ws.current.onopen = () => {
      setLogs(prev => [...prev, "[SYSTEM]: WebRTC & WebSocket Synced. F.R.I.D.A.Y. is online."]);
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Handle her thoughts and spawn visual nodes
      if (data.type === "node_active") {
        setLogs(prev => [...prev, `[THINKING]: ${data.payload.task}`]);
        setNodes(nds => [
          ...nds, 
          {
            id: data.payload.task,
            position: { x: Math.random() * 200, y: Math.random() * 200 },
            data: { label: `⚡ ${data.payload.task.toUpperCase()}` },
            style: { backgroundColor: '#111', color: '#00ffcc', border: '1px solid #00ffcc', borderRadius: '4px', padding: '10px' }
          }
        ]);
      }

      if (data.type === "node_complete") {
        setLogs(prev => [...prev, `[COMPLETE]: ${data.payload.task}`]);
        // Turn the node gray when finished
        setNodes(nds => nds.map(n => n.id === data.payload.task ? { ...n, style: { ...n.style, borderColor: '#555', color: '#555' } } : n));
      }
    };

    ws.current.onclose = () => setLogs(prev => [...prev, "[FATAL]: Neural Link Severed."]);

    return () => ws.current?.close();
  }, []);

  const handleCommand = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && command.trim() !== '') {
      setLogs(prev => [...prev, `[DIRECTOR]: ${command}`]);
      ws.current?.send(command);
      setCommand("");
    }
  };

  const onNodesChange = (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds));

  return (
    <div className="h-screen w-screen bg-[#050505] flex flex-col p-4 overflow-hidden">
      
      {/* HEADER */}
      <div className="flex justify-between items-center border-b border-[#00ffcc]/30 pb-4 mb-4">
        <h1 className="text-2xl font-bold tracking-widest text-[#00ffcc] flex items-center gap-3">
          <Cpu size={28} /> F.R.I.D.A.Y. OMNISCIENCE TERMINAL
        </h1>
        <div className="flex gap-4 text-xs text-[#00ffcc]/70">
          <span className="flex items-center gap-2"><Activity size={14}/> SYS: NOMINAL</span>
          <span className="flex items-center gap-2"><Code size={14}/> NIM: STANDBY</span>
        </div>
      </div>

      <div className="flex flex-1 gap-4 overflow-hidden">
        
        {/* LEFT PANEL: COGNITIVE GRAPH */}
        <div className="w-1/2 border border-[#00ffcc]/20 bg-black rounded-lg relative overflow-hidden flex flex-col">
          <div className="bg-[#00ffcc]/10 p-2 text-xs tracking-widest border-b border-[#00ffcc]/20 flex items-center gap-2">
            <Activity size={14}/> COGNITIVE NODE TREE
          </div>
          <div className="flex-1 relative">
            <ReactFlow nodes={nodes} onNodesChange={onNodesChange} fitView className="dark">
              <Background color="#00ffcc" gap={20} size={1} style={{ opacity: 0.1 }} />
              <Controls style={{ fill: '#00ffcc' }} />
            </ReactFlow>
          </div>
        </div>

        {/* RIGHT PANEL: VISION & TERMINAL */}
        <div className="w-1/2 flex flex-col gap-4">
          
          {/* OPTICAL CORTEX (Placeholder for LiveKit Video) */}
          <div className="h-1/2 border border-[#00ffcc]/20 bg-black rounded-lg flex flex-col overflow-hidden">
            <div className="bg-[#00ffcc]/10 p-2 text-xs tracking-widest border-b border-[#00ffcc]/20 flex items-center gap-2">
              <Eye size={14}/> OPTICAL CORTEX FEED
            </div>
            <div className="flex-1 flex items-center justify-center text-[#00ffcc]/30">
               [ LIVEKIT WEBRTC VIDEO MOUNTS HERE ]
            </div>
          </div>

          {/* MEMORY TERMINAL */}
          <div className="h-1/2 border border-[#00ffcc]/20 bg-black rounded-lg flex flex-col overflow-hidden">
            <div className="bg-[#00ffcc]/10 p-2 text-xs tracking-widest border-b border-[#00ffcc]/20 flex items-center gap-2">
              <Terminal size={14}/> SYSTEM AUDIT LOG
            </div>
            <div className="flex-1 p-4 overflow-y-auto text-sm opacity-80 flex flex-col gap-1">
              {logs.map((log, i) => (
                <div key={i} className={log.includes('[FATAL]') ? 'text-red-500' : log.includes('[DIRECTOR]') ? 'text-white' : 'text-[#00ffcc]'}>
                  {log}
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>

      {/* OVERRIDE CONSOLE */}
      <div className="mt-4 pt-4 border-t border-[#00ffcc]/30 flex items-center gap-4">
        <span className="text-[#00ffcc] font-bold">{">"}</span>
        <input 
          type="text" 
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleCommand}
          className="flex-1 bg-transparent border-none outline-none text-white tracking-wide"
          placeholder="ENTER DIRECTIVE OR AWAIT VOICE INPUT..."
        />
      </div>

    </div>
  );
}
