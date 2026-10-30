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
  Volume2,
  Trash2,
  StopCircle,
  CheckCircle,
  Eye,
  Clock,
  TrendingUp,
  Plus,
  PanelLeftClose,
  PanelLeftOpen,
  MessageSquarePlus
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
  thumbnail_url?: string | null;
  thumbnail_branded_url?: string | null;
  master_audio_url: string | null;
  frames: FrameItem[];
  character_bible: any;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

const API_BASE = "http://localhost:8000";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"studio" | "dashboard" | "mychannel" | "competitors">("studio");
  const [stats, setStats] = useState({ total_videos: 0, total_runtime_seconds: 0, gpu_model: "RTX 2050", active_model: "DisneyPixar 768" });
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [runDetail, setRunDetail] = useState<RunDetail | null>(null);
  const [myChannel, setMyChannel] = useState<any>(null);

  // Conversations state & history
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConvId, setActiveConvId] = useState<string>("");
  const [isConvSidebarOpen, setIsConvSidebarOpen] = useState(true);
  const [isCreatingConv, setIsCreatingConv] = useState(false);

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
  const [liveStatus, setLiveStatus] = useState<any>(null);
  const pollingRef = useRef<any>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Stop polling helper
  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  // Start polling production status
  const startPolling = () => {
    stopPolling();
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/production/status`);
        if (res.ok) {
          const data = await res.json();
          setLiveStatus(data);
          
          if (!data.is_active) {
            stopPolling();
            setIsChatLoading(false);
            
            if (data.error) {
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last?.content?.includes(data.error)) return prev;
                return [...prev, { role: "assistant", content: `❌ **Production Error**: ${data.error}` }];
              });
            } else if (data.latest_reply) {
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last?.content === data.latest_reply) return prev;
                return [...prev, { role: "assistant", content: data.latest_reply }];
              });
            }
            fetchStats();
            fetchRuns();
            if (activeConvId) fetchConversationMessages(activeConvId);
            fetchConversations();
          }
        }
      } catch (e) {
        console.warn("Status poll error:", e);
      }
    }, 1500);
  };

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
    } catch (e) { }
  };

  // Competitor data
  const [competitors, setCompetitors] = useState<any>(null);
  const [isCompLoading, setIsCompLoading] = useState(false);

  const fetchConversations = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/conversations`);
      if (res.ok) {
        const data: ConversationSummary[] = await res.json();
        setConversations(data);
        if (data.length > 0 && !activeConvId) {
          setActiveConvId(data[0].id);
          fetchConversationMessages(data[0].id);
        }
      }
    } catch (e) {
      console.warn("Failed to fetch conversations:", e);
    }
  };

  const fetchConversationMessages = async (convId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/conversations/${convId}`);
      if (res.ok) {
        const data = await res.json();
        setActiveConvId(convId);
        if (data.messages && Array.isArray(data.messages) && data.messages.length > 0) {
          setMessages((prev) => {
            // Never overwrite with fewer messages or wipe an active assistant reply
            if (prev.length > data.messages.length) return prev;
            return data.messages;
          });
        }
      }
    } catch (e) {
      console.warn("Failed to fetch conversation detail:", e);
    }
  };

  const handleCreateNewConversation = async () => {
    if (isCreatingConv) return;
    setIsCreatingConv(true);
    try {
      const res = await fetch(`${API_BASE}/api/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Production Chat" })
      });
      if (res.ok) {
        const data = await res.json();
        setActiveConvId(data.id);
        setMessages(data.messages || []);
        setChatInput("");
        await fetchConversations();
      }
    } catch (e) {
      console.warn("Create conversation error:", e);
    } finally {
      setIsCreatingConv(false);
    }
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this conversation thread?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/conversations/${convId}`, { method: "DELETE" });
      if (res.ok) {
        const remaining = conversations.filter(c => c.id !== convId);
        setConversations(remaining);
        if (activeConvId === convId) {
          if (remaining.length > 0) {
            fetchConversationMessages(remaining[0].id);
          } else {
            handleCreateNewConversation();
          }
        }
      }
    } catch (e) {
      console.warn("Delete conversation error:", e);
    }
  };
  const [isSyncingChannel, setIsSyncingChannel] = useState(false);
  const [syncStatusMsg, setSyncStatusMsg] = useState<string | null>(null);

  const handleSyncChannel = async () => {
    if (isSyncingChannel) return;
    setIsSyncingChannel(true);
    setSyncStatusMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/my_channel/sync`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        if (data.channel) {
          setMyChannel(data.channel);
          setSyncStatusMsg(`✅ Synced ${data.channel.total_uploaded_videos || 10} videos live from YouTube!`);
          setTimeout(() => setSyncStatusMsg(null), 5000);
        }
      } else {
        setSyncStatusMsg("⚠️ Synced with cached channel data.");
        setTimeout(() => setSyncStatusMsg(null), 4000);
      }
    } catch (e: any) {
      console.warn("Failed to sync channel:", e);
      setSyncStatusMsg("❌ Network error connecting to sync API.");
      setTimeout(() => setSyncStatusMsg(null), 4000);
    } finally {
      setIsSyncingChannel(false);
    }
  };

  // Copy feedback
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [showBrandedThumb, setShowBrandedThumb] = useState(true);
  const [isRegeneratingThumb, setIsRegeneratingThumb] = useState(false);

  const handleRegenerateThumbnail = async () => {
    if (!selectedRunId || isRegeneratingThumb) return;
    setIsRegeneratingThumb(true);
    try {
      const res = await fetch(`${API_BASE}/api/runs/${selectedRunId}/thumbnail`, { method: "POST" });
      if (res.ok) {
        await fetchRunDetail(selectedRunId);
      }
    } catch (e) {
      console.warn("Regenerate thumbnail error:", e);
    } finally {
      setIsRegeneratingThumb(false);
    }
  };

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
    fetchConversations();

    // Check if an existing production job is in progress on the server (handles page refresh seamlessly)
    const checkActiveJob = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/production/status`);
        if (res.ok) {
          const data = await res.json();
          setLiveStatus(data);
          if (data.is_active) {
            setIsChatLoading(true);
            startPolling();
          }
        }
      } catch (e) { }
    };
    checkActiveJob();

    return () => stopPolling();
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      fetchRunDetail(selectedRunId);
    }
  }, [selectedRunId]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isChatLoading]);

  const handleStopProduction = async () => {
    try {
      await fetch(`${API_BASE}/api/production/stop`, { method: "POST" });
      stopPolling();
      setIsChatLoading(false);
      setMessages((prev) => [...prev, { role: "assistant", content: "🛑 **Production stopped by user**. GPU resources released." }]);
    } catch (e: any) {
      console.warn("Stop error:", e);
    }
  };

  const handleCleanRuns = async () => {
    if (!confirm("Are you sure you want to clean all previous output runs to start fresh?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/production/clean`, { method: "POST" });
      if (res.ok) {
        fetchStats();
        fetchRuns();
        setSelectedRunId(null);
        setRunDetail(null);
        setMessages((prev) => [...prev, { role: "assistant", content: "🧹 **All previous output runs cleaned**. Workspace is pristine and ready for your first official long video production!" }]);
      }
    } catch (e: any) {
      console.warn("Clean runs error:", e);
    }
  };

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
        body: JSON.stringify({ message: text, thread_id: activeConvId || "default_user" }),
      });
      fetchConversations();
      if (res.ok) {
        const data = await res.json();
        if (data.status === "busy") {
          setMessages([...newMessages, { role: "assistant", content: `⏳ **Production already in progress**: ${data.message}` }]);
        }
        startPolling();
      } else {
        const errData = await res.json().catch(() => ({}));
        const errDetail = errData.detail || "Server error";
        setMessages([...newMessages, { role: "assistant", content: `❌ **Error connecting to AI Showrunner Agent**: ${errDetail}` }]);
        setIsChatLoading(false);
      }
    } catch (e: any) {
      setMessages([...newMessages, { role: "assistant", content: `❌ **Network Connection Error**: ${e.message}` }]);
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
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeTab === "studio" ? "bg-white text-stone-900 shadow-xs border border-stone-200/80" : "text-stone-600 hover:text-stone-900"
                }`}
            >
              🎬 Studio (Chat & Video)
            </button>
            <button
              onClick={() => setActiveTab("mychannel")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeTab === "mychannel" ? "bg-white text-stone-900 shadow-xs border border-stone-200/80" : "text-stone-600 hover:text-stone-900"
                }`}
            >
              🏰 Our Channel
            </button>
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeTab === "dashboard" ? "bg-white text-stone-900 shadow-xs border border-stone-200/80" : "text-stone-600 hover:text-stone-900"
                }`}
            >
              🎞️ All Runs ({runs.length})
            </button>
            <button
              onClick={() => { setActiveTab("competitors"); if (!competitors) fetchCompetitors(); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeTab === "competitors" ? "bg-white text-stone-900 shadow-xs border border-stone-200/80" : "text-stone-600 hover:text-stone-900"
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
            {/* LEFT PANE: CONVERSATION SIDEBAR + AGENT CHAT (48% Width)    */}
            {/* ------------------------------------------------------------ */}
            <div className="w-full md:w-[48%] h-full flex divide-x divide-stone-200 bg-[#FDFCF7] min-w-0">
              {/* Conversation History Drawer */}
              {isConvSidebarOpen && (
                <div className="w-56 md:w-60 h-full bg-white flex flex-col shrink-0 border-r border-stone-200/70">
                  {/* Top Bar: New Conversation Button */}
                  <div className="p-3 border-b border-stone-100">
                    <button
                      onClick={handleCreateNewConversation}
                      disabled={isCreatingConv}
                      className="w-full bg-gradient-to-r from-amber-500 via-rose-400 to-amber-600 hover:opacity-95 text-white font-bold py-2 px-3 rounded-xl shadow-xs flex items-center justify-center space-x-1.5 text-xs transition cursor-pointer"
                    >
                      <Plus className="w-4 h-4" />
                      <span>New Chat</span>
                    </button>
                  </div>

                  {/* Conversation List */}
                  <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-stone-400 flex items-center justify-between">
                      <span>Saved Chats ({conversations.length})</span>
                    </div>

                    {conversations.map((c) => {
                      const isActive = c.id === activeConvId;
                      return (
                        <div
                          key={c.id}
                          onClick={() => fetchConversationMessages(c.id)}
                          className={`group px-3 py-2 rounded-xl border text-xs cursor-pointer transition flex items-center justify-between ${
                            isActive
                              ? "bg-amber-50/90 border-amber-300 text-amber-950 font-bold shadow-2xs"
                              : "bg-transparent border-transparent hover:bg-stone-50 text-stone-600"
                          }`}
                        >
                          <div className="flex-1 min-w-0 pr-1">
                            <p className="truncate text-xs leading-snug">{c.title || "Untitled Chat"}</p>
                            <p className="text-[10px] text-stone-400 font-normal mt-0.5">
                              {c.updated_at ? c.updated_at.split(" ")[1] : "Today"} • {c.message_count} msgs
                            </p>
                          </div>
                          <button
                            onClick={(e) => handleDeleteConversation(c.id, e)}
                            className="opacity-0 group-hover:opacity-100 text-stone-400 hover:text-rose-600 p-1 rounded transition"
                            title="Delete conversation"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Main Chat Conversation View */}
              <div className="flex-1 h-full flex flex-col min-w-0">
                {/* Chat Header with Sidebar Toggle & Actions */}
                <div className="px-4 py-2.5 border-b border-stone-200 bg-white flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setIsConvSidebarOpen(!isConvSidebarOpen)}
                      className="text-stone-500 hover:text-stone-800 p-1.5 rounded-lg hover:bg-stone-100 border border-stone-200/60 transition"
                      title={isConvSidebarOpen ? "Hide chat history" : "Show chat history"}
                    >
                      {isConvSidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
                    </button>
                    <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-200">
                      <Wand2 className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <h2 className="text-xs font-bold text-stone-900 truncate max-w-[200px]">
                        {conversations.find(c => c.id === activeConvId)?.title || "AI Showrunner Agent"}
                      </h2>
                      <p className="text-[10px] text-emerald-700 font-medium">Autonomous Producer for @WhimsyWandTales</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <button
                      onClick={handleCreateNewConversation}
                      className="text-[11px] text-amber-800 bg-amber-50 hover:bg-amber-100 px-2.5 py-1 rounded-md transition border border-amber-200/80 font-medium flex items-center space-x-1"
                      title="Start a fresh conversation"
                    >
                      <Plus className="w-3 h-3" />
                      <span>New Chat</span>
                    </button>
                    <button
                      onClick={handleClearChat}
                      className="text-[11px] text-stone-500 hover:text-stone-800 px-2.5 py-1 rounded-md hover:bg-stone-100 transition border border-stone-200/60"
                    >
                      Clear
                    </button>
                  </div>
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
                  onClick={() => handleSendMessage("Produce a 5-minute Bedtime Story episode for WhimsyWand Tales (16:9 widescreen, target_duration_minutes=5.0, 25 frames) starring Barnaby Bear and friends, using our viral 4-phase bedtime framework, strict child voices, continuous dialogue, smooth camera zoom motion, and music-box lullaby.")}
                  className="whitespace-nowrap px-3 py-1 rounded-full bg-indigo-50 hover:bg-indigo-100 text-indigo-900 border border-indigo-200 transition flex items-center space-x-1.5 font-semibold"
                >
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  <span>🌙 5-Min Bedtime Story (Test Run)</span>
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
                <button
                  onClick={handleCleanRuns}
                  className="whitespace-nowrap px-3 py-1 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 transition font-medium flex items-center space-x-1"
                >
                  <Trash2 className="w-3 h-3 text-rose-600" />
                  <span>Clean Output Runs</span>
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
                      className={`max-w-[88%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-xs ${msg.role === "user"
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
                    <div className="bg-white border-2 border-amber-300/80 rounded-2xl rounded-bl-none p-5 text-xs text-stone-800 shadow-md max-w-[95%] w-[580px] space-y-4">
                      {/* Header with Title and Elapsed Timer */}
                      <div className="flex items-center justify-between border-b border-stone-200 pb-3">
                        <div className="flex items-center space-x-2.5">
                          <RefreshCw className="w-4 h-4 animate-spin text-amber-600 shrink-0" />
                          <div>
                            <h4 className="font-extrabold text-stone-900 text-xs">
                              {liveStatus?.stage_title || "AI Production In Progress"}
                            </h4>
                            <p className="text-[11px] text-stone-500 font-medium">
                              {liveStatus?.title || "Autonomous Fairy Tale Studio"} • {liveStatus?.aspect_ratio || "16:9"}
                            </p>
                          </div>
                        </div>
                        <div className="flex flex-col items-end space-y-1 shrink-0">
                          <span className="font-mono text-[11px] bg-amber-50 text-amber-900 border border-amber-200 px-2.5 py-0.5 rounded-full font-bold shadow-2xs">
                            ⏱️ {liveStatus?.elapsed_seconds !== undefined ? `${liveStatus.elapsed_seconds}s` : `${loadingElapsed}s`} elapsed
                          </span>
                          {liveStatus?.estimated_remaining_seconds > 0 && (
                            <span className="font-mono text-[10px] text-stone-500 font-medium">
                              ⏳ ~{liveStatus.estimated_remaining_seconds}s remaining
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Progress Bar & Frame Counter */}
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-[11px] font-semibold text-stone-700">
                          <span className="truncate pr-2">{liveStatus?.detail || "Processing step..."}</span>
                          <span className="font-mono font-bold text-amber-800 shrink-0">{liveStatus?.progress_percent || 0}%</span>
                        </div>
                        <div className="w-full bg-stone-100 rounded-full h-2.5 border border-stone-200 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-amber-500 via-rose-400 to-amber-600 h-2.5 rounded-full transition-all duration-500 ease-out"
                            style={{ width: `${Math.max(5, liveStatus?.progress_percent || 0)}%` }}
                          />
                        </div>
                      </div>

                      {/* Stages Checklist */}
                      <div className="space-y-2 pt-1">
                        {liveStatus?.stages?.map((st: any, idx: number) => {
                          const isDone = st.status === "completed";
                          const isCurrent = st.status === "in_progress";
                          return (
                            <div key={st.key || idx} className="flex items-center space-x-2.5 text-stone-700">
                              <span
                                className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                                  isDone
                                    ? "bg-emerald-100 text-emerald-700"
                                    : isCurrent
                                    ? "bg-amber-100 text-amber-800 animate-pulse border border-amber-300"
                                    : "bg-stone-100 text-stone-400"
                                }`}
                              >
                                {isDone ? "✓" : isCurrent ? "•" : "○"}
                              </span>
                              <span className={`text-[11px] ${isCurrent ? "font-bold text-stone-900" : isDone ? "font-medium text-stone-600" : "text-stone-400"}`}>
                                {st.title}
                              </span>
                            </div>
                          );
                        })}
                      </div>

                      {/* Control Actions */}
                      <div className="flex items-center justify-between pt-2 border-t border-stone-100">
                        <span className="text-[10px] text-stone-500 font-medium">
                          🛡️ Safe reload: refresh anytime without losing progress
                        </span>
                        <button
                          type="button"
                          onClick={handleStopProduction}
                          className="text-[11px] text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 px-2.5 py-1 rounded-lg font-bold transition-colors cursor-pointer flex items-center space-x-1"
                        >
                          <StopCircle className="w-3.5 h-3.5" />
                          <span>Stop Production</span>
                        </button>
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
          </div>

            {/* ------------------------------------------------------------ */}
            {/* RIGHT PANE: GENERATED VIDEOS, IMAGES & METADATA (52% Width)   */}
            {/* ------------------------------------------------------------ */}
            <div className="w-full md:w-[52%] h-full flex flex-col bg-white overflow-y-auto">
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
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${runDetail.aspect_ratio === "9:16" ? "bg-amber-100 text-amber-800 border border-amber-300/60" : "bg-stone-100 text-stone-800 border border-stone-300/60"
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

              {/* Dedicated High-CTR YouTube Thumbnail Showcase */}
              {runDetail && (runDetail.thumbnail_url || runDetail.thumbnail_branded_url) && (
                <div className="p-4 bg-white border-b border-stone-200">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-amber-600" />
                      <span className="text-xs font-bold text-stone-900">Official YouTube Thumbnail (1280×720 HD)</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <button
                        onClick={() => setShowBrandedThumb(true)}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition ${
                          showBrandedThumb ? "bg-amber-100 text-amber-900 border border-amber-300" : "bg-stone-100 text-stone-600 hover:bg-stone-200"
                        }`}
                      >
                        ✨ Branded Poster
                      </button>
                      <button
                        onClick={() => setShowBrandedThumb(false)}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition ${
                          !showBrandedThumb ? "bg-amber-100 text-amber-900 border border-amber-300" : "bg-stone-100 text-stone-600 hover:bg-stone-200"
                        }`}
                      >
                        🎨 Clean Art
                      </button>
                    </div>
                  </div>

                  <div className="relative rounded-xl overflow-hidden border border-stone-200 shadow-xs bg-stone-900 max-w-xl mx-auto">
                    <img
                      src={`${API_BASE}${showBrandedThumb && runDetail.thumbnail_branded_url ? runDetail.thumbnail_branded_url : runDetail.thumbnail_url}`}
                      alt="YouTube Thumbnail"
                      className="w-full h-auto object-cover max-h-[300px]"
                    />
                    <div className="p-3 bg-stone-50 border-t border-stone-200 flex items-center justify-between">
                      <span className="text-[11px] text-stone-500 font-medium">
                        16:9 High-CTR Poster • Ready for YouTube Studio
                      </span>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={handleRegenerateThumbnail}
                          disabled={isRegeneratingThumb}
                          className="text-[11px] text-stone-700 hover:text-stone-900 bg-white hover:bg-stone-100 border border-stone-300 px-3 py-1.5 rounded-lg font-medium transition flex items-center space-x-1 shadow-2xs cursor-pointer"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 text-stone-500 ${isRegeneratingThumb ? "animate-spin" : ""}`} />
                          <span>{isRegeneratingThumb ? "Rendering..." : "Regenerate"}</span>
                        </button>
                        <a
                          href={`${API_BASE}${showBrandedThumb && runDetail.thumbnail_branded_url ? runDetail.thumbnail_branded_url : runDetail.thumbnail_url}`}
                          download={`thumbnail_${runDetail.id}.jpg`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] text-white bg-amber-600 hover:bg-amber-500 px-3 py-1.5 rounded-lg font-bold transition flex items-center space-x-1 shadow-xs cursor-pointer"
                        >
                          <span>📥 Download Thumbnail</span>
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              )}

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
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-amber-500 to-rose-500 flex items-center justify-center text-4xl shadow-sm text-white shrink-0">
                  🐉
                </div>
                <div className="space-y-1.5 text-center md:text-left flex-1 min-w-0">
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-2.5">
                    <h2 className="text-2xl font-black text-stone-900">{myChannel.channel_name}</h2>
                    <span className="text-xs font-mono bg-amber-50 text-amber-800 border border-amber-300 px-2.5 py-0.5 rounded-full font-bold">
                      {myChannel.handle}
                    </span>
                    <a
                      href={myChannel.channel_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs bg-red-600 hover:bg-red-500 text-white font-bold px-3 py-1 rounded-full flex items-center space-x-1 shadow-xs transition"
                    >
                      <Tv className="w-3.5 h-3.5" />
                      <span>Visit Channel</span>
                      <ExternalLink className="w-3 h-3 ml-0.5" />
                    </a>
                    <button
                      onClick={handleSyncChannel}
                      disabled={isSyncingChannel}
                      className="text-xs bg-white hover:bg-amber-50 text-amber-900 border border-amber-300 font-bold px-3 py-1 rounded-full flex items-center space-x-1 shadow-2xs transition cursor-pointer"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 text-amber-700 ${isSyncingChannel ? "animate-spin" : ""}`} />
                      <span>{isSyncingChannel ? "Syncing YouTube..." : "Sync from YouTube"}</span>
                    </button>
                  </div>
                  <p className="text-amber-800 font-semibold text-sm">&ldquo;{myChannel.tagline}&rdquo;</p>
                  <p className="text-xs text-stone-600 max-w-3xl leading-relaxed">{myChannel.description}</p>
                  {syncStatusMsg && (
                    <div className="text-xs font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-lg inline-block">
                      {syncStatusMsg}
                    </div>
                  )}
                </div>
              </div>

              {/* Channel Performance KPI Strip */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6 pt-5 border-t border-amber-200/60">
                <div className="bg-[#FAF9F5] border border-stone-200 rounded-xl p-3 text-center">
                  <div className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Total Uploads</div>
                  <div className="text-xl font-black text-stone-900 mt-0.5">
                    {myChannel.total_uploaded_videos || (myChannel.live_videos?.length || 0) + (myChannel.live_shorts?.length || 0) || 10}
                  </div>
                  <div className="text-[10px] text-stone-400 mt-0.5">Live on @WhimsyWandTales</div>
                </div>
                <div className="bg-[#FAF9F5] border border-stone-200 rounded-xl p-3 text-center">
                  <div className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Long Videos (16:9)</div>
                  <div className="text-xl font-black text-amber-700 mt-0.5">
                    {myChannel.total_long_videos || myChannel.live_videos?.length || 3}
                  </div>
                  <div className="text-[10px] text-stone-400 mt-0.5">Omnibuses & Episodes</div>
                </div>
                <div className="bg-[#FAF9F5] border border-stone-200 rounded-xl p-3 text-center">
                  <div className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Shorts (9:16)</div>
                  <div className="text-xl font-black text-rose-600 mt-0.5">
                    {myChannel.total_shorts || myChannel.live_shorts?.length || 7}
                  </div>
                  <div className="text-[10px] text-stone-400 mt-0.5">Viral Hooks & Clips</div>
                </div>
                <div className="bg-[#FAF9F5] border border-stone-200 rounded-xl p-3 text-center">
                  <div className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Last Channel Sync</div>
                  <div className="text-xs font-bold text-stone-800 mt-1">
                    {myChannel.last_synced_at ? myChannel.last_synced_at.split(" ")[1] || myChannel.last_synced_at : "Just now"}
                  </div>
                  <div className="text-[10px] text-emerald-700 font-semibold mt-0.5">● Connected Live</div>
                </div>
              </div>
            </div>

            {/* Spotlight: Latest Uploaded Video */}
            {myChannel.live_videos && myChannel.live_videos.length > 0 && (
              <div className="bg-white border-2 border-amber-300/80 rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
                    <span className="text-xs font-extrabold uppercase tracking-wider text-amber-900 bg-amber-100 px-2.5 py-0.5 rounded-full border border-amber-300">
                      ⭐ Latest Published Video
                    </span>
                    <span className="text-xs text-stone-500 font-medium">
                      Uploaded {myChannel.live_videos[0].published_time || "recently"}
                    </span>
                  </div>
                  <a
                    href={myChannel.live_videos[0].url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs bg-stone-900 hover:bg-black text-white font-bold px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition shadow-2xs"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Watch on YouTube</span>
                    <ExternalLink className="w-3 h-3 ml-0.5" />
                  </a>
                </div>

                <div className="flex flex-col md:flex-row gap-5 items-start">
                  <div className="relative w-full md:w-72 aspect-video bg-stone-900 rounded-xl overflow-hidden shrink-0 border border-stone-200 shadow-xs">
                    <img
                      src={myChannel.live_videos[0].thumbnail}
                      alt={myChannel.live_videos[0].title}
                      className="w-full h-full object-cover"
                    />
                    <span className="absolute bottom-2 right-2 bg-black/85 text-white font-mono text-[11px] font-bold px-2 py-0.5 rounded shadow-sm">
                      ⏱️ {myChannel.live_videos[0].duration}
                    </span>
                  </div>
                  <div className="space-y-2.5 flex-1 min-w-0">
                    <h3 className="text-base font-extrabold text-stone-900 leading-snug">
                      {myChannel.live_videos[0].title}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="inline-flex items-center space-x-1 text-xs font-bold text-stone-700 bg-stone-100 px-2.5 py-1 rounded-md border border-stone-200">
                        <Eye className="w-3.5 h-3.5 text-stone-500" />
                        <span>{myChannel.live_videos[0].views}</span>
                      </span>
                      <span className="inline-flex items-center space-x-1 text-xs font-semibold text-stone-600 bg-stone-100 px-2.5 py-1 rounded-md border border-stone-200">
                        <Clock className="w-3.5 h-3.5 text-stone-500" />
                        <span>{myChannel.live_videos[0].published_time}</span>
                      </span>
                      <span className="text-xs font-bold text-amber-800 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-200">
                        16:9 Long Bedtime Omnibus
                      </span>
                    </div>
                    <p className="text-xs text-stone-500 leading-relaxed">
                      Now live and streaming for kids & toddlers worldwide. Showrunner agent automatically keeps track of this video to prevent story repeats.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Live Published Long Videos Grid (16:9) */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-extrabold text-stone-900 flex items-center space-x-2">
                    <Film className="w-4 h-4 text-amber-600" />
                    <span>Published Long Videos (16:9 Master Stories)</span>
                  </h3>
                  <p className="text-xs text-stone-500">Live video catalog from your YouTube channel</p>
                </div>
                <span className="text-xs font-bold bg-amber-50 text-amber-900 border border-amber-200 px-2.5 py-1 rounded-lg">
                  {myChannel.live_videos?.length || 3} Published
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {(myChannel.live_videos || []).map((vid: any) => (
                  <div
                    key={vid.id}
                    className="bg-white border border-stone-200 rounded-2xl overflow-hidden shadow-xs hover:border-amber-400 hover:shadow-sm transition flex flex-col"
                  >
                    <div className="relative aspect-video bg-stone-900">
                      <img
                        src={vid.thumbnail}
                        alt={vid.title}
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute bottom-2 right-2 bg-black/80 backdrop-blur text-white text-[10px] font-mono font-bold px-2 py-0.5 rounded">
                        ⏱️ {vid.duration}
                      </span>
                      <span className="absolute top-2 left-2 bg-amber-600 text-white text-[9px] font-extrabold px-2 py-0.5 rounded uppercase tracking-wider">
                        16:9 Widescreen
                      </span>
                    </div>

                    <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                      <div>
                        <h4 className="font-bold text-xs text-stone-900 line-clamp-2 leading-snug">
                          {vid.title}
                        </h4>
                        <div className="flex items-center space-x-2 mt-2">
                          <span className="text-[11px] font-semibold text-stone-600 bg-stone-100 px-2 py-0.5 rounded">
                            👁️ {vid.views}
                          </span>
                          <span className="text-[11px] text-stone-400">
                            {vid.published_time}
                          </span>
                        </div>
                      </div>

                      <div className="pt-2 border-t border-stone-100 flex items-center justify-between">
                        <span className="text-[10px] font-mono text-stone-400">ID: {vid.id}</span>
                        <a
                          href={vid.url}
                          target="_blank"
                          rel="noreferrer"
                          className="bg-red-600 hover:bg-red-500 text-white text-[11px] font-bold px-2.5 py-1 rounded-lg flex items-center space-x-1 shadow-2xs"
                        >
                          <Play className="w-3 h-3 fill-current" />
                          <span>YouTube</span>
                          <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Live Published Shorts Grid (9:16) */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-extrabold text-stone-900 flex items-center space-x-2">
                    <Flame className="w-4 h-4 text-rose-500" />
                    <span>Published YouTube Shorts (9:16 Viral Clips)</span>
                  </h3>
                  <p className="text-xs text-stone-500">Fast bedtime hooks and character moments on Shorts Feed</p>
                </div>
                <span className="text-xs font-bold bg-rose-50 text-rose-900 border border-rose-200 px-2.5 py-1 rounded-lg">
                  {myChannel.live_shorts?.length || 7} Shorts
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                {(myChannel.live_shorts || []).map((sh: any) => (
                  <div
                    key={sh.id}
                    className="bg-white border border-stone-200 rounded-xl overflow-hidden shadow-xs hover:border-rose-400 transition flex flex-col"
                  >
                    <div className="relative aspect-[9/14] bg-stone-900">
                      <img
                        src={sh.thumbnail}
                        alt={sh.title}
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute top-1.5 left-1.5 bg-rose-600 text-white text-[9px] font-extrabold px-1.5 py-0.5 rounded uppercase">
                        Short
                      </span>
                    </div>
                    <div className="p-2.5 flex-1 flex flex-col justify-between space-y-2">
                      <p className="text-[11px] font-bold text-stone-900 line-clamp-2 leading-tight">
                        {sh.title}
                      </p>
                      <div className="pt-1 border-t border-stone-100 flex items-center justify-between">
                        <span className="text-[10px] text-stone-500 font-semibold">{sh.views}</span>
                        <a
                          href={sh.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[10px] text-red-600 hover:text-red-700 font-bold flex items-center space-x-0.5"
                        >
                          <span>Watch</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
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
                      <p className="text-[10px] text-amber-800 font-medium">Character: {vid.character} {vid.duration ? `• ${vid.duration}` : ""}</p>
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
