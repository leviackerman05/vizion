import { SIDEBAR } from "@/constants/strings";
import { ChatHistory } from "@/types";
import { MessageSquare, Trash2 } from "lucide-react";

type ChatListProps = {
  chats: ChatHistory[];
  onSelectChat: (id: string) => void;
  selectedChatId: string | null;
  onDeleteChat?: (id: string, e: React.MouseEvent) => void;
};

const ChatList = ({ chats, onSelectChat, selectedChatId, onDeleteChat }: ChatListProps) => {
  const todayChats = chats.filter(
    (chat) => chat.timestamp && new Date(chat.timestamp).toDateString() === new Date().toDateString()
  );
  const yesterdayChats = chats.filter((chat) => {
    if (!chat.timestamp) return false;
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return new Date(chat.timestamp).toDateString() === yesterday.toDateString();
  });
  const olderChats = chats.filter((chat) => {
    if (!chat.timestamp) return true;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 1);
    return new Date(chat.timestamp) < cutoff;
  });

  const ChatGroup = ({ title, items }: { title: string; items: ChatHistory[] }) => (
    <div className="space-y-1 mb-4">
      <h3 className="text-[10px] uppercase tracking-wider text-sidebar-foreground/40 px-2 mb-1">
        {title}
      </h3>
      {items.map((chat) => (
        <button
          key={chat.id}
          onClick={() => onSelectChat(chat.id)}
          className={`group w-full px-2 py-1.5 text-left flex items-center gap-2 hover:bg-sidebar-accent rounded-md transition-colors ${
            selectedChatId === chat.id ? "bg-sidebar-accent" : ""
          }`}
        >
          <MessageSquare size={14} className="shrink-0 text-sidebar-foreground/60" />
          <span className="truncate flex-1 text-sm">{chat.title}</span>
          {onDeleteChat && (
            <Trash2
              size={12}
              className="opacity-0 group-hover:opacity-60 hover:!opacity-100 shrink-0"
              onClick={(e) => onDeleteChat(chat.id, e)}
            />
          )}
        </button>
      ))}
    </div>
  );

  if (chats.length === 0) {
    return <p className="text-xs text-muted-foreground px-2 py-4">No chats yet</p>;
  }

  return (
    <div>
      {todayChats.length > 0 && <ChatGroup title={SIDEBAR.TODAY} items={todayChats} />}
      {yesterdayChats.length > 0 && <ChatGroup title={SIDEBAR.YESTERDAY} items={yesterdayChats} />}
      {olderChats.length > 0 && <ChatGroup title={SIDEBAR.PREVIOUS} items={olderChats} />}
    </div>
  );
};

export default ChatList;
