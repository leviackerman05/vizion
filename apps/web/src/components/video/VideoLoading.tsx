
import { VIDEO } from "@/constants/strings";

const VideoLoading = () => {
  return (
    <div className="h-full flex flex-col items-center justify-center p-8">
      <div className="relative w-24 h-24 mb-4">
        <div className="absolute inset-0 rounded-full border-4 border-muted"></div>
        <div className="absolute inset-0 rounded-full border-4 border-t-primary border-r-transparent border-b-transparent border-l-transparent animate-spin-slow"></div>
      </div>
      <p className="text-lg font-medium animate-pulse-slow">
        {VIDEO.GENERATING}
      </p>
    </div>
  );
};

export default VideoLoading;
