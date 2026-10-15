import { handleUnauthorized } from "./auth";

import { getApiUrl } from "./config";

const BASE_URL = getApiUrl();

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function handleResponse(res: Response) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    handleUnauthorized(res.status);
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : `Request failed (${res.status})`;
    throw new Error(detail);
  }
  return data;
}

export function toVideoUrl(path: string): string {
  if (!path || path === "undefined") return "";
  if (path.startsWith("http")) return path;
  return `${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

/** Map a stream URL to an explicit download endpoint (user-initiated only). */
export function toDownloadUrl(streamUrl: string): string {
  const full = toVideoUrl(streamUrl);
  const match = full.match(/\/videos\/([a-f0-9]+)\/stream/);
  if (match) return `${BASE_URL}/videos/${match[1]}/download`;
  return full;
}

export async function downloadVideoFile(streamUrl: string, filename = "vizion-animation.mp4") {
  const downloadUrl = toDownloadUrl(streamUrl);
  const isServerDownload = downloadUrl.includes("/download");

  const res = await fetch(downloadUrl, {
    headers: isServerDownload ? getAuthHeaders() : undefined,
  });
  if (!res.ok) throw new Error("Download failed");

  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(objectUrl);
}

export const fetchUserChats = async () => {
  const res = await fetch(`${BASE_URL}/chats`, { headers: getAuthHeaders() });
  return handleResponse(res);
};

export const fetchChatMessages = async (chatId: string) => {
  const res = await fetch(`${BASE_URL}/chatdata/${chatId}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
};

export const deleteChat = async (chatId: string) => {
  const res = await fetch(`${BASE_URL}/chats/${chatId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
};

export const renameChat = async (chatId: string, title: string) => {
  const res = await fetch(`${BASE_URL}/chats/${chatId}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify({ title }),
  });
  return handleResponse(res);
};

export type StreamEvent = {
  stage: string;
  message: string;
  chat_id?: string;
  video_url?: string;
  script?: string;
  metadata?: Record<string, string>;
};

export const sendUserPromptStream = async (
  chatId: string | null,
  prompt: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal
): Promise<StreamEvent | null> => {
  const res = await fetch(`${BASE_URL}/chat/stream`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ chat_id: chatId, prompt }),
    signal,
  });

  if (!res.ok) {
    handleUnauthorized(res.status);
    const data = await res.json().catch(() => ({}));
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : res.status === 500
          ? "Server error — try again or check backend logs"
          : `Request failed (${res.status})`;
    throw new Error(detail);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response stream");

  const decoder = new TextDecoder();
  let buffer = "";
  let finalEvent: StreamEvent | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const event: StreamEvent = JSON.parse(line.slice(6));
        onEvent(event);
        if (event.stage === "done") finalEvent = event;
        if (event.stage === "error") throw new Error(event.message);
      } catch (e) {
        if (e instanceof Error && e.message !== "Unexpected end of JSON input") throw e;
      }
    }
  }
  return finalEvent;
};

export const fetchVideoFromLatestCode = async (chatId: string) => {
  const messages = await fetchChatMessages(chatId);
  const list = Array.isArray(messages) ? messages : messages.messages ?? [];
  const latest = [...list]
    .reverse()
    .find((m: { video_url?: string }) => m.video_url);
  if (!latest?.video_url) throw new Error("No video found for this chat");
  return { videoUrl: latest.video_url };
};
