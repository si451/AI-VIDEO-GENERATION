"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Play, 
  MessageSquare, 
  Film, 
  Sparkles, 
  Copy, 
  Check, 
  Send, 
  RefreshCw, 
  Video, 
  Flame, 
  Award,
  Compass,
  Wand2,
  Tv,
  CheckCircle2,
  HelpCircle,
  ExternalLink
} from "lucide-react";

interface RunItem {
  id: string;
  title: string;
  duration: number;
  aspect_ratio: string;
  video_url: string | null;
  thumbnail_url: string | null;
  tags: string[];
  chapters: string[];
  frame_count: number;
}

interface FrameItem {
  frame_id: number;
  speaker: string;
  dialogue: string;
  camera_motion: string;
  visual_prompt: string;
  image_url: string | null;
  audio_url: string | null;
}

interface RunDetail {
  id: string;
  title: string;
  description: string;
  tags: string[];
  chapters: string[];
  duration: number;
  aspect_ratio: string;
  video_url: string | null;
  master_audio_url: string | null;
  frames: FrameItem[];
  character_bible: any;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const API_BASE = "http://localhost:8000";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"studio" | "dashboard" | "mychannel" | "competitors">("studio");
  const [stats, setStats] = useState({ total_videos: 0, total_runtime_seconds: 0, gpu_model: "RTX 2050", active_model: "DisneyPixar 768" });
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [runDetail, setRunDetail] = useState<RunDetail | null>(null);
  const [myChannel, setMyChannel] = useState<any>(null);
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "👋 **Welcome to WhimsyWand Tales Studio!** (@WhimsyWandTales)\n\nI am your AI Showrunner and YouTube Growth Director with full autonomous control of video production.\n\nWhenever you want to produce a video, simply tell me in chat or pick a prompt below! I will:\n1. 🔍 **Audit our Channel**: Inspect `@WhimsyWandTales` published history and core mascots (Pip the Dragon, Fern the Fairy, Barnaby Bear, Benny Bunny, Luna the Cloud).\n2. 📈 **Research Competitors**: Find viral videos with millions of views to steal winning hooks and keywords.\n3. ✍️ **Draft Situational Script**: Auto-calculate ~3s frame timing with 1:1 spoken child dialogue.\n4. 🎨 **Render 3D Pixar Visuals**: Locally generate high-res artwork on your RTX 2050 (zero API cost).\n5. 🎙️ **Voiceover & Subtitles**: Strictly child voices with ASS karaoke animations & NVENC master rendering!\n\nTell me what you'd like to create, or ask for a 30-minute Bedtime Story Omnibus!"
    }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Competitor data
  const [competitors, setCompetitors] = useState<any>(null);
  const [isCompLoading, setIsCompLoading] = useState(false);

  // Copy feedback
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stats`);
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.warn("Backend error:", e);
    }
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/runs`);
      if (res.ok) {
        const data: RunItem[] = await res.json();
        setRuns(data);
        if (data.length > 0 && !selectedRunId) {
          setSelectedRunId(data[0].id);
        }
      }
    } catch (e) {
      console.warn("Failed to fetch runs:", e);
    }
  };

  const fetchRunDetail = async (runId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/runs/${runId}`);
      if (res.ok) {
        const data: RunDetail = await res.json();
        setRunDetail(data);
      }
    } catch (e) {
      console.warn("Failed to fetch run detail:", e);
    }
  };

  const fetchMyChannel = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/my_channel`);
      if (res.ok) setMyChannel(await res.json());
    } catch (e) {
      console.warn("Failed to fetch channel data:", e);
    }
  };

  const fetchCompetitors = async () => {
    setIsCompLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/competitors?max_results=6`);
      if (res.ok) setCompetitors(await res.json());
    } catch (e) {
      console.warn("Failed to fetch competitors:", e);
    } finally {
      setIsCompLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchRuns();
    fetchMyChannel();
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      fetchRunDetail(selectedRunId);
    }
  }, [selectedRunId]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isChatLoading]);

  // Send message to agent
  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || chatInput;
    if (!text.trim() || isChatLoading) return;

    const newMessages = [...messages, { role: "user" as const, content: text }];
    setMessages(newMessages);
    if (!textToSend) setChatInput("");
    setIsChatLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessages([...newMessages, { role: "assistant", content: data.reply }]);
        fetchStats();
        fetchRuns();
      } else {
        setMessages([...newMessages, { role: "assistant", content: "❌ Error connecting to AI Showrunner Agent." }]);
      }
    } catch (e: any) {
      setMessages([...newMessages, { role: "assistant", content: `❌ Error: ${e.message}` }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Global Header */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-400 via-rose-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-rose-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-black text-lg tracking-tight bg-gradient-to-r from-amber-200 via-rose-200 to-indigo-200 bg-clip-text text-transparent">
                WhimsyWand Tales Studio
              </h1>
              <span className="text-[11px] font-mono bg-indigo-950/80 text-indigo-300 border border-indigo-700/50 px-2 py-0.5 rounded-full">
                @WhimsyWandTales
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Tiny heroes. Magical worlds. Big-hearted endings.</p>
          </div>
        </div>

        {/* Live Badges & Navigation */}
        <div className="flex items-center space-x-3">
          <div className="hidden lg:flex items-center space-x-2 bg-slate-800/80 border border-slate-700/60 rounded-full px-3 py-1 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-300 font-medium">RTX 2050 (4GB)</span>
            <span className="text-slate-500">•</span>
            <span className="text-amber-300 font-medium">Child Voices Only</span>
          </div>

          <div className="flex items-center space-x-1.5 bg-indigo-950/60 border border-indigo-800/50 rounded-full px-3 py-1 text-xs text-indigo-200 font-semibold">
            <Video className="w-3.5 h-3.5 text-indigo-400" />
            <span>{stats.total_videos} Videos Ready</span>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 bg-slate-800/90 p-1 rounded-xl border border-slate-700/50">
            <button
              onClick={() => setActiveTab("studio")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "studio" ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              🎬 Studio (Chat & Video)
            </button>
            <button
              onClick={() => setActiveTab("mychannel")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "mychannel" ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              🏰 Our Channel (WhimsyWand)
            </button>
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "dashboard" ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              🎞️ All Runs ({runs.length})
            </button>
            <button
              onClick={() => { setActiveTab("competitors"); if (!competitors) fetchCompetitors(); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "competitors" ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              📈 Competitor Spy
            </button>
          </nav>
        </div>
      </header>

      {/* Main Studio Split Screen */}
      <main className="flex-1 overflow-hidden">
        {/* ============================================================== */}
        {/* TAB 1: STUDIO (LEFT CHAT & ONE-CLICK BAR, RIGHT LIVE VIDEO)     */}
        {/* ============================================================== */}
        {activeTab === "studio" && (
          <div className="h-[calc(100vh-62px)] flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x divide-slate-800">
            {/* ------------------------------------------------------------ */}
            {/* LEFT PANE: AGENT CHAT & ONE-CLICK WORKFLOW (45% Width)       */}
            {/* ------------------------------------------------------------ */}
            <div className="w-full md:w-[45%] h-full flex flex-col bg-slate-900/40">
              {/* Chat Header */}
              <div className="px-5 py-2.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
                <div className="flex items-center space-x-2">
                  <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30">
                    <Wand2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-xs font-extrabold text-slate-100">AI Showrunner Agent</h2>
                    <p className="text-[10px] text-emerald-400">Targeting Viral Growth for @WhimsyWandTales</p>
                  </div>
                </div>

                <button 
                  onClick={() => setMessages([{ role: "assistant", content: "Chat cleared! How can I help you write or render our next fairy tale episode?" }])}
                  className="text-[11px] text-slate-400 hover:text-slate-200 px-2 py-0.5 rounded hover:bg-slate-800 transition"
                >
                  Clear Chat
                </button>
              </div>

              {/* Quick Action Suggestion Chips */}
              <div className="px-4 py-2 border-b border-slate-800/80 bg-slate-900/30 flex space-x-2 overflow-x-auto text-[11px] no-scrollbar">
                <button
                  onClick={() => handleSendMessage("Inspect our channel @WhimsyWandTales and compare our 8 published videos against top viral competitor fairy tales.")}
                  className="whitespace-nowrap px-2.5 py-1 rounded-full bg-indigo-950/70 hover:bg-indigo-900 text-indigo-300 border border-indigo-800/60 transition flex items-center space-x-1"
                >
                  <Award className="w-3 h-3 text-amber-400" />
                  <span>Audit WhimsyWand vs Competitors</span>
                </button>
                <button
                  onClick={() => handleSendMessage("Analyze our channel @WhimsyWandTales and research viral competitor hits, then outline a 30-minute Bedtime Story Omnibus compilation (5 sequential chapters) starring Pip the Dragon, Fern the Fairy, Barnaby Bear, Luna the Cloud, and Benny Bunny.")}
                  className="whitespace-nowrap px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/40 transition flex items-center space-x-1"
                >
                  <Sparkles className="w-3 h-3 text-amber-400" />
                  <span>30-Min Bedtime Omnibus</span>
                </button>
                <button
                  onClick={() => handleSendMessage("Produce an autonomous 9:16 Short for WhimsyWand Tales starring Pip the Baby Dragon, using strict child voices and ~3s frames.")}
                  className="whitespace-nowrap px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/80 transition"
                >
                  🐉 Auto 9:16 Short (Pip)
                </button>
                <button
                  onClick={() => handleSendMessage("List all completed video runs and report their status.")}
                  className="whitespace-nowrap px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/80 transition"
                >
                  📋 List All Runs
                </button>
              </div>

              {/* Chat Message Stream */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-sm ${
                        msg.role === "user"
                          ? "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-br-none"
                          : "bg-slate-800/90 text-slate-200 border border-slate-700/70 rounded-bl-none prose prose-invert prose-xs max-w-none"
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  </div>
                ))}
                {isChatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800/90 border border-slate-700/70 rounded-2xl rounded-bl-none px-4 py-3 text-xs text-slate-400 flex items-center space-x-2">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                      <span>AI Showrunner is thinking, planning, and executing tools...</span>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Direct Agent Chat Input */}
              <div className="p-4 bg-slate-900 border-t border-slate-800">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-center space-x-2"
                >
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Talk to AI Showrunner (e.g. 'Analyze our channel and produce a 30-minute episode compilation')..."
                    className="flex-1 bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition shadow-inner"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim() || isChatLoading}
                    className="bg-gradient-to-r from-amber-500 to-indigo-600 hover:from-amber-400 hover:to-indigo-500 disabled:opacity-40 text-slate-950 font-bold rounded-xl px-4 py-3 transition flex items-center justify-center space-x-1 shadow-md shadow-indigo-600/20"
                  >
                    <Send className="w-4 h-4 text-white" />
                  </button>
                </form>
              </div>
            </div>

            {/* ------------------------------------------------------------ */}
            {/* RIGHT PANE: GENERATED VIDEOS, IMAGES & METADATA (55% Width)   */}
            {/* ------------------------------------------------------------ */}
            <div className="w-full md:w-[55%] h-full flex flex-col bg-slate-950 overflow-y-auto">
              {/* Top Bar: Selector & Duration */}
              <div className="p-3.5 border-b border-slate-800 bg-slate-900/60 sticky top-0 z-20 backdrop-blur flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <Film className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Active Run:</span>
                  <select
                    value={selectedRunId}
                    onChange={(e) => setSelectedRunId(e.target.value)}
                    className="bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 font-medium focus:outline-none focus:border-indigo-500 max-w-[280px] truncate"
                  >
                    {runs.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.title} ({r.duration}s • {r.aspect_ratio || "16:9"})
                      </option>
                    ))}
                  </select>
                </div>

                {runDetail && (
                  <div className="flex items-center space-x-2">
                    <span className={`text-[10px] font-black px-2.5 py-0.5 rounded-full ${
                      runDetail.aspect_ratio === "9:16" ? "bg-amber-500/20 text-amber-300 border border-amber-500/40" : "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40"
                    }`}>
                      {runDetail.aspect_ratio === "9:16" ? "9:16 Short" : "16:9 Long"}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      ⏱️ {runDetail.duration.toFixed(1)}s
                    </span>
                  </div>
                )}
              </div>

              {/* Master Video Display */}
              <div className="p-5 flex flex-col items-center justify-center bg-slate-900/20 border-b border-slate-800">
                {runDetail?.video_url ? (
                  <div className={`w-full flex justify-center ${runDetail.aspect_ratio === "9:16" ? "max-w-xs" : "max-w-xl"}`}>
                    <div className="relative rounded-2xl overflow-hidden border border-slate-700/80 shadow-2xl bg-black w-full">
                      <video
                        src={`${API_BASE}${runDetail.video_url}`}
                        controls
                        className="w-full h-auto max-h-[440px] object-contain rounded-2xl"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    <Film className="w-10 h-10 mx-auto mb-2 opacity-40" />
                    <p className="text-xs">No video selected yet</p>
                  </div>
                )}
              </div>

              {/* YouTube Metadata Package (Title, Description, Tags) */}
              {runDetail && (
                <div className="p-4 border-b border-slate-800 space-y-3.5">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Viral YouTube Title</span>
                      <button
                        onClick={() => copyToClipboard(runDetail.title, "title")}
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
                      >
                        {copiedKey === "title" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedKey === "title" ? "Copied!" : "Copy Title"}</span>
                      </button>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-bold text-slate-100">
                      {runDetail.title}
                    </div>
                  </div>

                  {/* Description & Chapters */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Description & Timestamps</span>
                      <button
                        onClick={() => copyToClipboard(runDetail.description, "desc")}
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
                      >
                        {copiedKey === "desc" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedKey === "desc" ? "Copied!" : "Copy Description"}</span>
                      </button>
                    </div>
                    <textarea
                      readOnly
                      value={runDetail.description}
                      rows={3}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-[11px] text-slate-300 font-mono resize-none focus:outline-none"
                    />
                  </div>

                  {/* Tags */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Viral SEO Tags</span>
                      <button
                        onClick={() => copyToClipboard(runDetail.tags.join(", "), "tags")}
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
                      >
                        {copiedKey === "tags" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedKey === "tags" ? "Copied!" : "Copy Tags"}</span>
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {runDetail.tags.map((tag, i) => (
                        <span key={i} className="text-[10px] bg-slate-900 border border-slate-800 text-indigo-300 px-2 py-0.5 rounded-md">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Frame-by-Frame Situational Storyboard (~3s each) */}
              {runDetail && (
                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-slate-200">Situational Frame Storyboard</h3>
                      <p className="text-[11px] text-slate-400">~3.0s per frame, matching spoken child dialogue 1:1</p>
                    </div>
                    <span className="text-[11px] font-bold bg-slate-800 px-2 py-0.5 rounded-lg text-slate-300 border border-slate-700">
                      {runDetail.frames.length} Unique Frames
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {runDetail.frames.map((frame) => (
                      <div
                        key={frame.frame_id}
                        className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm flex flex-col hover:border-slate-700 transition"
                      >
                        {/* Frame Image */}
                        <div className="relative bg-slate-950 aspect-[9/16] sm:aspect-video flex items-center justify-center overflow-hidden">
                          {frame.image_url ? (
                            <img
                              src={`${API_BASE}${frame.image_url}`}
                              alt={`Frame ${frame.frame_id}`}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="text-xs text-slate-500">Generating frame...</div>
                          )}
                          <span className="absolute top-2 left-2 bg-black/70 backdrop-blur px-1.5 py-0.5 rounded text-[9px] font-bold text-amber-300">
                            Frame {frame.frame_id < 10 ? `0${frame.frame_id}` : frame.frame_id}
                          </span>
                          <span className="absolute top-2 right-2 bg-black/70 backdrop-blur px-1 py-0.5 rounded text-[9px] text-slate-300 font-mono">
                            {frame.camera_motion}
                          </span>
                        </div>

                        {/* Dialogue & Speaker */}
                        <div className="p-2.5 flex-1 flex flex-col justify-between space-y-1.5">
                          <div>
                            <div className="text-[10px] font-bold text-indigo-400 mb-0.5">
                              🗣️ {frame.speaker}
                            </div>
                            <p className="text-[11px] text-slate-200 line-clamp-2 leading-snug">
                              &ldquo;{frame.dialogue}&rdquo;
                            </p>
                          </div>

                          {frame.audio_url && (
                            <div className="pt-0.5">
                              <audio
                                src={`${API_BASE}${frame.audio_url}`}
                                controls
                                className="w-full h-6 text-xs"
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 2: MY CHANNEL PROFILE (WHIMSYWAND TALES)                   */}
        {/* ============================================================== */}
        {activeTab === "mychannel" && myChannel && (
          <div className="p-8 max-w-6xl mx-auto space-y-6 overflow-y-auto">
            {/* Banner Card */}
            <div className="bg-gradient-to-r from-indigo-950 via-slate-900 to-amber-950 border border-slate-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden">
              <div className="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-6">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-amber-500 to-indigo-600 flex items-center justify-center text-4xl shadow-xl shadow-rose-500/20">
                  🐉
                </div>
                <div className="space-y-1 text-center md:text-left flex-1">
                  <div className="flex items-center justify-center md:justify-start space-x-3">
                    <h2 className="text-2xl font-black text-white">{myChannel.channel_name}</h2>
                    <a
                      href={myChannel.channel_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs bg-red-600 hover:bg-red-500 text-white font-bold px-3 py-1 rounded-full flex items-center space-x-1"
                    >
                      <Tv className="w-3.5 h-3.5" />
                      <span>Visit Channel</span>
                      <ExternalLink className="w-3 h-3 ml-0.5" />
                    </a>
                  </div>
                  <p className="text-amber-300 font-semibold text-sm">&ldquo;{myChannel.tagline}&rdquo;</p>
                  <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">{myChannel.description}</p>
                </div>
              </div>
            </div>

            {/* Core Mascots & Characters */}
            <div className="space-y-3">
              <h3 className="text-base font-extrabold text-slate-100 flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span>Our Tiny Heroes & Mascots</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {myChannel.core_characters?.map((c: any, i: number) => (
                  <div key={i} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-sm text-amber-300">{c.name}</h4>
                      <span className="text-[10px] bg-slate-800 text-indigo-300 px-2 py-0.5 rounded-full capitalize">
                        {c.role}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300 leading-relaxed bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                      {c.visual_anchor}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      <span className="font-semibold text-slate-300">Personality:</span> {c.personality}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Published Video Audit */}
            <div className="space-y-3">
              <h3 className="text-base font-extrabold text-slate-100">
                Published Video Audit (Agent Memory)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {myChannel.published_video_audit?.map((vid: any, i: number) => (
                  <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold text-slate-200">{vid.title}</p>
                      <p className="text-[10px] text-indigo-400">Character: {vid.character}</p>
                    </div>
                    <span className="text-[10px] bg-slate-800 text-emerald-400 px-2 py-0.5 rounded">
                      Audited
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 3: ALL RUNS GALLERY                                        */}
        {/* ============================================================== */}
        {activeTab === "dashboard" && (
          <div className="p-8 max-w-7xl mx-auto space-y-6 overflow-y-auto">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-extrabold text-slate-100">All Production Runs</h2>
                <p className="text-xs text-slate-400">Stored in isolated folders under output/runs/</p>
              </div>
              <button
                onClick={() => { fetchStats(); fetchRuns(); }}
                className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs px-3 py-1.5 rounded-lg border border-slate-700 flex items-center space-x-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Refresh</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {runs.map((r) => (
                <div
                  key={r.id}
                  className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg hover:border-indigo-500/50 transition flex flex-col"
                >
                  <div className="relative aspect-video bg-slate-950 flex items-center justify-center">
                    {r.thumbnail_url ? (
                      <img src={`${API_BASE}${r.thumbnail_url}`} alt={r.title} className="w-full h-full object-cover" />
                    ) : (
                      <Film className="w-10 h-10 text-slate-700" />
                    )}
                    <span className="absolute bottom-2 right-2 bg-black/80 backdrop-blur text-white text-xs font-mono px-2 py-0.5 rounded">
                      ⏱️ {r.duration.toFixed(1)}s
                    </span>
                    <span className="absolute top-2 left-2 bg-indigo-600 text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase">
                      {r.aspect_ratio || "16:9"}
                    </span>
                  </div>

                  <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                    <h3 className="font-bold text-xs text-slate-100 line-clamp-2 leading-snug">{r.title}</h3>
                    <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                      <span className="text-[11px] text-slate-400">{r.frame_count} frames</span>
                      <button
                        onClick={() => {
                          setSelectedRunId(r.id);
                          setActiveTab("studio");
                        }}
                        className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center space-x-1"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>Watch in Studio</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 4: COMPETITOR SPY & VIRAL FORMULAS                         */}
        {/* ============================================================== */}
        {activeTab === "competitors" && (
          <div className="p-8 max-w-6xl mx-auto space-y-6 overflow-y-auto">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-extrabold text-slate-100">Competitor Viral Hits & Formulas</h2>
                <p className="text-xs text-slate-400">Million-view kids bedtime and cartoon stories scraped via YouTube Data API</p>
              </div>
              <button
                disabled={isCompLoading}
                onClick={fetchCompetitors}
                className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3 py-1.5 rounded-xl flex items-center space-x-1"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isCompLoading ? "animate-spin" : ""}`} />
                <span>Refresh Competitors</span>
              </button>
            </div>

            {competitors && (
              <div className="space-y-5">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
                  <div className="p-3.5 border-b border-slate-800 font-bold text-xs text-slate-200">
                    🏆 Million-View Benchmark Videos
                  </div>
                  <div className="divide-y divide-slate-800">
                    {competitors.top_videos?.map((vid: any, idx: number) => (
                      <div key={idx} className="p-3.5 flex items-center justify-between hover:bg-slate-850">
                        <div>
                          <p className="text-xs font-semibold text-slate-100">#{idx + 1} {vid.title}</p>
                          <p className="text-[11px] text-slate-400">{vid.channel}</p>
                        </div>
                        <span className="text-xs font-mono font-bold text-amber-400">
                          {vid.views?.toLocaleString()} views
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
                  <h3 className="text-xs font-bold text-slate-200 mb-2">🔥 Viral Tags to Copy</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {competitors.top_keywords?.map((tag: string, i: number) => (
                      <span key={i} className="bg-slate-950 border border-slate-800 px-2.5 py-1 rounded-lg text-xs text-indigo-300">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
