import { Navigate, Route, Routes } from "react-router-dom";
import { isAuthenticated } from "./lib/auth";
import { AppLayout } from "./components/layouts/AppLayout";
import { AuthLayout } from "./components/layouts/AuthLayout";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { GoogleCallback } from "./pages/GoogleCallback";
import { Onboarding } from "./pages/Onboarding";
import { Dashboard } from "./pages/Dashboard";
import { Swipe } from "./pages/Swipe";
import { Liked } from "./pages/Liked";
import { Feed } from "./pages/Feed";
import { Collections } from "./pages/Collections";
import { AgentProfile } from "./pages/AgentProfile";
import { NewAgent } from "./pages/NewAgent";
import { Settings } from "./pages/Settings";
import { AdminVerification } from "./pages/AdminVerification";
import { AdminReports } from "./pages/AdminReports";
import { MyAgents } from "./pages/MyAgents";

export default function App() {
  return (
    <Routes>
      {/* Public pages */}
      <Route path="/" element={<Landing />} />

      {/* Auth pages (centered card layout) */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>

      {/* OAuth callback (no layout) */}
      <Route path="/oauth/google/callback" element={<GoogleCallback />} />

      {/* Authenticated pages (sidebar layout) */}
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/swipe" element={<Swipe />} />
        <Route path="/liked" element={<Liked />} />
        <Route path="/collections" element={<Collections />} />
        <Route path="/feed" element={<Feed />} />
        <Route path="/agents/mine" element={<MyAgents />} />
        <Route path="/agents/new" element={<NewAgent />} />
        <Route path="/agents/:slug" element={<AgentProfile />} />
        <Route path="/settings/profile" element={<Settings />} />
        <Route path="/admin/verification" element={<AdminVerification />} />
        <Route path="/admin/reports" element={<AdminReports />} />
      </Route>

      {/* Fallback */}
      <Route
        path="*"
        element={<Navigate to={isAuthenticated() ? "/dashboard" : "/"} replace />}
      />
    </Routes>
  );
}
