import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router";
import { getToken, fetchProfile, type UserProfile } from "../auth";
import { Loader2 } from "lucide-react";

/** Requires JWT; incomplete onboarding is sent to /onboarding. */
export function ProtectedLayout() {
  const loc = useLocation();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [authState, setAuthState] = useState<"loading" | "ok" | "login">("loading");

  useEffect(() => {
    const t = getToken();
    if (!t) {
      setAuthState("login");
      setProfile(null);
      return;
    }
    fetchProfile()
      .then((p) => {
        setProfile(p);
        setAuthState("ok");
      })
      .catch(() => setAuthState("login"));
  }, []);

  if (authState === "login") {
    return <Navigate to="/login" replace state={{ from: loc }} />;
  }

  if (authState === "loading" || !profile) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <Loader2 className="w-10 h-10 animate-spin text-[#990F3D]" />
      </div>
    );
  }

  const onOnboardingPath =
    loc.pathname === "/onboarding" || loc.pathname === "/setup";

  if (!profile.onboarding_completed && !onOnboardingPath) {
    return <Navigate to="/onboarding" replace />;
  }

  if (profile.onboarding_completed && onOnboardingPath) {
    const ind = profile.industry || "crm";
    const aud = (profile.audience as string) || "investors";
    return <Navigate to={`/${ind}/${aud}`} replace />;
  }

  return <Outlet />;
}
