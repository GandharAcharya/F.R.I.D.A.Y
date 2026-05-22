import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactFlow, { Background, applyNodeChanges, applyEdgeChanges, MarkerType } from 'reactflow';
import type { NodeChange, EdgeChange, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';
import { Terminal, Activity, Eye, Code, Target, Layers3, Radio, MessageSquare, Zap } from 'lucide-react';
import { Room, RoomEvent } from 'livekit-client';

// --- VISUAL TELEMETRY MODULES ---
const StatusIndicator = ({ label, icon: Icon, value, status }) => (
  <div className="flex flex-col gap-1 border-l border-[#00ffcc]/30 pl-3">
    <div className="flex items-center gap-2 text-[#00ffcc]/60 text-xs">
      <Icon size={14} className={status === 'warning' ? 'text-yellow-400' : 'text-[#00ffcc]/60'} />
      {label}
    </div>
    <div className={`text-lg font-bold tracking-wider ${status === 'warning' ? 'text-yellow-400' : 'text-white'}`}>{value}</div>
  </div>
);

const TelemetryScanner = () => (
  <div className="text-[9px] text-[#00ffcc]/40 space-y-0.5 leading-tight opacity-70">
    <div>{`[SCAN]` + ' >'.repeat(30)}</div>
    <div>{`RANG: ${Math.random().toFixed(4)} KM > TARGET_TRAC_LOCKED`}</div>
    <div>{`VECT: ${[...Array(6)].map(() => (Math.random() > 0.5 ? '1' : '0')).join('')} > VECTOR_ALGN_NOMINAL`}</div>
    <div>{`SCAN: ${Math.random().toFixed(4)} ARC > RADIAL_SCAN_COMPLETE`}</div>
  </div>
);

const JarvisCore = () => (
  <div className="relative w-48 h-48 flex items-center justify-center scale-90">
    <div className="absolute inset-0 border-[1px] border-dashed border-[#00ffcc]/40 rounded-full animate-spin-slow"></div>
    <div className="absolute inset-2 border-[2px] border-t-transparent border-[#00ffcc]/60 rounded-full animate-spin-reverse"></div>
    <div className="absolute inset-6 border-[4px] border-dotted border-[#00ffcc]/30 rounded-full animate-spin-slow"></div>
    <div className="absolute inset-10 bg-[radial-gradient(circle,_rgba(0,255,204,0.15)_0%,_transparent_70%)] rounded-full flex items-center justify-center animate-pulse">
        <Radio size={32} className="text-[#00ffcc] hud-glow opacity-80" />
    </div>
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-30">
        <div className="w-full h-[1px] bg-[#00ffcc]"></div>
        <div className="h-full w-[1px] bg-[#00ffcc] absolute"></div>
    </div>
  </div>
);

// --- NODE TYPES (defined OUTSIDE component to prevent React Flow warning) ---
const nodeTypes = {};

// --- NEURAL ROUTER BASE URL ---
const ROUTER_URL = import.meta.env.VITE_ROUTER_URL || 'http://localhost:8080';

// --- MASTER COMPONENT ---
export default function FridayOS() {
  const [logs, setLogs] = useState<string[]>(["MARK VI OMNISCIENCE TERMINAL INITIALIZED", "DECODING SYMBOLIC PROTOCOLS...", "AWAITING CORTEX SYNC..."]);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [command, setCommand] = useState("");
  const [voiceStatus, setVoiceStatus] = useState("STANDBY");
  const ws   = useRef<WebSocket | null>(null);
  const room = useRef<Room | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // ─── WEBSOCKET: connects ONCE ─────────────────────────────────────────────
  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket(`${ROUTER_URL.replace('http', 'ws')}/ws/cortex`);

      ws.current.onopen = () => {
        setLogs(prev => [...prev, "[HUD]: Hive Router linked. Real-time telemetry active."]);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === "node_active") {
            setLogs(prev => [...prev, `[THINKING]: ${data.payload.task}`]);
            const id = data.payload.task;
            setNodes(nds => {
              const previousNode = nds[nds.length - 1];
              const newNode: Node = {
                id,
                position: { x: (Math.random() * 300) + 50, y: (nds.length * 100) + 50 },
                data: { label: `⚡ ${id.toUpperCase()}` },
                style: {
                  backgroundColor: 'transparent', color: '#00ffcc',
                  border: '1px solid rgba(0,255,204,0.3)', borderRadius: '0px',
                  padding: '12px', fontSize: '11px', letterSpacing: '1px',
                  fontWeight: 'bold', boxShadow: '0 0 10px rgba(0,255,204,0.5)',
                  transform: 'skewX(-10deg)'
                }
              };
              if (previousNode) {
                setEdges(eds => [...eds, {
                  id: `e-${previousNode.id}-${id}`,
                  source: previousNode.id, target: id,
                  style: { stroke: '#00ffcc', strokeWidth: 2 },
                  markerEnd: { type: MarkerType.Arrow, color: '#00ffcc' },
                }]);
              }
              return [...nds, newNode];
            });
          }

          if (data.type === "node_complete") {
            setLogs(prev => [...prev, `[COMPLETE]: ${data.payload.task}`]);
            setNodes(nds => nds.map(n => n.id === data.payload.task
              ? { ...n, style: { ...n.style, borderColor: '#555', color: '#555', boxShadow: 'none' } } : n));
            setEdges(eds => eds.map(e =>
              (e.source === data.payload.task || e.target === data.payload.task)
                ? { ...e, style: { ...e.style, stroke: '#555' } } : e));
          }
        } catch (_) {}
      };

      ws.current.onclose = () => {
        setLogs(prev => [...prev, "[HUD]: Hive Router disconnected. Reconnecting in 3s..."]);
        setTimeout(connect, 3000);
      };
    };

    connect();
    return () => ws.current?.close();
  }, []);

  // ─── LIVEKIT: fetch fresh token from neural_router, then connect ──────────
  useEffect(() => {
    let lkRoom: Room;

    const bootVoice = async () => {
      try {
        setLogs(prev => [...prev, "[COMM]: Requesting voice token from Neural Router..."]);

        const res = await fetch(`${ROUTER_URL}/livekit-token`);
        const { token, url, error } = await res.json();

        if (error || !token) {
          setLogs(prev => [...prev, `[COMM ERROR]: Token fetch failed — ${error || 'empty token'}. Check .env LIVEKIT_API_KEY/SECRET.`]);
          return;
        }

        lkRoom = new Room();
        room.current = lkRoom;

        lkRoom.on(RoomEvent.TrackSubscribed, (track) => {
          if (track.kind === 'audio' && audioRef.current) {
            track.attach(audioRef.current);
            setVoiceStatus('LIVE');
            setLogs(prev => [...prev, "[COMM]: Neural voice link established. F.R.I.D.A.Y. is online."]);
          }
        });

        lkRoom.on(RoomEvent.Disconnected, () => {
          setVoiceStatus('SEVERED');
          setLogs(prev => [...prev, "[COMM]: Voice link disconnected."]);
        });

        await lkRoom.connect(url, token, { autoSubscribe: true });
        await lkRoom.localParticipant.setMicrophoneEnabled(true);
        setLogs(prev => [...prev, "[COMM]: Microphone armed. Speak to F.R.I.D.A.Y."]);

      } catch (err: any) {
        setLogs(prev => [...prev, `[COMM ERROR]: ${err.message}`]);
      }
    };

    bootVoice();
    return () => { lkRoom?.disconnect(); };
  }, []);

  const handleCommand = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && command.trim() !== '') {
      setLogs(prev => [...prev, `[DIRECTOR]: ${command}`]);
      ws.current?.send(command);
      setCommand("");
    }
  };

  const onNodesChange = useCallback((changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  return (
    <div className="h-screen w-screen bg-[#020202] text-[#00ffcc] flex flex-col p-6 overflow-hidden font-mono relative">
      {/* Hidden audio element for F.R.I.D.A.Y.'s voice */}
      <audio ref={audioRef} autoPlay />

      {/* GLOBAL TACTICAL SCANLINES */}
      <div className="absolute inset-0 scanlines"></div>

      {/* GLOBAL RADIAL HUD OVERLAY */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden z-0 opacity-10">
          <div className="w-[150vw] h-[150vw] border-[1px] border-[#00ffcc] rounded-full absolute animate-spin-slow"></div>
          <div className="w-[100vw] h-[100vw] border-[2px] border-dashed border-[#00ffcc] rounded-full absolute animate-spin-reverse"></div>
          <div className="w-[50vw] h-[50vw] border-[1px] border-[#00ffcc] rounded-full absolute"></div>
      </div>

      {/* BACKGROUND HEX LAYER */}
      <div className="absolute inset-0 bg-[url('/hex_bg.png')] opacity-10 pointer-events-none"></div>

      {/* HEADER SECTION */}
      <div className="flex justify-between items-center border-b border-[#00ffcc]/40 pb-5 mb-6 relative">
        <div className="flex gap-4 items-center">
          <Layers3 size={32} className="text-[#00ffcc]" />
          <h1 className="text-3xl font-light tracking-[0.3em] text-[#00ffcc] tactical-glow animate-flicker">
            F.R.I.D.A.Y. <span className='text-white'>OMNISCIENCE HUD</span>
          </h1>
        </div>
        <div className="flex gap-6 text-xs text-center border border-[#00ffcc]/30 p-2 rounded-sm bg-[#111]">
          <StatusIndicator label="SYSTEM LOAD" icon={Activity} value="NORMAL" status="nominal" />
          <StatusIndicator label="CORTEX STATUS" icon={Layers3} value="LINKED" status="nominal" />
          <StatusIndicator label="NIM CLUSTER" icon={Code} value="STANDBY" status="nominal" />
          <StatusIndicator label="VOICE LINK" icon={Eye} value={voiceStatus} status={voiceStatus === 'LIVE' ? 'nominal' : 'warning'} />
        </div>
        <div className="absolute top-0 right-0 p-2 text-[8px] text-[#00ffcc]/40 bg-black/50 tracking-widest">{`[ BUILD: MARK_VI_OS_HUD ] [ DIRECTOR_GANDHAR_ACHARYA ]`}</div>
      </div>

      <div className="flex flex-1 gap-6 overflow-hidden relative">

        {/* LEFT PANEL: COGNITIVE GEOMETRY */}
        <div className="w-1/2 relative overflow-hidden flex flex-col p-1 rounded-3xl bg-black/20 backdrop-blur-md border border-[#00ffcc]/10 shadow-[0_0_30px_rgba(0,255,204,0.05)_inset]">
          <div className="bg-[#111] p-3 text-sm tracking-[0.2em] font-bold border border-[#00ffcc]/30 flex items-center justify-between">
            <div className="flex items-center gap-3"><Activity size={16} /> COGNITIVE NODE TRAJECTORY</div>
            <div className="text-xs opacity-70">ACTIVE PROTOCOLS: {nodes.length}</div>
          </div>
          <div className="flex-1 relative">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              className="dark"
            >
              <Background color="#00ffcc" gap={20} size={1} style={{ opacity: 0.05 }} />
            </ReactFlow>
          </div>
          <div className="absolute bottom-4 left-4 p-2 bg-black/70 border border-[#00ffcc]/30 text-xs tracking-wider opacity-60">
            {`X:${nodes[nodes.length - 1]?.position?.x.toFixed(2) || '--'} Y:${nodes[nodes.length - 1]?.position?.y.toFixed(2) || '--'} [TRACE_ACTIVE]`}
          </div>
          <div className="absolute top-16 right-4 p-2 opacity-50"><TelemetryScanner /></div>
        </div>

        {/* RIGHT PANEL: RECEPTION & LOGS */}
        <div className="w-1/2 flex flex-col gap-6">

          {/* RECEPTION & COGNITIVE WAVEFORM */}
          <div className="h-1/2 relative overflow-hidden flex flex-col p-1 rounded-3xl bg-black/20 backdrop-blur-md border border-[#00ffcc]/10 shadow-[0_0_30px_rgba(0,255,204,0.05)_inset]">
            <div className="bg-[#111] p-3 text-sm tracking-[0.2em] font-bold border border-[#00ffcc]/30 flex items-center gap-3">
              <Eye size={16} /> COGNITIVE FEED & WAVEFORM
            </div>
            <div className="flex-1 flex gap-4 p-3 relative">
              <div className="w-3/5 border-2 border-[#00ffcc]/40 bg-[#0a0a0a] flex items-center justify-center text-[#00ffcc]/30 relative">
                [ OPTICAL CORTEX FEED ]
                <Target size={20} className="absolute top-2 left-2 text-[#00ffcc]/50" />
              </div>
              <div className="w-2/5 flex flex-col gap-3 justify-center items-center">
                <JarvisCore />
                <div className="text-center text-xs opacity-80 leading-relaxed tracking-wider text-[#00ffcc]">
                  VOICE PROTOCOL<br />
                  <span className={voiceStatus === 'LIVE' ? 'text-[#00ffcc]' : 'text-yellow-400'}>[{voiceStatus}]</span>
                </div>
              </div>
              <div className="absolute bottom-2 right-2 p-1 opacity-50 scale-75"><TelemetryScanner /></div>
            </div>
          </div>

          {/* AUDIT LOGS & DENSE DATA */}
          <div className="h-1/2 relative overflow-hidden flex flex-col p-1 rounded-3xl bg-black/20 backdrop-blur-md border border-[#00ffcc]/10 shadow-[0_0_30px_rgba(0,255,204,0.05)_inset]">
            <div className="bg-[#111] p-3 text-sm tracking-[0.2em] font-bold border border-[#00ffcc]/30 flex items-center gap-3">
              <Terminal size={16} /> SYSTEM AUDIT & DENSE DATA MATRIX
            </div>
            <div className="flex-1 p-5 overflow-y-auto text-xs opacity-80 flex flex-col gap-1.5 leading-relaxed relative z-10">
              {logs.map((log, i) => (
                <div key={i} className={
                  log.includes('[FATAL]') ? 'text-red-500 font-bold' :
                  log.includes('[COMM ERROR]') ? 'text-red-400' :
                  log.includes('[DIRECTOR]') ? 'text-white' :
                  log.includes('[COMPLETE]') ? 'text-[#00ffcc]/60' :
                  log.includes('[COMM]') ? 'text-yellow-300' :
                  'text-[#00ffcc]'
                }>
                  {`> ${log}`}
                </div>
              ))}
            </div>
            <div className="absolute inset-0 p-5 font-mono text-[9px] text-[#00ffcc]/10 overflow-hidden leading-none z-0 tracking-tight select-none opacity-40">
              {[...Array(50)].map(() => (Math.random() > 0.5 ? '1' : '0')).join('')}
              {[...Array(50)].map(() => (Math.random() > 0.7 ? 'X' : 'O')).join('')}
              {Array(20).fill(' MATRIX_SCAN__'.repeat(10)).join('\n')}
            </div>
          </div>

        </div>
      </div>

      {/* OVERRIDE CONSOLE */}
      <div className="mt-6 pt-5 border-t-2 border-[#00ffcc]/40 flex items-center gap-5 relative bg-[#111] p-3 rounded-sm">
        <MessageSquare size={20} className="text-[#00ffcc]" />
        <span className="text-[#00ffcc] font-bold text-xl tracking-widest">{">"}</span>
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleCommand}
          className="flex-1 bg-transparent border-none outline-none text-white tracking-widest text-lg font-bold placeholder-[#00ffcc]/40"
          placeholder="ENTER DIRECTIVE PROTOCOL OR AWAIT VOICE INPUT..."
        />
        <Zap size={20} className="text-[#00ffcc] opacity-70" />
      </div>

    </div>
  );
}
