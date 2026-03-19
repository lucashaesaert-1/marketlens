import { createBrowserRouter, Navigate, useParams } from "react-router";
import { Dashboard } from "./components/Dashboard";
import { Layout } from "./components/Layout";

function RedirectToAudience() {
  const { industry } = useParams();
  return <Navigate to={`/${industry}/investors`} replace />;
}

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      {
        index: true,
        element: <Navigate to="/crm/investors" replace />,
      },
      {
        path: ":industry",
        element: <RedirectToAudience />,
      },
      {
        path: ":industry/:audience",
        Component: Dashboard,
      },
    ],
  },
]);
