import ChatContainer from "./ChatContainer";
import ChatInput from "./ChatInput";
import { CHAT } from "@/constants/strings";
import { ChatMessage } from "@/types";

type ChatPanelProps = {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  onStop?: () => void;
  expanded: boolean;
  isGenerating?: boolean;
  statusMessage?: string;
};

const ChatPanel = ({
  messages,
  onSendMessage,
  onStop,
  expanded,
  isGenerating,
  statusMessage,
}: ChatPanelProps) => {
  if (!expanded) {
    return (
      <div className="h-full flex flex-col items-center justify-center px-6">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold tracking-tight mb-2">{CHAT.WELCOME}</h1>
          <p className="text-muted-foreground text-sm">
            Describe any concept, equation, or process to animate
          </p>
        </div>
        <ChatInput
          onSend={onSendMessage}
          onStop={onStop}
          disabled={isGenerating}
          isGenerating={isGenerating}
          centered
        />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {statusMessage && isGenerating && (
        <div className="px-4 py-2 text-xs text-primary border-b border-border/50 bg-primary/5 animate-pulse">
          {statusMessage}
        </div>
      )}
      <ChatContainer messages={messages} />
      <ChatInput
        onSend={onSendMessage}
        onStop={onStop}
        disabled={isGenerating}
        isGenerating={isGenerating}
      />
    </div>
  );
};

export default ChatPanel;
