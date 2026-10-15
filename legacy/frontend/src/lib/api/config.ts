/** Backend API base URL. Set VITE_API_URL in production (e.g. Railway). */
export function getApiUrl(): string {
  const url = import.meta.env.VITE_API_URL as string | undefined;
  if (url?.trim()) return url.trim().replace(/\/$/, "");
  return "http://localhost:8000";
}
