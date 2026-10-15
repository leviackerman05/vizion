import { useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { toast } from "sonner";
import Header from "@/components/header/Header";
import Sidebar from "@/components/sidebar/Sidebar";
import ChatPanel from "@/components/chat/ChatPanel";
import VideoPanel from "@/components/video/VideoPanel";
import { ChatHistory, ChatMessage, VideoMetadata, VideoState } from "@/types";
import { createUserMessage, createAiMessage } from "@/utils";
import {
  fetchUserChats,
  fetchChatMessages,
  sendUserPromptStream,
  toVideoUrl,
} from "@/lib/api/chats";
import { fetchMe } from "@/lib/api/user";

const Index = () => {
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chats, setChats] = useState<ChatHistory[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [videoState, setVideoState] = useState<VideoState>("idle");
  const [videoMetadata, setVideoMetadata] = useState<VideoMetadata | null>(null);
  const [videoSrc, setVideoSrc] = useState<string | null>(null);
  const [script, setScript] = useState<string>("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [plan, setPlan] = useState("free");
  const [remaining, setRemaining] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchUserChats()
      .then((data) => {
        setChats(
          data.map((item: { id: string; title: string; created_at?: string }) => ({
            id: item.id,
            title: item.title || "Untitled",
            lastMessage: "",
            timestamp: item.created_at ? new Date(item.created_at) : new Date(),
          }))
        );
      })
      .catch(console.error);

    fetchMe()
      .then((me) => {
        setPlan(me.plan);
        setRemaining(me.remaining);
        localStorage.setItem("active_plan", me.plan);
      })
      .catch(console.error);
  }, []);

  const handleStop = () => {
    abortRef.current?.abort();
    setIsGenerating(false);
    setVideoState("idle");
    setStatusMessage("");
  };

  const handleSendMessage = async (text: string) => {
    let currentChatId = selectedChatId;

    if (!expanded || !selectedChatId) {
      const newChatId = uuidv4();
      const newChat: ChatHistory = {
        id: newChatId,
        title: text.length > 30 ? text.slice(0, 30) + "..." : text,
        lastMessage: text,
        timestamp: new Date(),
      };
      setChats((prev) => [newChat, ...prev]);
      setSelectedChatId(newChatId);
      setExpanded(true);
      currentChatId = newChatId;
    }

    setMessages((prev) => [...prev, createUserMessage(text)]);
    setVideoState("generating");
    setIsGenerating(true);
    setErrorMessage("");
    setStatusMessage("Analyzing your prompt...");
    setVideoSrc(null);
    setScript("");

    const aiMsg = createAiMessage("Generating your animation...", "generating");
    setMessages((prev) => [...prev, aiMsg]);

    abortRef.current = new AbortController();

    try {
      const result = await sendUserPromptStream(
        currentChatId,
        text,
        (event) => {
          setStatusMessage(event.message);
          if (event.chat_id) setSelectedChatId(event.chat_id);
        },
        abortRef.current.signal
      );

      if (!result?.video_url) throw new Error("No video returned");

      const videoUrl = `${toVideoUrl(result.video_url)}?t=${Date.now()}`;
      setVideoSrc(videoUrl);
      setScript(result.script || "");
      setVideoMetadata(result.metadata || {
        duration: "unknown",
        resolution: "unknown",
        format: "MP4",
        size: "unknown",
      });
      setVideoState("ready");

      setMessages((prev) => [
        ...prev.filter((m) => m.id !== aiMsg.id),
        createAiMessage("Here's your animation! Check the preview panel →"),
      ]);

      fetchMe().then((me) => {
        setPlan(me.plan);
        setRemaining(me.remaining);
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Generation failed";
      if (msg !== "The user aborted a request.") {
        setVideoState("error");
        setErrorMessage(msg);
        setMessages((prev) => [
          ...prev.filter((m) => m.id !== aiMsg.id),
          createAiMessage(`❌ ${msg}`, "error"),
        ]);
        if (msg.includes("Upgrade") || msg.includes("limit")) {
          toast.error(msg);
        }
      }
    } finally {
      setIsGenerating(false);
      setStatusMessage("");
    }
  };

  const handleSelectChat = async (chatId: string) => {
    setSelectedChatId(chatId);
    setExpanded(true);
    setMessages([]);
    setVideoState("idle");
    setVideoSrc(null);
    setScript("");

    try {
      const data = await fetchChatMessages(chatId);
      const list = Array.isArray(data) ? data : [];
      setMessages(
        list.map((m: { role: string; content: string; created_at?: string; video_url?: string }) => ({
          id: crypto.randomUUID(),
          text: m.content,
          sender: m.role === "assistant" ? "ai" : "user",
          timestamp: m.created_at ? new Date(m.created_at) : new Date(),
        }))
      );

      const withVideo = [...list].reverse().find((m: { video_url?: string }) => m.video_url);
      if (withVideo?.video_url) {
        setVideoSrc(`${toVideoUrl(withVideo.video_url)}?t=${Date.now()}`);
        setVideoState("ready");
        setVideoMetadata({ duration: "unknown", resolution: "unknown", format: "MP4", size: "unknown" });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteChat = (chatId: string) => {
    setChats((prev) => prev.filter((c) => c.id !== chatId));
    if (selectedChatId === chatId) handleNewChat();
  };

  const handleNewChat = () => {
    setExpanded(false);
    setSelectedChatId(null);
    setMessages([]);
    setVideoState("idle");
    setVideoMetadata(null);
    setVideoSrc(null);
    setScript("");
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          chats={chats}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
          selectedChatId={selectedChatId}
          plan={plan}
          remaining={remaining}
        />
        <div className="flex-1 flex flex-col min-w-0">
          <Header />
          <main className="flex-1 flex overflow-hidden">
            <div
              className={`transition-all duration-300 flex flex-col ${
                expanded ? "w-1/2 border-r border-border/50" : "w-full"
              }`}
            >
              <ChatPanel
                messages={messages}
                onSendMessage={handleSendMessage}
                onStop={handleStop}
                expanded={expanded}
                isGenerating={isGenerating}
                statusMessage={statusMessage}
              />
            </div>
            {expanded && (
              <div className="w-1/2 animate-fade-in">
                <VideoPanel
                  videoState={videoState}
                  videoSrc={videoSrc ?? undefined}
                  script={script}
                  metadata={videoMetadata}
                  errorMessage={errorMessage}
                />
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default Index;
