import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mail, Lock } from "lucide-react";
import { APP } from "@/constants/strings";
import { validateSignupEmail } from "@/utils/emailValidation";
import { getApiUrl } from "@/lib/api/config";

function parseApiError(data: unknown, fallback: string): string {
  if (!data || typeof data !== "object") return fallback;
  const record = data as Record<string, unknown>;
  if (typeof record.detail === "string") return record.detail;
  if (Array.isArray(record.detail) && record.detail.length > 0) {
    const first = record.detail[0] as { msg?: string };
    if (first.msg) return first.msg.replace(/^Value error,\s*/i, "");
  }
  return fallback;
}

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSignup = async () => {
    setError("");
    const emailError = validateSignupEmail(email);
    if (emailError) {
      setError(emailError);
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${getApiUrl()}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
      });
      const result = await res.json();
      if (!res.ok) {
        const message = parseApiError(result, "Signup failed");
        setError(message);
        toast.error(message);
        return;
      }
      toast.success("Account created! You can now sign in.");
      navigate("/login");
    } catch {
      const message = "Cannot reach backend. Is the API running?";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 p-8">
        <div className="text-center space-y-1">
          <div className="mx-auto w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-bold text-lg mb-4">
            V
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Create account</h1>
          <p className="text-sm text-muted-foreground">Join {APP.NAME} — it's free</p>
        </div>

        <div className="space-y-3">
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
            <Input
              type="email"
              placeholder="you@gmail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="pl-10"
              onKeyDown={(e) => e.key === "Enter" && handleSignup()}
            />
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
            <Input
              type="password"
              placeholder="Password (min 6 characters)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="pl-10"
              onKeyDown={(e) => e.key === "Enter" && handleSignup()}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            Supported: Gmail, Outlook, Yahoo, iCloud, Proton, and .edu school emails.
          </p>
          {error && <p className="text-destructive text-sm">{error}</p>}
          <Button className="w-full" onClick={handleSignup} disabled={loading}>
            {loading ? "Creating account..." : "Create account"}
          </Button>
        </div>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <a href="/login" className="text-primary hover:underline">
            Sign in
          </a>
        </p>
      </div>
    </div>
  );
}
