
import { ChatMessage, VideoMetadata } from "@/types";

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "numeric",
  }).format(date);
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}

export function createUserMessage(text: string): ChatMessage {
  return {
    id: generateId(),
    sender: "user",
    text,
    timestamp: new Date(),
  };
}

export function createAiMessage(
  text: string,
  status?: "generating" | "done" | "error"
): ChatMessage {
  return {
    id: generateId(),
    sender: "ai",
    text,
    timestamp: new Date(),
    status,
  };
}

export function simulateVideoGeneration(): Promise<VideoMetadata> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        duration: "0:48",
        resolution: "1920x1080",
        format: "MP4",
        size: "24.3 MB",
      });
    }, 5000);
  });
}
