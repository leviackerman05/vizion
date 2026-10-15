export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-Vizion-Client": "web",
      ...options.headers,
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
          ? data.detail.map((item: { msg: string }) => item.msg).join(". ")
          : "The request could not be completed. Please try again.";
    if (response.status === 401 && !path.startsWith("/auth/")) {
      window.dispatchEvent(new Event("vizion:session-expired"));
    }
    throw new ApiError(message, response.status);
  }
  return data as T;
}

export const post = <T>(
  path: string,
  body?: unknown,
  headers?: Record<string, string>,
) =>
  api<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
    headers,
  });
