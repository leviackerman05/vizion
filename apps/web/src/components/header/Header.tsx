import { useNavigate } from "react-router-dom";
import { HEADER } from "@/constants/strings";
import { Button } from "@/components/ui/button";
import { User } from "lucide-react";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { useState } from "react";
import ExportModal from "@/components/modals/ExportModal";

const Header = () => {
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <header className="h-12 border-b border-border/50 flex items-center justify-between px-4 bg-background/80 backdrop-blur-sm">
      <Button variant="ghost" size="sm" onClick={() => setExportModalOpen(true)}>
        {HEADER.EXPORT}
      </Button>

      <div className="flex items-center gap-1">
        <ThemeToggle />
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => navigate("/profile")}>
          <User size={16} />
        </Button>
      </div>

      <ExportModal open={exportModalOpen} onOpenChange={setExportModalOpen} />
    </header>
  );
};

export default Header;
