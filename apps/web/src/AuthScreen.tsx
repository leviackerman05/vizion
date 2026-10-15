import { FormEvent, useState } from "react";
import {
  ArrowRight,
  Check,
  Copy,
  Eye,
  EyeOff,
  Film,
  KeyRound,
  LoaderCircle,
  MoveUpRight,
} from "lucide-react";
import { post } from "./api";
import type { User } from "./types";

export function Brand() {
  return (
    <span className="brand">
      <span className="brand-symbol">
        <i />
        <i />
        <i />
      </span>
      vizion<span className="brand-dot">.</span>
    </span>
  );
}

export function AuthScreen({
  onLogin,
  message = "",
}: {
  onLogin: (user: User) => void;
  message?: string;
}) {
  const [mode, setMode] = useState<"login" | "register" | "recover">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [recoveryInput, setRecoveryInput] = useState("");
  const [recovery, setRecovery] = useState("");
  const [pendingUser, setPendingUser] = useState<User | null>(null);
  const [error, setError] = useState(message);
  const [pending, setPending] = useState(false);
  const [visible, setVisible] = useState(false);
  const [copied, setCopied] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setPending(true);
    try {
      const result = await post<{ user?: User; recovery_code?: string }>(
        `/auth/${mode}`,
        {
          email,
          password,
          ...(mode === "recover" ? { recovery_code: recoveryInput } : {}),
        },
      );
      if (result.recovery_code) {
        setRecovery(result.recovery_code);
        setPendingUser(result.user ?? null);
      } else if (result.user) onLogin(result.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Please try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <Brand />
        <div className="auth-story-copy">
          <span className="eyebrow">
            <span className="live-dot" /> THE EXPLAINER STUDIO
          </span>
          <h1>
            Some ideas
            <br />
            need to be <em>seen.</em>
          </h1>
          <p>
            Turn a topic into a clear, narrated animation.
            <br />
            Make the next “aha” moment yours.
          </p>
        </div>
        <div
          className="auth-illustration"
          aria-label="Illustration of a quadratic function"
        >
          <svg viewBox="0 0 520 220" aria-hidden="true">
            <defs>
              <pattern
                id="authGrid"
                width="35"
                height="35"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 35 0 L 0 0 0 35"
                  fill="none"
                  stroke="#27312b"
                  strokeWidth=".7"
                />
              </pattern>
            </defs>
            <rect width="520" height="220" fill="url(#authGrid)" />
            <path d="M40 175H475M115 200V20" stroke="#62716a" strokeWidth="1" />
            <path
              d="M115 175 Q245 175 355 25"
              fill="none"
              stroke="#ccf478"
              strokeWidth="3"
            />
            <circle cx="265" cy="103" r="6" fill="#ccf478" />
            <text
              x="320"
              y="150"
              fill="#edf1e8"
              fontSize="29"
              fontFamily="serif"
            >
              f(x) = x²
            </text>
          </svg>
          <span>
            <Film size={14} /> From a simple rule to a moving explanation{" "}
            <MoveUpRight size={14} />
          </span>
        </div>
        <div className="auth-footnote">
          A little curiosity. A clearer picture.
        </div>
      </section>
      <section className="auth-form-side">
        <div className="mobile-brand">
          <Brand />
        </div>
        <div className="auth-form-wrap">
          {recovery ? (
            <>
              <div className="icon-tile">
                <KeyRound size={25} />
              </div>
              <h2>Keep your recovery code.</h2>
              <p className="muted">
                Save this somewhere private. It lets you reset your password
                without relying on email delivery. This code is only shown once.
              </p>
              <div className="recovery-code">
                <code>{recovery}</code>
                <button
                  type="button"
                  className="icon-button"
                  aria-label="Copy recovery code"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(recovery);
                      setCopied(true);
                    } catch {
                      setError("Select and copy your recovery code manually.");
                    }
                  }}
                >
                  {copied ? <Check size={17} /> : <Copy size={17} />}
                </button>
              </div>
              <button
                className="button primary wide"
                onClick={() => {
                  if (pendingUser) onLogin(pendingUser);
                  else {
                    setRecovery("");
                    setMode("login");
                    setPassword("");
                  }
                }}
              >
                I saved my code <ArrowRight size={17} />
              </button>
            </>
          ) : (
            <>
              <span className="eyebrow muted">
                YOUR NEXT EXPLANATION STARTS HERE
              </span>
              <h2>
                {mode === "register"
                  ? "Make room for ideas."
                  : mode === "recover"
                    ? "Find your way back."
                    : "Welcome back."}
              </h2>
              <p className="muted">
                {mode === "register"
                  ? "Create your free workspace and bring a concept to life."
                  : mode === "recover"
                    ? "Use the recovery code saved when you created your account."
                    : "Sign in to your workspace. Your lessons are waiting."}
              </p>
              <form onSubmit={submit} className="auth-form">
                <label>
                  Email address
                  <input
                    required
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    maxLength={254}
                  />
                </label>
                {mode === "recover" && (
                  <label>
                    Recovery code
                    <input
                      required
                      value={recoveryInput}
                      onChange={(event) => setRecoveryInput(event.target.value)}
                      autoComplete="off"
                    />
                  </label>
                )}
                <label>
                  {mode === "recover" ? "New password" : "Password"}
                  <span className="password-field">
                    <input
                      aria-label={
                        mode === "recover" ? "New password" : "Password"
                      }
                      required
                      type={visible ? "text" : "password"}
                      minLength={8}
                      maxLength={128}
                      autoComplete={
                        mode === "login" ? "current-password" : "new-password"
                      }
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      placeholder="At least 8 characters"
                    />
                    <button
                      type="button"
                      className="icon-button"
                      aria-label={visible ? "Hide password" : "Show password"}
                      onClick={() => setVisible(!visible)}
                    >
                      {visible ? <EyeOff size={17} /> : <Eye size={17} />}
                    </button>
                  </span>
                </label>
                {error && (
                  <div role="alert" className="error-box">
                    {error}
                  </div>
                )}
                <button className="button primary wide" disabled={pending}>
                  {pending ? (
                    <LoaderCircle size={17} className="spin" />
                  ) : (
                    <ArrowRight size={17} />
                  )}
                  {mode === "register"
                    ? "Create workspace"
                    : mode === "recover"
                      ? "Reset password"
                      : "Sign in"}
                </button>
              </form>
              <p className="auth-switch">
                {mode === "login"
                  ? "New to Vizion?"
                  : "Already have an account?"}{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode(mode === "login" ? "register" : "login");
                    setError("");
                  }}
                >
                  {mode === "login" ? "Create an account" : "Sign in"}
                </button>
              </p>
              {mode === "login" && (
                <button
                  className="text-button subtle"
                  onClick={() => {
                    setMode("recover");
                    setError("");
                  }}
                >
                  Reset password with a recovery code
                </button>
              )}
            </>
          )}
        </div>
        <span className="auth-bottom">
          Built for curious minds, everywhere.
        </span>
      </section>
    </main>
  );
}
