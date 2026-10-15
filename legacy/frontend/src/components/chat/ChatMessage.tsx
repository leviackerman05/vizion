import ReactMarkdown from "react-markdown";
import { Copy, Check } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

type ChatMessageProps = {
  message: {
    id: string;
    sender: "user" | "ai";
    text: string;
    timestamp: Date;
    status?: "generating" | "done" | "error";
  };
};

const ChatMessage = ({ message }: ChatMessageProps) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.sender === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold ${
          isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
        }`}
      >
        {isUser ? "U" : "V"}
      </div>
      <div className={`flex flex-col gap-1 max-w-[85%] ${isUser ? "items-end" : ""}`}>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {isUser ? "You" : "Vizion"}
          </span>
          {message.status === "generating" && (
            <span className="text-xs text-primary animate-pulse">generating...</span>
          )}
        </div>
        <div
          className={`rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted/60 text-foreground border border-border/50"
          } ${message.status === "error" ? "border-destructive/50 text-destructive" : ""}`}
        >
          {isUser ? (
            message.text
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{message.text}</ReactMarkdown>
            </div>
          )}
        </div>
        {!isUser && message.status !== "generating" && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs self-start"
            onClick={handleCopy}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span className="ml-1">{copied ? "Copied" : "Copy"}</span>
          </Button>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
