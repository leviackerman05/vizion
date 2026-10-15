import { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";
import { CHAT } from "@/constants/strings";
import { ChatMessage as ChatMessageType } from "@/types";

type ChatContainerProps = {
  messages: ChatMessageType[];
};

const ChatContainer = ({ messages }: ChatContainerProps) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
        {CHAT.EMPTY}
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin">
      {messages.map((msg) => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
};

export default ChatContainer;
