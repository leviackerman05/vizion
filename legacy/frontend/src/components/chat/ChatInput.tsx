import { useState, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { INPUT } from "@/constants/strings";
import { Send, Square } from "lucide-react";

type ChatInputProps = {
  onSend: (text: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  isGenerating?: boolean;
  centered?: boolean;
};

const ChatInput = ({
  onSend,
  onStop,
  disabled,
  isGenerating,
  centered,
}: ChatInputProps) => {
  const [text, setText] = useState("");

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={`p-4 ${centered ? "max-w-2xl mx-auto w-full" : ""}`}>
      <div className="relative flex gap-2 items-end rounded-xl border border-border/60 bg-card/50 backdrop-blur-sm p-2 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 transition-all">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={INPUT.PLACEHOLDER}
          disabled={disabled}
          rows={1}
          className="flex-1 min-h-[44px] max-h-32 resize-none border-0 bg-transparent focus-visible:ring-0 shadow-none text-sm"
        />
        {isGenerating ? (
          <Button
            size="icon"
            variant="destructive"
            className="shrink-0 h-9 w-9"
            onClick={onStop}
          >
            <Square size={14} />
          </Button>
        ) : (
          <Button
            size="icon"
            className="shrink-0 h-9 w-9"
            onClick={handleSend}
            disabled={disabled || !text.trim()}
          >
            <Send size={16} />
          </Button>
        )}
      </div>
      <p className="text-[10px] text-muted-foreground mt-1.5 text-center">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  );
};

export default ChatInput;
