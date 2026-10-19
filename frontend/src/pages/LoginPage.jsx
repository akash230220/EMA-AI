import * as React from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, Sparkles, CalendarClock, CheckSquare, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import authApi from "@/api/authApi";
import { useAuth } from "@/context/AuthContext";

const FEATURES = [
  { icon: Sparkles, label: "AI-powered categorization & priority detection" },
  { icon: CalendarClock, label: "Automatic meeting detection & calendar sync" },
  { icon: CheckSquare, label: "Task extraction from your inbox" },
  { icon: BarChart3, label: "Analytics on response time & AI time saved" },
];

/**
 * Login page — single "Continue with Google" CTA (OAuth 2.0 only,
 * no email/password). Handles the OAuth callback when Google
 * redirects back with `?code=...`, exchanging it for a session.
 */
export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const { setUser } = useAuth();
  const [isExchanging, setIsExchanging] = React.useState(false);
  const [error, setError] = React.useState(null);
  const exchangeStartedRef = React.useRef(false);

  const code = searchParams.get("code");
  const oauthError = searchParams.get("error");

  React.useEffect(() => {
    if (oauthError) {
      setError("Google sign-in was cancelled or denied. Please try again.");
      return;
    }
    if (!code) return;
    if (exchangeStartedRef.current) return;

    exchangeStartedRef.current = true;

    setIsExchanging(true);
    authApi
      .exchangeCodeForToken(code)
      .then((data) => {
        setUser(data.user);
        window.location.replace("/dashboard");
      })
      .catch(() => {
        setError("Something went wrong signing you in. Please try again.");
        setIsExchanging(false);
      });
  }, [code, oauthError, setUser]);

  if (isExchanging) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-violet-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          <p className="text-sm text-muted-foreground">Signing you in...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-full bg-gradient-to-br from-indigo-50 via-white to-violet-50">
      <div className="mx-auto flex w-full max-w-5xl flex-col items-center justify-center gap-10 px-6 py-12 lg:flex-row lg:items-stretch lg:gap-16">
        {/* Left: brand + features */}
        <motion.div
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className="flex flex-1 flex-col justify-center"
        >
          <div className="mb-6 flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white">
              <Mail className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold tracking-tight">AI Email OS</span>
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-foreground lg:text-4xl">
            Your inbox, run by AI.
          </h1>
          <p className="mt-3 max-w-md text-muted-foreground">
            Automatically categorize, prioritize, and reply to your emails — with meetings and
            tasks extracted for you.
          </p>

          <div className="mt-8 space-y-3">
            {FEATURES.map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white shadow-sm">
                  <Icon className="h-4 w-4 text-indigo-600" />
                </div>
                <span className="text-sm text-foreground">{label}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Right: login card */}
        <motion.div
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="flex flex-1 items-center justify-center"
        >
          <Card className="w-full max-w-sm shadow-lg">
            <CardContent className="p-8">
              <h2 className="text-lg font-semibold">Welcome back</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Sign in with Google to connect your inbox and calendar.
              </p>

              {error && (
                <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
                  {error}
                </div>
              )}

              <Button
                className="mt-6 w-full gap-2 bg-indigo-600 hover:bg-indigo-700 text-white"
                size="lg"
                onClick={() => authApi.loginWithGoogle()}
              >
                <GoogleIcon />
                Continue with Google
              </Button>

              <div className="relative my-4 flex items-center justify-center">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border" />
                </div>
                <span className="relative bg-card px-2 text-[11px] uppercase tracking-wider text-muted-foreground">
                  Or Local Dev / Demo
                </span>
              </div>

              <Button
                variant="outline"
                className="w-full gap-2 border-indigo-200 text-indigo-600 hover:bg-indigo-50"
                size="lg"
                onClick={async () => {
                  try {
                    setIsExchanging(true);
                    const data = await authApi.devLogin();
                    setUser(data.user);
                    window.location.replace("/dashboard");
                  } catch (err) {
                    setError(err?.message || "Demo sign in failed.");
                    setIsExchanging(false);
                  }
                }}
              >
                <Sparkles className="h-4 w-4 text-indigo-600" />
                Demo Sign-In (Alex Mercer)
              </Button>

              <p className="mt-4 text-center text-[11px] text-muted-foreground">
                By continuing, you agree to grant access to your Gmail and Calendar for AI
                processing. You can revoke access anytime in Settings.
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.25 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.85A11 11 0 0012 23z" />
      <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 010-4.2V7.05H2.18a11 11 0 000 9.9l3.66-2.85z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1a11 11 0 00-9.82 6.05l3.66 2.85C6.71 7.31 9.14 5.38 12 5.38z" />
    </svg>
  );
}