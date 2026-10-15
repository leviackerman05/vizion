import { useRef, useState } from "react";
import { Download, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VIDEO } from "@/constants/strings";
import { VideoMetadata } from "@/types";
import { downloadVideoFile } from "@/lib/api/chats";

type VideoPlayerProps = {
  videoSrc?: string;
  metadata: VideoMetadata;
};

const VideoPlayer = ({ videoSrc, metadata }: VideoPlayerProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    if (!videoSrc || downloading) return;
    setDownloading(true);
    try {
      await downloadVideoFile(videoSrc);
    } catch {
      // Silent fail — user can retry
    } finally {
      setDownloading(false);
    }
  };

  const handleFullscreen = () => {
    videoRef.current?.requestFullscreen();
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 relative bg-black/90 m-3 rounded-lg overflow-hidden">
        {videoSrc ? (
          <video
            ref={videoRef}
            src={videoSrc}
            controls
            autoPlay
            preload="metadata"
            playsInline
            className="absolute inset-0 w-full h-full object-contain"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-white/40 text-sm">
            No video
          </div>
        )}
      </div>

      <div className="px-4 pb-4 space-y-3">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleDownload} disabled={!videoSrc || downloading}>
            <Download size={14} className="mr-1.5" />
            {downloading ? "Downloading..." : VIDEO.DOWNLOAD}
          </Button>
          <Button variant="outline" size="sm" onClick={handleFullscreen} disabled={!videoSrc}>
            <Maximize2 size={14} className="mr-1.5" />
            {VIDEO.FULLSCREEN}
          </Button>
        </div>

        <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">{VIDEO.METADATA.RESOLUTION}</span>
            <span className="font-medium">{metadata.resolution}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">{VIDEO.METADATA.FORMAT}</span>
            <span className="font-medium">{metadata.format}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">{VIDEO.METADATA.SIZE}</span>
            <span className="font-medium">{metadata.size}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">{VIDEO.METADATA.DURATION}</span>
            <span className="font-medium">{metadata.duration}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;
