export type ChatMessage = {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: Date;
  status?: "generating" | "done" | "error";
};

export type ChatHistory = {
  id: string;
  title: string;
  lastMessage: string;
  timestamp?: Date;
};

export type VideoMetadata = {
  duration: string;
  resolution: string;
  format: string;
  size: string;
};

export type VideoState = "idle" | "generating" | "ready" | "error";

export type UserPlan = "free" | "pro";

export type GenerationStatus = {
  stage: string;
  message: string;
};
