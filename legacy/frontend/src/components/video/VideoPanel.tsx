import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { VIDEO } from "@/constants/strings";
import { VideoMetadata } from "@/types";
import VideoPlayer from "./VideoPlayer";
import CodeViewer from "./CodeViewer";

type VideoPanelProps = {
  videoState: "idle" | "generating" | "ready" | "error";
  videoSrc?: string;
  script?: string;
  metadata: VideoMetadata | null;
  errorMessage?: string;
};

const VideoPanel = ({
  videoState,
  videoSrc,
  script,
  metadata,
  errorMessage,
}: VideoPanelProps) => {
  if (videoState === "idle") return null;

  if (videoState === "generating") {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4 text-muted-foreground">
        <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        <p className="text-sm animate-pulse">{VIDEO.GENERATING}</p>
      </div>
    );
  }

  if (videoState === "error") {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3 p-8 text-center">
        <div className="text-destructive text-4xl">⚠</div>
        <p className="font-medium text-destructive">{VIDEO.ERROR}</p>
        <p className="text-sm text-muted-foreground max-w-sm">{errorMessage}</p>
      </div>
    );
  }

  return (
    <Tabs defaultValue="preview" className="h-full flex flex-col">
      <TabsList className="mx-4 mt-3 w-fit">
        <TabsTrigger value="preview">{VIDEO.PREVIEW}</TabsTrigger>
        <TabsTrigger value="code" disabled={!script}>{VIDEO.CODE}</TabsTrigger>
      </TabsList>
      <TabsContent value="preview" className="flex-1 mt-0 overflow-hidden">
        <VideoPlayer videoSrc={videoSrc} metadata={metadata!} />
      </TabsContent>
      <TabsContent value="code" className="flex-1 mt-0 overflow-hidden">
        <CodeViewer code={script || ""} />
      </TabsContent>
    </Tabs>
  );
};

export default VideoPanel;
