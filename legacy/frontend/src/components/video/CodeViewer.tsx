import { Copy, Check } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

type CodeViewerProps = {
  code: string;
};

const CodeViewer = ({ code }: CodeViewerProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!code) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
        No code generated yet
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col m-3">
      <div className="flex justify-end mb-2">
        <Button variant="outline" size="sm" onClick={handleCopy}>
          {copied ? <Check size={14} className="mr-1" /> : <Copy size={14} className="mr-1" />}
          {copied ? "Copied" : "Copy code"}
        </Button>
      </div>
      <pre className="flex-1 overflow-auto rounded-lg bg-muted/40 border border-border/50 p-4 text-xs font-mono leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
};

export default CodeViewer;
