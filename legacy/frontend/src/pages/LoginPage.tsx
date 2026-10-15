import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mail, Lock } from "lucide-react";
import { APP } from "@/constants/strings";
import { getApiUrl } from "@/lib/api/config";
import { consumeAuthRedirectMessage } from "@/lib/api/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const msg = consumeAuthRedirectMessage();
    if (msg) {
      setError(msg);
      toast.error(msg);
    }
  }, []);

  const handleLogin = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${getApiUrl()}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Invalid credentials");

      localStorage.setItem("token", data.access_token);
      localStorage.setItem("uid", data.user?.id ?? "");
      localStorage.setItem("active_plan", data.active_plan ?? "free");
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      toast.error("Login failed");
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
          <h1 className="text-2xl font-semibold tracking-tight">Welcome to {APP.NAME}</h1>
          <p className="text-sm text-muted-foreground">{APP.TAGLINE}</p>
        </div>

        <div className="space-y-3">
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="pl-10"
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            />
          </div>
          {error && <p className="text-destructive text-sm">{error}</p>}
          <Button className="w-full" onClick={handleLogin} disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </div>

        <p className="text-center text-sm text-muted-foreground">
          No account?{" "}
          <a href="/signup" className="text-primary hover:underline">
            Sign up
          </a>
        </p>
      </div>
    </div>
  );
}
