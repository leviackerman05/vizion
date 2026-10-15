import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Search,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Logo from "./Logo";
import ChatList from "./ChatList";
import { SIDEBAR, PLANS } from "@/constants/strings";
import { ChatHistory } from "@/types";
import { deleteChat } from "@/lib/api/chats";

type SidebarProps = {
  chats: ChatHistory[];
  onNewChat: () => void;
  onSelectChat: (id: string) => void;
  onDeleteChat?: (id: string) => void;
  selectedChatId: string | null;
  plan?: string;
  remaining?: number | null;
};

const Sidebar = ({
  chats,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  selectedChatId,
  plan = "free",
  remaining,
}: SidebarProps) => {
  const [collapsed, setCollapsed] = useState(false);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const filtered = chats.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase())
  );

  const handleLogout = () => {
    localStorage.clear();
    navigate("/login");
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteChat(id);
      onDeleteChat?.(id);
    } catch (err) {
      console.error(err);
    }
  };

  if (collapsed) {
    return (
      <div className="w-12 bg-sidebar border-r border-sidebar-border flex flex-col items-center py-3 gap-2">
        <Button variant="ghost" size="icon" onClick={() => setCollapsed(false)}>
          <ChevronRight size={16} />
        </Button>
        <Button variant="ghost" size="icon" onClick={onNewChat}>
          <Plus size={16} />
        </Button>
      </div>
    );
  }

  return (
    <div className="w-64 bg-sidebar text-sidebar-foreground border-r border-sidebar-border flex flex-col shrink-0">
      <div className="p-3 flex items-center justify-between border-b border-sidebar-border">
        <Logo />
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setCollapsed(true)}>
          <ChevronLeft size={14} />
        </Button>
      </div>

      <div className="p-3">
        <Button
          onClick={onNewChat}
          className="w-full justify-start gap-2 bg-sidebar-accent hover:bg-sidebar-accent/80 text-sidebar-foreground"
          variant="ghost"
        >
          <Plus size={16} />
          {SIDEBAR.NEW_CHAT}
        </Button>
      </div>

      <div className="px-3 pb-2">
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={SIDEBAR.SEARCH}
            className="pl-8 h-8 text-xs bg-sidebar-accent/50 border-sidebar-border"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2">
        <ChatList
          chats={filtered}
          onSelectChat={onSelectChat}
          selectedChatId={selectedChatId}
          onDeleteChat={handleDelete}
        />
      </div>

      <div className="p-3 border-t border-sidebar-border space-y-2">
        {plan === "free" && remaining !== null && remaining !== undefined && (
          <div className="text-xs text-muted-foreground px-1">
            {remaining} {PLANS.REMAINING}
          </div>
        )}
        {plan === "pro" && (
          <div className="text-xs text-primary px-1 font-medium">Pro plan active</div>
        )}
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 justify-start gap-2 text-xs"
            onClick={() => navigate("/profile")}
          >
            <Settings size={14} />
            {SIDEBAR.SIGN_OUT === "Sign Out" ? "Account" : "Settings"}
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleLogout}>
            <LogOut size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
