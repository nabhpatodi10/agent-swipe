import { NavLink, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Compass,
  Heart,
  FolderOpen,
  Newspaper,
  Bot,
  PlusCircle,
  Settings,
  ShieldCheck,
  Flag,
  LogOut,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { clearAccessToken } from "../../lib/auth";
import { cn } from "../../lib/utils";
import type { User } from "../../lib/types";

interface SidebarProps {
  user?: User | null;
}

interface NavItem {
  to: string;
  icon: LucideIcon;
  label: string;
  admin?: boolean;
}

const mainNav: NavItem[] = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/swipe", icon: Compass, label: "Discover" },
  { to: "/liked", icon: Heart, label: "Liked" },
  { to: "/collections", icon: FolderOpen, label: "Collections" },
  { to: "/feed", icon: Newspaper, label: "Feed" },
];

const createNav: NavItem[] = [
  { to: "/agents/mine", icon: Bot, label: "Your Agents" },
  { to: "/agents/new", icon: PlusCircle, label: "New Agent" },
];

const adminNav: NavItem[] = [
  { to: "/admin/verification", icon: ShieldCheck, label: "Verification", admin: true },
  { to: "/admin/reports", icon: Flag, label: "Reports", admin: true },
];

function SidebarLink({ to, icon: Icon, label }: NavItem) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
          isActive
            ? "bg-accent/15 text-accent-light"
            : "text-text-secondary hover:text-text-primary hover:bg-surface-200/50",
        )
      }
    >
      {({ isActive }) => (
        <>
          <Icon size={18} className={isActive ? "text-accent-light" : ""} />
          <span>{label}</span>
          {isActive && (
            <motion.div
              layoutId="sidebar-indicator"
              className="absolute left-0 w-[3px] h-6 rounded-r-full bg-accent"
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            />
          )}
        </>
      )}
    </NavLink>
  );
}

export function Sidebar({ user }: SidebarProps) {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAccessToken();
    navigate("/");
  };

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 border-r border-border bg-surface-50/80 backdrop-blur-xl z-40 flex flex-col">
      {/* Brand */}
      <div className="px-5 py-6 border-b border-border/50">
        <NavLink to="/dashboard" className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-accent to-brown flex items-center justify-center">
            <Zap size={18} className="text-white" />
          </div>
          <span className="text-lg font-bold gradient-text">AgentSwipe</span>
        </NavLink>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <p className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
          Main
        </p>
        {mainNav.map((item) => (
          <SidebarLink key={item.to} {...item} />
        ))}

        <div className="h-px bg-border/50 my-4" />
        <p className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
          Create
        </p>
        {createNav.map((item) => (
          <SidebarLink key={item.to} {...item} />
        ))}

        {user?.is_superuser && (
          <>
            <div className="h-px bg-border/50 my-4" />
            <p className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Admin
            </p>
            {adminNav.map((item) => (
              <SidebarLink key={item.to} {...item} />
            ))}
          </>
        )}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-border/50 space-y-1">
        <NavLink
          to="/settings/profile"
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
              isActive
                ? "bg-accent/15 text-accent-light"
                : "text-text-secondary hover:text-text-primary hover:bg-surface-200/50",
            )
          }
        >
          <Settings size={18} />
          <span>Settings</span>
        </NavLink>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-text-secondary hover:text-danger hover:bg-danger/10 transition-all duration-200"
        >
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
