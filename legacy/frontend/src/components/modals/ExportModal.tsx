import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { BadgeCheck, Download } from "lucide-react";
import { fetchMe } from "@/lib/api/user";

type ExportModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onExport?: () => void;
};

const ExportModal = ({ open, onOpenChange, onExport }: ExportModalProps) => {
  const navigate = useNavigate();
  const [plan, setPlan] = useState("free");

  useEffect(() => {
    if (open) fetchMe().then((me) => setPlan(me.plan)).catch(() => {});
  }, [open]);

  const handleUpgrade = () => {
    onOpenChange(false);
    navigate("/profile");
  };

  const handleExport = () => {
    onExport?.();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{plan === "pro" ? "Export Video" : "Upgrade to Export"}</DialogTitle>
          <DialogDescription>
            {plan === "pro"
              ? "Download your generated animation as MP4."
              : "Video export is a Pro feature. Upgrade to unlock downloads and HD quality."}
          </DialogDescription>
        </DialogHeader>

        {plan !== "pro" && (
          <div className="flex flex-col gap-3 py-2 text-sm">
            {["Unlimited video exports", "1080p HD quality", "Priority generation"].map((f) => (
              <div key={f} className="flex items-center gap-2">
                <BadgeCheck size={16} className="text-primary" />
                {f}
              </div>
            ))}
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          {plan === "pro" ? (
            <Button onClick={handleExport} className="gap-2">
              <Download size={16} />
              Download MP4
            </Button>
          ) : (
            <Button onClick={handleUpgrade} className="gap-2">
              <BadgeCheck size={16} />
              Upgrade to Pro
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ExportModal;
