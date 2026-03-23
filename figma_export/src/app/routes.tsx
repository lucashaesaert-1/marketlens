import { createBrowserRouter, Navigate, useParams } from "react-router";
import { Dashboard } from "./components/Dashboard";
import { Layout } from "./components/Layout";
import { LoginPage } from "./components/LoginPage";
import { OnboardingPage } from "./components/OnboardingPage";
import { ProtectedLayout } from "./components/ProtectedLayout";

/** Must not collide with dynamic `/:industry` (e.g. /onboarding was treated as an industry). */
const RESERVED_INDUSTRY_SLUGS = new Set(["onboarding", "setup"]);

function RedirectToAudience() {
  const { industry } = useParams();
  if (industry && RESERVED_INDUSTRY_SLUGS.has(industry)) {
    return <Navigate to="/onboarding" replace />;
  }
  return <Navigate to={`/${industry}/investors`} replace />;
}

function DashboardGate() {
  const { industry } = useParams();
  if (industry && RESERVED_INDUSTRY_SLUGS.has(industry)) {
    return <Navigate to="/onboarding" replace />;
  }
  return <Dashboard />;
}

export const router = createBrowserRouter([
  { path: "/login", Component: LoginPage },
  {
    path: "/",
    Component: ProtectedLayout,
    children: [
      { path: "onboarding", Component: OnboardingPage },
      { path: "setup", Component: OnboardingPage },
      {
        Component: Layout,
        children: [
          { index: true, element: <Navigate to="crm/investors" replace /> },
          { path: ":industry", Component: RedirectToAudience },
          { path: ":industry/:audience", Component: DashboardGate },
        ],
      },
    ],
  },
]);
