export function clearSessionAndRedirect(message = "Session expired. Please sign in again.") {
  localStorage.removeItem("token");
  localStorage.removeItem("uid");
  localStorage.removeItem("active_plan");
  if (window.location.pathname !== "/login" && window.location.pathname !== "/signup") {
    sessionStorage.setItem("auth_redirect_message", message);
    window.location.href = "/login";
  }
}

export function consumeAuthRedirectMessage(): string | null {
  const msg = sessionStorage.getItem("auth_redirect_message");
  if (msg) sessionStorage.removeItem("auth_redirect_message");
  return msg;
}

export function handleUnauthorized(status: number) {
  if (status === 401) {
    clearSessionAndRedirect();
    throw new Error("Session expired. Please sign in again.");
  }
}
