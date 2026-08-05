/**
 * FinPilot AI — API Client
 * ==========================
 * Axios instance with:
 * - JWT auth interceptor
 * - Token refresh on 401
 * - Error normalization
 * - Response caching helpers
 */

import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import { store } from "../app/store";
import { logout, setUser } from "../app/slices/authSlice";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ── Create Axios Instance ──────────────────────────────────────────────────────

export const api: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request Interceptor: Attach JWT ────────────────────────────────────────────

api.interceptors.request.use((config) => {
  const token = store.getState().auth.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response Interceptor: Handle 401 ──────────────────────────────────────────

let isRefreshing = false;
let refreshQueue: Array<(token: string) => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;

      if (isRefreshing) {
        // Queue the request until refresh completes
        return new Promise((resolve) => {
          refreshQueue.push((token: string) => {
            original.headers.Authorization = `Bearer ${token}`;
            resolve(api(original));
          });
        });
      }

      isRefreshing = true;
      const refreshToken = store.getState().auth.refreshToken;

      try {
        const response = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token, user } = response.data;
        store.dispatch(setUser({ user, accessToken: access_token, refreshToken: refresh_token }));

        // Process queued requests
        refreshQueue.forEach((cb) => cb(access_token));
        refreshQueue = [];

        original.headers.Authorization = `Bearer ${access_token}`;
        return api(original);
      } catch {
        store.dispatch(logout());
        window.location.href = "/auth";
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ── API Methods ────────────────────────────────────────────────────────────────

export const authAPI = {
  register: (data: { email: string; password: string; full_name: string; organization?: string }) =>
    api.post("/auth/register", data),
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  me: () => api.get("/auth/me"),
  updateProfile: (data: any) => api.patch("/auth/me", data),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post("/auth/change-password", { current_password: currentPassword, new_password: newPassword }),
};

export const chatAPI = {
  createSession: (data: { title?: string; active_document_ids?: string[] }) =>
    api.post("/chat/sessions", data),
  listSessions: (page = 1) =>
    api.get(`/chat/sessions?page=${page}`),
  getSession: (id: string) =>
    api.get(`/chat/sessions/${id}`),
  deleteSession: (id: string) =>
    api.delete(`/chat/sessions/${id}`),
  sendMessage: (sessionId: string, content: string, documentIds?: string[]) =>
    fetch(`${BASE_URL}/api/v1/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${store.getState().auth.accessToken}`,
      },
      body: JSON.stringify({ content, active_document_ids: documentIds }),
    }),
};

export const documentsAPI = {
  upload: (file: File, onProgress?: (pct: number) => void) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) {
          onProgress(Math.round((evt.loaded * 100) / evt.total));
        }
      },
    });
  },
  list: (page = 1, statusFilter?: string) =>
    api.get(`/documents?page=${page}${statusFilter ? `&status_filter=${statusFilter}` : ""}`),
  get: (id: string) =>
    api.get(`/documents/${id}`),
  getStatus: (id: string) =>
    api.get(`/documents/${id}/status`),
  delete: (id: string) =>
    api.delete(`/documents/${id}`),
  search: (query: string, documentIds?: string[]) =>
    api.post("/documents/search", { query, document_ids: documentIds }),
};

export const dashboardAPI = {
  getKPIs: () => api.get("/dashboard/kpis"),
  getActivity: () => api.get("/dashboard/activity"),
  getAgentStatus: () => api.get("/dashboard/agent-status"),
};

export const analyticsAPI = {
  getTokenUsage: (days?: number) => api.get(`/analytics/token-usage?days=${days || 30}`),
  getAgentPerformance: () => api.get("/analytics/agent-performance"),
};

export const workflowsAPI = {
  create: (data: any) => api.post("/workflows", data),
  list: () => api.get("/workflows"),
  get: (id: string) => api.get(`/workflows/${id}`),
  update: (id: string, data: any) => api.patch(`/workflows/${id}`, data),
  delete: (id: string) => api.delete(`/workflows/${id}`),
};

export const reportsAPI = {
  list: () => api.get("/reports"),
  get: (id: string) => api.get(`/reports/${id}`),
};

export const adminAPI = {
  listUsers: (page = 1) => api.get(`/admin/users?page=${page}`),
  getAuditLogs: (page = 1) => api.get(`/admin/audit-logs?page=${page}`),
  getSystemStats: () => api.get("/admin/system-stats"),
};
