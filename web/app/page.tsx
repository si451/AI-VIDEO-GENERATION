"use client";

import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
  ExternalLink,
  ChevronRight,
  BookOpen,
  Volume2
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
      content: `👋 **Welcome to WhimsyWand Tales Studio!** (@WhimsyWandTales)

I am your **AI Showrunner & YouTube Growth Director** with full autonomous control of video generation.

Whenever you want to produce a video, simply type your vision or choose a quick prompt below. I will:
1. 🔍 **Audit our Channel**: Verify [@WhimsyWandTales](https://www.youtube.com/@WhimsyWandTales) mascots (*Pip the Dragon, Fern the Fairy, Barnaby Bear, Luna the Cloud, Benny Bunny*) and review published videos to prevent duplicates.
2. 📈 **Scan Competitors**: Scrape viral hits (>1M views) to identify high-retention hooks and curiosity-gap titles.
3. ✍️ **Draft Situational Script**: Auto-calculate ~3s frame timing with 1:1 spoken child dialogue.
4. 🎨 **Render 3D Pixar Visuals**: Locally synthesize high-res artwork on your RTX 2050 (zero API cost).
5. 🎙️ **Voiceover & Subtitles**: Strictly sweet child voices with animated ASS karaoke subtitles and NVENC master rendering!

Tell me what you'd like to create, or ask for a **30-minute Bedtime Story Omnibus**!`
    }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [loadingElapsed, setLoadingElapsed] = useState(0);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Load chat history from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("whimsywand_chat_history");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
        }
      }
    } catch (e) {
      console.warn("Failed to load chat history:", e);
    }
  }, []);

  // Persist chat history to localStorage
  useEffect(() => {
    try {
      if (messages.length > 1) {
        localStorage.setItem("whimsywand_chat_history", JSON.stringify(messages));
      }
    } catch (e) {
      console.warn("Failed to persist chat history:", e);
    }
  }, [messages]);

  // Loading elapsed timer
  useEffect(() => {
    let interval: any = null;
    if (isChatLoading) {
      setLoadingElapsed(0);
      interval = setInterval(() => {
        setLoadingElapsed((prev) => prev + 1);
      }, 1000);
    } else {
      setLoadingElapsed(0);
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isChatLoading]);

  const handleClearChat = () => {
    const initialMsg: ChatMessage[] = [{
      role: "assistant",
      content: "Chat cleared! How can I help you write or render our next fairy tale episode?"
    }];
    setMessages(initialMsg);
    try {
      localStorage.removeItem("whimsywand_chat_history");
    } catch (e) {}
  };

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
    <div className="min-h-screen bg-[#FAF9F5] text-stone-800 flex flex-col font-sans selection:bg-amber-200 selection:text-stone-900">
      {/* Top Global Header - Clean Calm Cream Theme */}
      <header className="border-b border-stone-200/80 bg-white/90 backdrop-blur sticky top-0 z-50 px-6 py-3 flex items-center justify-between shadow-xs">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-rose-400 to-amber-600 flex items-center justify-center shadow-sm">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-extrabold text-base tracking-tight text-stone-900">
                WhimsyWand Tales Studio
              </h1>
              <span className="text-[11px] font-mono bg-amber-50 text-amber-800 border border-amber-200/80 px-2 py-0.5 rounded-full font-medium">
                @WhimsyWandTales
              </span>
            </div>
            <p className="text-[11px] text-stone-500 font-medium">Tiny heroes. Magical worlds. Big-hearted endings.</p>
          </div>
        </div>

        {/* Live Badges & Navigation */}
        <div className="flex items-center space-x-3">
          <div className="hidden lg:flex items-center space-x-2 bg-stone-50 border border-stone-200/80 rounded-full px-3 py-1 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-stone-700 font-medium">RTX 2050 (4GB)</span>
            <span className="text-stone-300">•</span>
            <span className="text-amber-800 font-semibold bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/60">Child Voices Only</span>
          </div>

          <div className="flex items-center space-x-1.5 bg-stone-100/90 border border-stone-200 rounded-full px-3 py-1 text-xs text-stone-700 font-semibold">
            <Video className="w-3.5 h-3.5 text-stone-500" />
            <span>{stats.total_videos} Videos Ready</span>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 bg-stone-100/80 p-1 rounded-xl border border-stone-200/70">
            <button
              onClick={() => setActiveTab("studio")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "studio" ? "bg-white text-stone-900 shadow-xs border border-stone-200/80" : "text-stone-600 hover:text-stone-900"
              }`}
            >
              🎬 Studio (Chat & Video)
            </button>
            <button
              onClick={() => setActiveTab("mychannel")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "mychannel" ? "bg-white text-stone-900 shadow-xs border border-stone-200/80" : "text-stone-600 hover:text-stone-900"
              }`}
            >
              🏰 Our Channel
            </button>
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "dashboard" ? "bg-white text-stone-900 shadow-xs border border-stone-200/80" : "text-stone-600 hover:text-stone-900"
              }`}
            >
              🎞️ All Runs ({runs.length})
            </button>
            <button
              onClick={() => { setActiveTab("competitors"); if (!competitors) fetchCompetitors(); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "competitors" ? "bg-white text-stone-900 shadow-xs border border-stone-200/80" : "text-stone-600 hover:text-stone-900"
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
        {/* TAB 1: STUDIO (LEFT CHAT, RIGHT MASTER VIDEO & STORYBOARD)      */}
        {/* ============================================================== */}
        {activeTab === "studio" && (
          <div className="h-[calc(100vh-62px)] flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x divide-stone-200">
            {/* ------------------------------------------------------------ */}
            {/* LEFT PANE: AGENT CHAT (45% Width)                            */}
            {/* ------------------------------------------------------------ */}
            <div className="w-full md:w-[45%] h-full flex flex-col bg-[#FDFCF7]">
              {/* Chat Header */}
              <div className="px-5 py-2.5 border-b border-stone-200 bg-white flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-200">
                    <Wand2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-xs font-bold text-stone-900">AI Showrunner Agent</h2>
                    <p className="text-[10px] text-emerald-700 font-medium">Autonomous Producer for @WhimsyWandTales</p>
                  </div>
                </div>

                <button 
                  onClick={handleClearChat}
                  className="text-[11px] text-stone-500 hover:text-stone-800 px-2.5 py-1 rounded-md hover:bg-stone-100 transition border border-stone-200/60"
                >
                  Clear Chat
                </button>
              </div>

              {/* Quick Action Suggestion Chips */}
              <div className="px-4 py-2 border-b border-stone-200/70 bg-stone-50/70 flex space-x-2 overflow-x-auto text-[11px] no-scrollbar">
                <button
                  onClick={() => handleSendMessage("Inspect our channel @WhimsyWandTales and compare our 8 published videos against top viral competitor fairy tales.")}
                  className="whitespace-nowrap px-3 py-1 rounded-full bg-white hover:bg-stone-100 text-stone-700 border border-stone-200 shadow-xs transition flex items-center space-x-1.5 font-medium"
                >
                  <Award className="w-3.5 h-3.5 text-amber-600" />
                  <span>Audit WhimsyWand vs Competitors</span>
                </button>
                <button
                  onClick={() => handleSendMessage("Analyze our channel @WhimsyWandTales and research viral competitor hits, then outline a 30-minute Bedtime Story Omnibus compilation (5 sequential chapters) starring Pip the Dragon, Fern the Fairy, Barnaby Bear, Luna the Cloud, and Benny Bunny.")}
                  className="whitespace-nowrap px-3 py-1 rounded-full bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 transition flex items-center space-x-1.5 font-semibold"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                  <span>30-Min Bedtime Omnibus</span>
                </button>
                <button
                  onClick={() => handleSendMessage("Produce an autonomous 9:16 Short for WhimsyWand Tales starring Pip the Baby Dragon, using strict child voices and ~3s frames.")}
                  className="whitespace-nowrap px-3 py-1 rounded-full bg-white hover:bg-stone-100 text-stone-700 border border-stone-200 shadow-xs transition font-medium"
                >
                  🐉 Auto 9:16 Short (Pip)
                </button>
                <button
                  onClick={() => handleSendMessage("List all completed video runs and report their status.")}
                  className="whitespace-nowrap px-3 py-1 rounded-full bg-white hover:bg-stone-100 text-stone-700 border border-stone-200 shadow-xs transition font-medium"
                >
                  📋 List All Runs
                </button>
              </div>

              {/* Chat Message Stream - Clean Formatted Markdown */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[88%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-xs ${
                        msg.role === "user"
                          ? "bg-stone-900 text-white rounded-br-none"
                          : "bg-white text-stone-800 border border-stone-200/90 rounded-bl-none shadow-sm"
                      }`}
                    >
                      {msg.role === "user" ? (
                        <div className="whitespace-pre-wrap font-medium">{msg.content}</div>
                      ) : (
                        <div className="prose prose-stone prose-xs max-w-none break-words">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              h1: ({ node, ...props }) => <h1 className="text-sm font-extrabold text-stone-900 mt-3 mb-1.5 pb-1 border-b border-stone-200" {...props} />,
                              h2: ({ node, ...props }) => <h2 className="text-xs font-bold text-stone-900 mt-2.5 mb-1" {...props} />,
                              h3: ({ node, ...props }) => <h3 className="text-xs font-bold text-amber-800 mt-2 mb-0.5" {...props} />,
                              p: ({ node, ...props }) => <p className="mb-2 last:mb-0 leading-relaxed text-stone-700" {...props} />,
                              strong: ({ node, ...props }) => <strong className="font-semibold text-stone-900" {...props} />,
                              ul: ({ node, ...props }) => <ul className="list-disc list-inside space-y-1 my-1.5 text-stone-700 pl-1" {...props} />,
                              ol: ({ node, ...props }) => <ol className="list-decimal list-inside space-y-1 my-1.5 text-stone-700 pl-1" {...props} />,
                              li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
                              blockquote: ({ node, ...props }) => <blockquote className="border-l-2 border-amber-500 pl-3 my-2 italic text-stone-600 bg-amber-50/50 py-1 rounded-r" {...props} />,
                              code: ({ node, inline, ...props }: any) => inline ? (
                                <code className="bg-stone-100 text-amber-900 text-[11px] font-mono px-1.5 py-0.5 rounded border border-stone-200 font-semibold" {...props} />
                              ) : (
                                <code className="block bg-stone-900 text-stone-100 p-2.5 rounded-lg text-[11px] font-mono overflow-x-auto my-2" {...props} />
                              ),
                              table: ({ node, ...props }) => (
                                <div className="my-2.5 overflow-x-auto rounded-lg border border-stone-200 shadow-xs">
                                  <table className="min-w-full divide-y divide-stone-200 text-[11px]" {...props} />
                                </div>
                              ),
                              thead: ({ node, ...props }) => <thead className="bg-stone-100/90 font-bold text-stone-800" {...props} />,
                              th: ({ node, ...props }) => <th className="px-3 py-1.5 text-left font-semibold text-stone-800" {...props} />,
                              tbody: ({ node, ...props }) => <tbody className="divide-y divide-stone-100 bg-white" {...props} />,
                              td: ({ node, ...props }) => <td className="px-3 py-1.5 text-stone-700" {...props} />,
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isChatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-stone-200 rounded-2xl rounded-bl-none p-4 text-xs text-stone-700 shadow-sm max-w-[92%] space-y-3">
                      <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                        <div className="flex items-center space-x-2">
                          <RefreshCw className="w-4 h-4 animate-spin text-amber-600" />
                          <span className="font-bold text-stone-900">AI Showrunner Pipeline In Progress</span>
                        </div>
                        <span className="font-mono text-[11px] bg-amber-50 text-amber-900 border border-amber-200 px-2 py-0.5 rounded-full font-semibold">
                          ⏱️ {loadingElapsed}s elapsed
                        </span>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center space-x-2.5 text-stone-700">
                          <span className="w-4 h-4 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-[10px] font-bold">✓</span>
                          <span className="font-medium">1. Channel & Mascot Audit (@WhimsyWandTales memory verified)</span>
                        </div>

                        <div className="flex items-center space-x-2.5 text-stone-700">
                          <span className={`w-4 h-4 rounded-full ${loadingElapsed >= 2 ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700 animate-pulse"} flex items-center justify-center text-[10px] font-bold`}>
                            {loadingElapsed >= 2 ? "✓" : "•"}
                          </span>
                          <span className="font-medium">2. Competitor Viral Scan (>1M views analyzed for curiosity hooks)</span>
                        </div>

                        <div className="flex items-center space-x-2.5 text-stone-700">
                          <span className={`w-4 h-4 rounded-full ${loadingElapsed >= 6 ? "bg-emerald-100 text-emerald-700" : loadingElapsed >= 2 ? "bg-amber-100 text-amber-700 animate-pulse" : "bg-stone-100 text-stone-400"} flex items-center justify-center text-[10px] font-bold`}>
                            {loadingElapsed >= 6 ? "✓" : "•"}
                          </span>
                          <span className="font-medium">3. Script & Frame Breakdown (~3s pacing + persistent character anchors)</span>
                        </div>

                        <div className="flex items-center space-x-2.5 text-stone-700">
                          <span className={`w-4 h-4 rounded-full ${loadingElapsed >= 10 ? "bg-amber-100 text-amber-700 animate-pulse" : "bg-stone-100 text-stone-400"} flex items-center justify-center text-[10px] font-bold`}>
                            •
                          </span>
                          <span className="font-medium">4. 3D Disney Pixar Rendering (Local RTX 2050 Diffusers fp16)</span>
                        </div>

                        <div className="flex items-center space-x-2.5 text-stone-500">
                          <span className="w-4 h-4 rounded-full bg-stone-100 text-stone-400 flex items-center justify-center text-[10px] font-bold">•</span>
                          <span>5. Voiceover & Karaoke Subtitles (Strict child neural voices)</span>
                        </div>

                        <div className="flex items-center space-x-2.5 text-stone-500">
                          <span className="w-4 h-4 rounded-full bg-stone-100 text-stone-400 flex items-center justify-center text-[10px] font-bold">•</span>
                          <span>6. Master NVENC Assembly & YouTube SEO Metadata Package</span>
                        </div>
                      </div>

                      <div className="pt-2 border-t border-stone-100 text-[10px] text-stone-500 flex items-center justify-between">
                        <span>Estimated completion: ~30-45s for Shorts • ~3-4m per Long Chapter</span>
                        <span className="text-amber-800 font-semibold">Running locally on RTX 2050</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Direct Agent Chat Input */}
              <div className="p-3.5 bg-white border-t border-stone-200">
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
                    placeholder="Talk to AI Showrunner (e.g. 'Produce a 16:9 bedtime story chapter about Barnaby Bear')..."
                    className="flex-1 bg-stone-50 border border-stone-300 rounded-xl px-4 py-2.5 text-xs text-stone-900 placeholder-stone-400 focus:outline-none focus:border-amber-500 focus:bg-white transition shadow-inner"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim() || isChatLoading}
                    className="bg-amber-600 hover:bg-amber-500 disabled:opacity-40 text-white font-bold rounded-xl px-4 py-2.5 transition flex items-center justify-center space-x-1 shadow-sm"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </div>

            {/* ------------------------------------------------------------ */}
            {/* RIGHT PANE: GENERATED VIDEOS, IMAGES & METADATA (55% Width)   */}
            {/* ------------------------------------------------------------ */}
            <div className="w-full md:w-[55%] h-full flex flex-col bg-white overflow-y-auto">
              {/* Top Bar: Selector & Duration */}
              <div className="p-3.5 border-b border-stone-200 bg-[#FAF9F5]/90 sticky top-0 z-20 backdrop-blur flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <Film className="w-4 h-4 text-amber-600" />
                  <span className="text-xs font-bold uppercase tracking-wider text-stone-500">Active Run:</span>
                  <select
                    value={selectedRunId}
                    onChange={(e) => setSelectedRunId(e.target.value)}
                    className="bg-white border border-stone-300 rounded-lg px-2.5 py-1 text-xs text-stone-800 font-medium focus:outline-none focus:border-amber-500 max-w-[280px] truncate shadow-xs"
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
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                      runDetail.aspect_ratio === "9:16" ? "bg-amber-100 text-amber-800 border border-amber-300/60" : "bg-stone-100 text-stone-800 border border-stone-300/60"
                    }`}>
                      {runDetail.aspect_ratio === "9:16" ? "9:16 Short" : "16:9 Long"}
                    </span>
                    <span className="text-xs text-stone-600 font-mono font-medium">
                      ⏱️ {runDetail.duration.toFixed(1)}s
                    </span>
                  </div>
                )}
              </div>

              {/* Master Video Display */}
              <div className="p-6 flex flex-col items-center justify-center bg-[#FAF9F5] border-b border-stone-200">
                {runDetail?.video_url ? (
                  <div className={`w-full flex justify-center ${runDetail.aspect_ratio === "9:16" ? "max-w-xs" : "max-w-xl"}`}>
                    <div className="relative rounded-2xl overflow-hidden border border-stone-300 shadow-lg bg-black w-full">
                      <video
                        src={`${API_BASE}${runDetail.video_url}`}
                        controls
                        className="w-full h-auto max-h-[440px] object-contain rounded-2xl"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-stone-400">
                    <Film className="w-10 h-10 mx-auto mb-2 opacity-30" />
                    <p className="text-xs font-medium">No video selected yet</p>
                  </div>
                )}
              </div>

              {/* YouTube Metadata Package (Title, Description, Tags) */}
              {runDetail && (
                <div className="p-5 border-b border-stone-200 space-y-4 bg-white">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Viral YouTube Title</span>
                      <button
                        onClick={() => copyToClipboard(runDetail.title, "title")}
                        className="text-xs text-amber-700 hover:text-amber-800 font-medium flex items-center space-x-1"
                      >
                        {copiedKey === "title" ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedKey === "title" ? "Copied!" : "Copy Title"}</span>
                      </button>
                    </div>
                    <div className="bg-[#FAF9F5] border border-stone-200 rounded-xl px-3.5 py-2.5 text-xs font-bold text-stone-900 leading-snug">
                      {runDetail.title}
                    </div>
                  </div>

                  {/* Description & Chapters */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Description & Timestamps</span>
                      <button
                        onClick={() => copyToClipboard(runDetail.description, "desc")}
                        className="text-xs text-amber-700 hover:text-amber-800 font-medium flex items-center space-x-1"
                      >
                        {copiedKey === "desc" ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedKey === "desc" ? "Copied!" : "Copy Description"}</span>
                      </button>
                    </div>
                    <textarea
                      readOnly
                      value={runDetail.description}
                      rows={3}
                      className="w-full bg-[#FAF9F5] border border-stone-200 rounded-xl p-3 text-[11px] text-stone-700 font-mono resize-none focus:outline-none leading-relaxed"
                    />
                  </div>

                  {/* Tags */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Viral SEO Tags</span>
                      <button
                        onClick={() => copyToClipboard(runDetail.tags.join(", "), "tags")}
                        className="text-xs text-amber-700 hover:text-amber-800 font-medium flex items-center space-x-1"
                      >
                        {copiedKey === "tags" ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedKey === "tags" ? "Copied!" : "Copy Tags"}</span>
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {runDetail.tags.map((tag, i) => (
                        <span key={i} className="text-[11px] bg-stone-100 border border-stone-200/80 text-stone-700 px-2.5 py-0.5 rounded-md font-medium">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Frame-by-Frame Situational Storyboard (~3s each) */}
              {runDetail && (
                <div className="p-5 space-y-3.5 bg-[#FAF9F5]/50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-stone-900">Situational Frame Storyboard</h3>
                      <p className="text-[11px] text-stone-500">~3.0s per frame, matching spoken child dialogue 1:1</p>
                    </div>
                    <span className="text-[11px] font-bold bg-white px-2.5 py-1 rounded-lg text-stone-700 border border-stone-200 shadow-xs">
                      {runDetail.frames.length} Unique Frames
                    </span>
                  </div>

                  <div className="space-y-3">
                    {runDetail.frames.map((frame) => (
                      <div
                        key={frame.frame_id}
                        className="bg-white border border-stone-200 rounded-xl p-3.5 shadow-xs flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-4 items-start"
                      >
                        {/* Frame Image Thumbnail */}
                        <div className="w-full md:w-36 h-28 rounded-lg overflow-hidden bg-stone-100 flex-shrink-0 border border-stone-200 relative">
                          {frame.image_url ? (
                            <img
                              src={`${API_BASE}${frame.image_url}`}
                              alt={`Frame ${frame.frame_id}`}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-stone-400 text-xs">
                              Rendering...
                            </div>
                          )}
                          <span className="absolute bottom-1 right-1 bg-black/70 text-white font-mono text-[9px] px-1.5 py-0.5 rounded">
                            Frame {frame.frame_id.toString().padStart(2, "0")}
                          </span>
                        </div>

                        {/* Dialogue & Director Visual Prompt */}
                        <div className="flex-1 space-y-1.5 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                              {frame.speaker}
                            </span>
                            <span className="text-[10px] text-stone-500 font-mono">
                              Motion: {frame.camera_motion}
                            </span>
                          </div>

                          <p className="text-xs font-semibold text-stone-900 leading-snug">
                            &ldquo;{frame.dialogue}&rdquo;
                          </p>

                          <p className="text-[11px] text-stone-500 line-clamp-2 leading-relaxed">
                            <span className="font-medium text-stone-600">Visual Prompt:</span> {frame.visual_prompt}
                          </p>

                          {frame.audio_url && (
                            <div className="pt-1">
                              <audio
                                src={`${API_BASE}${frame.audio_url}`}
                                controls
                                className="h-6 w-full max-w-xs opacity-80"
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
            <div className="bg-gradient-to-r from-amber-500/10 via-rose-500/10 to-amber-600/10 border border-amber-200/80 rounded-3xl p-6 shadow-sm relative overflow-hidden bg-white">
              <div className="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-6">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-amber-500 to-rose-500 flex items-center justify-center text-4xl shadow-sm text-white">
                  🐉
                </div>
                <div className="space-y-1 text-center md:text-left flex-1">
                  <div className="flex items-center justify-center md:justify-start space-x-3">
                    <h2 className="text-2xl font-black text-stone-900">{myChannel.channel_name}</h2>
                    <a
                      href={myChannel.channel_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs bg-red-600 hover:bg-red-500 text-white font-bold px-3 py-1 rounded-full flex items-center space-x-1 shadow-xs"
                    >
                      <Tv className="w-3.5 h-3.5" />
                      <span>Visit Channel</span>
                      <ExternalLink className="w-3 h-3 ml-0.5" />
                    </a>
                  </div>
                  <p className="text-amber-800 font-semibold text-sm">&ldquo;{myChannel.tagline}&rdquo;</p>
                  <p className="text-xs text-stone-600 max-w-3xl leading-relaxed">{myChannel.description}</p>
                </div>
              </div>
            </div>

            {/* Core Mascots & Characters */}
            <div className="space-y-3">
              <h3 className="text-base font-extrabold text-stone-900 flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-amber-600" />
                <span>Our Tiny Heroes & Mascots</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {myChannel.core_characters?.map((c: any, i: number) => (
                  <div key={i} className="bg-white border border-stone-200 rounded-2xl p-4 space-y-2 shadow-xs">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-sm text-amber-900">{c.name}</h4>
                      <span className="text-[10px] bg-stone-100 text-stone-700 border border-stone-200 px-2 py-0.5 rounded-full capitalize font-medium">
                        {c.role}
                      </span>
                    </div>
                    <p className="text-[11px] text-stone-700 leading-relaxed bg-[#FAF9F5] p-2.5 rounded-xl border border-stone-200">
                      {c.visual_anchor}
                    </p>
                    <p className="text-[11px] text-stone-500">
                      <span className="font-semibold text-stone-700">Personality:</span> {c.personality}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Published Video Audit */}
            <div className="space-y-3">
              <h3 className="text-base font-extrabold text-stone-900">
                Published Video Audit (Agent Memory)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {myChannel.published_video_audit?.map((vid: any, i: number) => (
                  <div key={i} className="bg-white border border-stone-200 rounded-xl p-3 flex items-center justify-between shadow-xs">
                    <div>
                      <p className="text-xs font-semibold text-stone-900">{vid.title}</p>
                      <p className="text-[10px] text-amber-800 font-medium">Character: {vid.character}</p>
                    </div>
                    <span className="text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded font-medium">
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
                <h2 className="text-xl font-extrabold text-stone-900">All Production Runs</h2>
                <p className="text-xs text-stone-500 font-medium">Stored in isolated folders under output/runs/</p>
              </div>
              <button
                onClick={() => { fetchStats(); fetchRuns(); }}
                className="bg-white hover:bg-stone-50 text-stone-700 text-xs px-3 py-1.5 rounded-lg border border-stone-300 flex items-center space-x-1.5 shadow-xs font-medium"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Refresh</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {runs.map((r) => (
                <div
                  key={r.id}
                  className="bg-white border border-stone-200 rounded-2xl overflow-hidden shadow-xs hover:border-amber-400 hover:shadow-sm transition flex flex-col"
                >
                  <div className="relative aspect-video bg-stone-100 flex items-center justify-center">
                    {r.thumbnail_url ? (
                      <img src={`${API_BASE}${r.thumbnail_url}`} alt={r.title} className="w-full h-full object-cover" />
                    ) : (
                      <Film className="w-10 h-10 text-stone-400" />
                    )}
                    <span className="absolute bottom-2 right-2 bg-black/80 backdrop-blur text-white text-xs font-mono px-2 py-0.5 rounded font-medium">
                      ⏱️ {r.duration.toFixed(1)}s
                    </span>
                    <span className="absolute top-2 left-2 bg-amber-600 text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase">
                      {r.aspect_ratio || "16:9"}
                    </span>
                  </div>

                  <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                    <h3 className="font-bold text-xs text-stone-900 line-clamp-2 leading-snug">{r.title}</h3>
                    <div className="pt-2 border-t border-stone-100 flex items-center justify-between">
                      <span className="text-[11px] text-stone-500 font-medium">{r.frame_count} frames</span>
                      <button
                        onClick={() => {
                          setSelectedRunId(r.id);
                          setActiveTab("studio");
                        }}
                        className="bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center space-x-1 shadow-xs"
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
                <h2 className="text-xl font-extrabold text-stone-900">Competitor Viral Hits & Formulas</h2>
                <p className="text-xs text-stone-500 font-medium">Million-view kids bedtime and cartoon stories scraped via YouTube Data API</p>
              </div>
              <button
                disabled={isCompLoading}
                onClick={fetchCompetitors}
                className="bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold px-3 py-1.5 rounded-xl flex items-center space-x-1 shadow-xs"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isCompLoading ? "animate-spin" : ""}`} />
                <span>Refresh Competitors</span>
              </button>
            </div>

            {competitors && (
              <div className="space-y-5">
                <div className="bg-white border border-stone-200 rounded-2xl overflow-hidden shadow-xs">
                  <div className="p-3.5 border-b border-stone-200 font-bold text-xs text-stone-800 bg-stone-50/80">
                    🏆 Million-View Benchmark Videos
                  </div>
                  <div className="divide-y divide-stone-100">
                    {competitors.top_videos?.map((vid: any, idx: number) => (
                      <div key={idx} className="p-3.5 flex items-center justify-between hover:bg-stone-50/80 transition">
                        <div>
                          <p className="text-xs font-semibold text-stone-900">#{idx + 1} {vid.title}</p>
                          <p className="text-[11px] text-stone-500">{vid.channel}</p>
                        </div>
                        <span className="text-xs font-mono font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-200/60">
                          {vid.views?.toLocaleString()} views
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white border border-stone-200 rounded-2xl p-4 shadow-xs">
                  <h3 className="text-xs font-bold text-stone-900 mb-2">🔥 Viral Tags to Model</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {competitors.top_keywords?.map((tag: string, i: number) => (
                      <span key={i} className="bg-stone-100 border border-stone-200 px-2.5 py-1 rounded-lg text-xs text-stone-700 font-medium">
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
