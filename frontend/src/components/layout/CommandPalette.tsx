/**
 * FinPilot AI — Command Palette (Cmd+K)
 * ==========================================
 * Global search and action launcher using cmdk
 */

import React, { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import {
  Search, LayoutDashboard, MessageSquare, FileText,
  Workflow, BarChart3, Shield, Bot, Zap, TrendingUp,
  X, ArrowRight,
} from "lucide-react";
import { setCommandPaletteOpen } from "@/app/slices/uiSlice";

const COMMANDS = [
  { id: "dashboard", label: "Go to Dashboard", icon: LayoutDashboard, path: "/dashboard", category: "Navigation" },
  { id: "chat",      label: "New AI Conversation", icon: Bot, path: "/chat", category: "Navigation" },
  { id: "docs",      label: "Upload Document", icon: FileText, path: "/documents", category: "Navigation" },
  { id: "workflows", label: "Workflow Builder", icon: Workflow, path: "/workflows", category: "Navigation" },
  { id: "reports",   label: "View Reports", icon: TrendingUp, path: "/reports", category: "Navigation" },
  { id: "analytics", label: "Analytics Dashboard", icon: BarChart3, path: "/analytics", category: "Navigation" },
  { id: "admin",     label: "Admin Panel", icon: Shield, path: "/admin", category: "Navigation" },
  { id: "detect-fraud", label: "Run Fraud Detection", icon: Zap, path: "/chat?q=Run fraud detection analysis", category: "AI Actions" },
  { id: "risk",        label: "Generate Risk Report", icon: Zap, path: "/chat?q=Generate a risk assessment report", category: "AI Actions" },
  { id: "compliance",  label: "Check Compliance", icon: Zap, path: "/chat?q=Check regulatory compliance status", category: "AI Actions" },
];

export default function CommandPalette() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const filtered = COMMANDS.filter(
    (c) =>
      c.label.toLowerCase().includes(query.toLowerCase()) ||
      c.category.toLowerCase().includes(query.toLowerCase())
  );

  const grouped = filtered.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {} as Record<string, typeof COMMANDS>);

  const handleSelect = (cmd: (typeof COMMANDS)[0]) => {
    dispatch(setCommandPaletteOpen(false));
    navigate(cmd.path);
  };

  const handleClose = () => {
    dispatch(setCommandPaletteOpen(false));
  };

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        onClick={handleClose}
      />

      {/* Palette */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: -20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: -20 }}
        transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}
        className="fixed top-1/4 left-1/2 -translate-x-1/2 w-full max-w-xl glass rounded-2xl overflow-hidden z-50 shadow-2xl"
      >
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Search size={16} className="text-muted-foreground flex-shrink-0" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search commands, pages, actions..."
            className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
          />
          <button onClick={handleClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X size={14} />
          </button>
          <kbd className="text-[10px] text-muted-foreground bg-secondary px-1.5 py-0.5 rounded border border-border">ESC</kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto p-2">
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category} className="mb-2">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground px-3 py-1 font-semibold">
                {category}
              </div>
              {items.map((cmd) => {
                const Icon = cmd.icon;
                return (
                  <motion.button
                    key={cmd.id}
                    whileHover={{ backgroundColor: "rgba(59, 130, 246, 0.08)" }}
                    onClick={() => handleSelect(cmd)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors group"
                  >
                    <div className="w-7 h-7 rounded-lg bg-secondary flex items-center justify-center flex-shrink-0">
                      <Icon size={14} className="text-muted-foreground" />
                    </div>
                    <span className="flex-1 text-sm text-foreground">{cmd.label}</span>
                    <ArrowRight size={12} className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                  </motion.button>
                );
              })}
            </div>
          ))}

          {filtered.length === 0 && (
            <div className="text-center py-8 text-muted-foreground text-sm">
              No commands found for "{query}"
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border px-4 py-2 flex items-center gap-4 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <kbd className="bg-secondary px-1 rounded border border-border">↑↓</kbd> Navigate
          </span>
          <span className="flex items-center gap-1">
            <kbd className="bg-secondary px-1 rounded border border-border">↵</kbd> Select
          </span>
          <span className="flex items-center gap-1">
            <kbd className="bg-secondary px-1 rounded border border-border">ESC</kbd> Close
          </span>
        </div>
      </motion.div>
    </>
  );
}
