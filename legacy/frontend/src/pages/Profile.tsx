
import ProfileSidebar from "@/components/profile/ProfileSidebar";
import ProfileContent from "@/components/profile/ProfileContent";
import Header from "@/components/header/Header";
import Sidebar from "@/components/sidebar/Sidebar";
import { useState } from "react";
import { ChatHistory } from "@/types";

const Profile = () => {
  const [chats, setChats] = useState<ChatHistory[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);

  const handleNewChat = () => {
    setSelectedChatId(null);
  };

  const handleSelectChat = (id: string) => {
    setSelectedChatId(id);
  };

  return (
    <div className="h-screen flex flex-col">
      <div className="flex-1 flex overflow-hidden">
        <Sidebar 
          chats={chats} 
          onNewChat={handleNewChat} 
          onSelectChat={handleSelectChat}
          selectedChatId={selectedChatId}
        />
        
        <div className="flex-1 flex flex-col">
          <Header />
          
          <main className="flex-1 flex overflow-auto">
            <div className="flex w-full gap-6 p-6">
              <ProfileSidebar />
              <ProfileContent />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default Profile;
