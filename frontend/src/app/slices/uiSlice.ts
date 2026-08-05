/**
 * FinPilot AI — UI Redux Slice
 * Controls sidebar, theme, modals, notifications
 */

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface Notification {
  id: string;
  title: string;
  message: string;
  type: "success" | "error" | "warning" | "info";
  timestamp: string;
  read: boolean;
}

interface UIState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  theme: "dark" | "light";
  commandPaletteOpen: boolean;
  notifications: Notification[];
  activeAgents: string[];
  globalLoading: boolean;
  loadingMessage: string;
}

const initialState: UIState = {
  sidebarOpen: true,
  sidebarCollapsed: false,
  theme: (localStorage.getItem("finpilot_theme") as "dark" | "light") || "dark",
  commandPaletteOpen: false,
  notifications: [],
  activeAgents: [],
  globalLoading: false,
  loadingMessage: "",
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarCollapsed(state, action: PayloadAction<boolean>) {
      state.sidebarCollapsed = action.payload;
    },
    toggleTheme(state) {
      state.theme = state.theme === "dark" ? "light" : "dark";
      localStorage.setItem("finpilot_theme", state.theme);
      document.documentElement.className = state.theme;
    },
    setTheme(state, action: PayloadAction<"dark" | "light">) {
      state.theme = action.payload;
      localStorage.setItem("finpilot_theme", action.payload);
      document.documentElement.className = action.payload;
    },
    toggleCommandPalette(state) {
      state.commandPaletteOpen = !state.commandPaletteOpen;
    },
    setCommandPaletteOpen(state, action: PayloadAction<boolean>) {
      state.commandPaletteOpen = action.payload;
    },
    addNotification(state, action: PayloadAction<Omit<Notification, "id" | "timestamp" | "read">>) {
      state.notifications.unshift({
        ...action.payload,
        id: Math.random().toString(36).slice(2),
        timestamp: new Date().toISOString(),
        read: false,
      });
      // Keep only last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50);
      }
    },
    markNotificationRead(state, action: PayloadAction<string>) {
      const notif = state.notifications.find((n) => n.id === action.payload);
      if (notif) notif.read = true;
    },
    markAllNotificationsRead(state) {
      state.notifications.forEach((n) => { n.read = true; });
    },
    clearNotifications(state) {
      state.notifications = [];
    },
    setActiveAgents(state, action: PayloadAction<string[]>) {
      state.activeAgents = action.payload;
    },
    setGlobalLoading(state, action: PayloadAction<{ loading: boolean; message?: string }>) {
      state.globalLoading = action.payload.loading;
      state.loadingMessage = action.payload.message || "";
    },
  },
});

export const {
  toggleSidebar,
  setSidebarCollapsed,
  toggleTheme,
  setTheme,
  toggleCommandPalette,
  setCommandPaletteOpen,
  addNotification,
  markNotificationRead,
  markAllNotificationsRead,
  clearNotifications,
  setActiveAgents,
  setGlobalLoading,
} = uiSlice.actions;

export default uiSlice.reducer;
