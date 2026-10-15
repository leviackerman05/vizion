import { getApiUrl } from "@/lib/api/config";

export async function login(email: string, password: string) {
  const res = await fetch(`${getApiUrl()}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) throw new Error("Invalid credentials");

  const data = await res.json();
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("uid", data.user?.id ?? "");
}
