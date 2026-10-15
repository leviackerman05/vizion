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

export type UserProfile = {
  user_id: string;
  email?: string;
  plan: string;
  daily_count: number;
  daily_limit: number | null;
  remaining: number | null;
};

export async function fetchMe(): Promise<UserProfile> {
  const res = await fetch(`${BASE_URL}/me`, { headers: getAuthHeaders() });
  if (!res.ok) {
    handleUnauthorized(res.status);
    throw new Error("Failed to fetch profile");
  }
  return res.json();
}

export async function startCheckout(): Promise<string> {
  const res = await fetch(`${BASE_URL}/billing/create-checkout-session`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Checkout unavailable");
  }
  const data = await res.json();
  return data.url;
}

export async function openBillingPortal(): Promise<string> {
  const res = await fetch(`${BASE_URL}/billing/portal`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("No billing account found");
  const data = await res.json();
  return data.url;
}
