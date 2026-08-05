/**
 * FinPilot AI — App Shell Layout
 * ================================
 * Main layout wrapper with:
 * - Animated sidebar navigation
 * - Top navigation bar
 * - Command palette (Cmd+K)
 * - Notification center
 * - Theme toggle
 */

import React, { useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useDispatch, useSelector } from "react-redux";

import {
  LayoutDashboard, MessageSquare, FileText, Workflow, BarChart3,
  Settings, Shield, Bell, Search, Moon, Sun, LogOut, ChevronLeft,
  Bot, Zap, TrendingUp, AlertTriangle, Menu, X,
} from "lucide-react";

import { RootState } from "@/app/store";
import { toggleSidebar, toggleTheme, setSidebarCollapsed, setCommandPaletteOpen } from "@/app/slices/uiSlice";
import { logout } from "@/app/slices/authSlice";
import CommandPalette from "./CommandPalette";

// ── Navigation Items ──────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { path: "/dashboard",  label: "Dashboard",  icon: LayoutDashboard, badge: null },
  { path: "/chat",       label: "AI Agents",  icon: Bot,             badge: "Live" },
  { path: "/documents",  label: "Documents",  icon: FileText,        badge: null },
  { path: "/workflows",  label: "Workflows",  icon: Workflow,        badge: null },
  { path: "/reports",    label: "Reports",    icon: TrendingUp,      badge: null },
  { path: "/analytics",  label: "Analytics",  icon: BarChart3,       badge: null },
];

const BOTTOM_ITEMS = [
  { path: "/admin",   label: "Admin",    icon: Shield },
];

// ── Sidebar Component ──────────────────────────────────────────────────────────

function Sidebar({ collapsed }: { collapsed: boolean }) {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 256 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="flex flex-col h-full bg-card border-r border-border overflow-hidden flex-shrink-0"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 p-4 border-b border-border h-16 flex-shrink-0">
        <motion.div
          className="w-9 h-9 rounded-xl flex items-center justify-center text-lg flex-shrink-0 animate-glow-pulse"
          style={{ background: "linear-gradient(135deg, #3b82f6, #8b5cf6)" }}
        >
          🤖
        </motion.div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="font-bold text-sm leading-none gradient-text">FinPilot AI</div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Enterprise Platform</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const active = isActive(item.path);
          const Icon = item.icon;

          return (
            <motion.button
              key={item.path}
              onClick={() => navigate(item.path)}
              whileHover={{ x: 2 }}
              whileTap={{ scale: 0.97 }}
              className={`sidebar-item w-full ${active ? "active" : ""}`}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-4.5 h-4.5 flex-shrink-0" size={18} />
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex-1 text-sm text-left"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
              {!collapsed && item.badge && (
                <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded-full font-medium border border-primary/30">
                  {item.badge}
                </span>
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* Bottom Items */}
      <div className="p-2 border-t border-border space-y-1">
        {BOTTOM_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <motion.button
              key={item.path}
              onClick={() => navigate(item.path)}
              whileHover={{ x: 2 }}
              className={`sidebar-item w-full ${active ? "active" : ""}`}
              title={collapsed ? item.label : undefined}
            >
              <Icon size={18} />
              {!collapsed && <span className="text-sm">{item.label}</span>}
            </motion.button>
          );
        })}

        {/* Collapse Toggle */}
        <motion.button
          onClick={() => dispatch(setSidebarCollapsed(!collapsed))}
          whileHover={{ x: 2 }}
          className="sidebar-item w-full"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <motion.div
            animate={{ rotate: collapsed ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            <ChevronLeft size={18} />
          </motion.div>
          {!collapsed && <span className="text-sm">Collapse</span>}
        </motion.button>
      </div>
    </motion.aside>
  );
}

// ── Top Bar Component ──────────────────────────────────────────────────────────

function TopBar() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useSelector((s: RootState) => s.auth);
  const { theme, notifications } = useSelector((s: RootState) => s.ui);
  const unreadCount = notifications.filter((n) => !n.read).length;

  const pageTitles: Record<string, string> = {
    "/dashboard": "Dashboard",
    "/chat": "AI Agents",
    "/documents": "Document Intelligence",
    "/workflows": "Workflow Builder",
    "/reports": "Reports",
    "/analytics": "Analytics",
    "/admin": "Administration",
  };

  const currentTitle = Object.entries(pageTitles).find(([path]) =>
    location.pathname.startsWith(path)
  )?.[1] || "FinPilot AI";

  return (
    <header className="h-16 border-b border-border flex items-center justify-between px-6 bg-card flex-shrink-0">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold text-foreground">{currentTitle}</h1>
        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full border border-primary/20">
          v1.0
        </span>
      </div>

      <div className="flex items-center gap-2">
        {/* Search / Command Palette */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => dispatch(setCommandPaletteOpen(true))}
          className="flex items-center gap-2 px-3 py-1.5 bg-secondary rounded-lg text-muted-foreground text-sm hover:text-foreground transition-colors border border-border"
        >
          <Search size={14} />
          <span>Search...</span>
          <kbd className="text-[10px] bg-background px-1.5 py-0.5 rounded border border-border ml-2">⌘K</kbd>
        </motion.button>

        {/* Theme Toggle */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => dispatch(toggleTheme())}
          className="w-9 h-9 flex items-center justify-center rounded-lg bg-secondary border border-border text-muted-foreground hover:text-foreground transition-colors"
        >
          <AnimatePresence mode="wait">
            {theme === "dark" ? (
              <motion.div key="sun" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }}>
                <Sun size={16} />
              </motion.div>
            ) : (
              <motion.div key="moon" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }}>
                <Moon size={16} />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>

        {/* Notifications */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="relative w-9 h-9 flex items-center justify-center rounded-lg bg-secondary border border-border text-muted-foreground hover:text-foreground transition-colors"
        >
          <Bell size={16} />
          {unreadCount > 0 && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold"
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </motion.span>
          )}
        </motion.button>

        {/* User Avatar */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-lg hover:bg-secondary transition-colors"
          onClick={() => dispatch(logout())}
          title="Logout"
        >
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-white text-xs font-bold">
            {user?.full_name?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="text-left hidden md:block">
            <div className="text-xs font-medium text-foreground leading-none">
              {user?.full_name?.split(" ")[0] || "User"}
            </div>
            <div className="text-[10px] text-muted-foreground mt-0.5 capitalize">{user?.role}</div>
          </div>
          <LogOut size={12} className="text-muted-foreground ml-1" />
        </motion.button>
      </div>
    </header>
  );
}

// ── App Shell ──────────────────────────────────────────────────────────────────

export default function AppShell() {
  const dispatch = useDispatch();
  const { sidebarCollapsed, commandPaletteOpen } = useSelector((s: RootState) => s.ui);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K — Command Palette
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        dispatch(setCommandPaletteOpen(true));
      }
      // Escape — Close command palette
      if (e.key === "Escape" && commandPaletteOpen) {
        dispatch(setCommandPaletteOpen(false));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [dispatch, commandPaletteOpen]);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar collapsed={sidebarCollapsed} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={window.location.pathname}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Command Palette Modal */}
      <AnimatePresence>
        {commandPaletteOpen && <CommandPalette />}
      </AnimatePresence>
    </div>
  );
}
