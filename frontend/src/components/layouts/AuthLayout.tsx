import { Outlet, NavLink } from "react-router-dom";
import { Zap } from "lucide-react";

export function AuthLayout() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 grid-bg relative">
      {/* Ambient glow orbs */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-accent/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-brown/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Brand */}
      <NavLink to="/" className="flex items-center gap-2.5 mb-8">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-accent to-brown flex items-center justify-center">
          <Zap size={20} className="text-white" />
        </div>
        <span className="text-2xl font-bold gradient-text">AgentSwipe</span>
      </NavLink>

      {/* Form card */}
      <div className="w-full max-w-md glass rounded-2xl p-8 glow-sm">
        <Outlet />
      </div>
    </div>
  );
}
