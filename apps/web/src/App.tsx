import { Component, ErrorInfo, ReactNode, useEffect, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { api, ApiError } from "./api";
import { AuthScreen, Brand } from "./AuthScreen";
import { Studio } from "./Studio";
import type { User } from "./types";

class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(error, info.componentStack);
  }
  render() {
    return this.state.failed ? (
      <main className="boot">
        <Brand />
        <h2>The workspace hit a problem.</h2>
        <p>Your projects are saved on the server.</p>
        <button
          className="button primary"
          onClick={() => window.location.reload()}
        >
          Reload workspace
        </button>
      </main>
    ) : (
      this.props.children
    );
  }
}

function Workspace() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expired, setExpired] = useState("");
  useEffect(() => {
    let live = true;
    api<{ user: User }>("/auth/me")
      .then((result) => {
        if (live) setUser(result.user);
      })
      .catch((err) => {
        if (live && !(err instanceof ApiError && err.status === 401))
          setError(
            "Cannot reach your workspace. Check your connection and try again.",
          );
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    const onExpired = () => {
      setUser(null);
      setExpired(
        "Your session expired. Sign in to continue; your projects are saved.",
      );
    };
    window.addEventListener("vizion:session-expired", onExpired);
    return () => {
      live = false;
      window.removeEventListener("vizion:session-expired", onExpired);
    };
  }, []);
  if (loading)
    return (
      <main className="boot">
        <Brand />
        <LoaderCircle className="spin" />
        <p>Opening your workspace…</p>
      </main>
    );
  if (error)
    return (
      <main className="boot">
        <Brand />
        <p role="alert">{error}</p>
        <button
          className="button primary"
          onClick={() => window.location.reload()}
        >
          Try again
        </button>
      </main>
    );
  return user ? (
    <Studio user={user} onLogout={() => setUser(null)} />
  ) : (
    <AuthScreen onLogin={setUser} message={expired} />
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <Workspace />
    </ErrorBoundary>
  );
}
