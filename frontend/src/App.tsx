/**
 * FinPilot AI — Main Application Router + Theme
 * ===============================================
 * Handles routing, authentication guards, and theme initialization.
 */

import React, { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { motion, AnimatePresence } from "framer-motion";

import { RootState } from "./app/store";
import { setTheme } from "./app/slices/uiSlice";

// ── Lazy-loaded pages for code splitting ──────────────────────────────────────

const AuthPage     = React.lazy(() => import("./features/auth/AuthPage"));
const AppShell     = React.lazy(() => import("./components/layout/AppShell"));
const DashboardPage = React.lazy(() => import("./features/dashboard/DashboardPage"));
const ChatPage     = React.lazy(() => import("./features/chat/ChatPage"));
const DocumentsPage = React.lazy(() => import("./features/documents/DocumentsPage"));
const WorkflowPage = React.lazy(() => import("./features/workflows/WorkflowPage"));
const ReportsPage  = React.lazy(() => import("./features/reports/ReportsPage"));
const AnalyticsPage = React.lazy(() => import("./features/analytics/AnalyticsPage"));
const AdminPage    = React.lazy(() => import("./features/admin/AdminPage"));

// ── Route Guards ───────────────────────────────────────────────────────────────

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useSelector((s: RootState) => s.auth.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  return <>{children}</>;
}

function RequireGuest({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useSelector((s: RootState) => s.auth.isAuthenticated);
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}

// ── Loading Fallback ───────────────────────────────────────────────────────────

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center animate-pulse text-2xl">
          🤖
        </div>
        <div className="w-48 h-1 bg-secondary rounded-full overflow-hidden">
          <div className="h-full w-full bg-gradient-to-r from-blue-500 to-violet-600 animate-shimmer" />
        </div>
      </div>
    </div>
  );
}

// ── App Component ──────────────────────────────────────────────────────────────

export default function App() {
  const dispatch = useDispatch();
  const theme = useSelector((s: RootState) => s.ui.theme);

  // Apply theme on mount and when it changes
  useEffect(() => {
    document.documentElement.className = theme;
  }, [theme]);

  // Initialize theme from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("finpilot_theme") as "dark" | "light";
    if (saved) {
      dispatch(setTheme(saved));
    }
  }, [dispatch]);

  return (
    <React.Suspense fallback={<PageLoader />}>
      <AnimatePresence mode="wait">
        <Routes>
          {/* ── Auth ───────────────────────────────────────────────────────── */}
          <Route
            path="/auth"
            element={
              <RequireGuest>
                <AuthPage />
              </RequireGuest>
            }
          />

          {/* ── Protected App ───────────────────────────────────────────────── */}
          <Route
            path="/"
            element={
              <RequireAuth>
                <AppShell />
              </RequireAuth>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard"   element={<DashboardPage />} />
            <Route path="chat"        element={<ChatPage />} />
            <Route path="chat/:id"    element={<ChatPage />} />
            <Route path="documents"   element={<DocumentsPage />} />
            <Route path="workflows"   element={<WorkflowPage />} />
            <Route path="workflows/:id" element={<WorkflowPage />} />
            <Route path="reports"     element={<ReportsPage />} />
            <Route path="analytics"   element={<AnalyticsPage />} />
            <Route path="admin"       element={<AdminPage />} />
          </Route>

          {/* ── Catch-all ───────────────────────────────────────────────────── */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AnimatePresence>
    </React.Suspense>
  );
}
