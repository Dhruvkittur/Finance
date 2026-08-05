/**
 * FinPilot AI — Auth Redux Slice
 */

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization?: string;
  department?: string;
  avatar_url?: string;
  theme: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const initialState: AuthState = {
  user: (() => {
    try {
      const stored = localStorage.getItem("finpilot_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  })(),
  accessToken: localStorage.getItem("finpilot_access_token"),
  refreshToken: localStorage.getItem("finpilot_refresh_token"),
  isAuthenticated: !!localStorage.getItem("finpilot_access_token"),
  isLoading: false,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setUser(state, action: PayloadAction<{ user: User; accessToken: string; refreshToken: string }>) {
      state.user = action.payload.user;
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
      state.isAuthenticated = true;
      state.isLoading = false;
      localStorage.setItem("finpilot_user", JSON.stringify(action.payload.user));
      localStorage.setItem("finpilot_access_token", action.payload.accessToken);
      localStorage.setItem("finpilot_refresh_token", action.payload.refreshToken);
    },
    updateUser(state, action: PayloadAction<Partial<User>>) {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
        localStorage.setItem("finpilot_user", JSON.stringify(state.user));
      }
    },
    logout(state) {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      localStorage.removeItem("finpilot_user");
      localStorage.removeItem("finpilot_access_token");
      localStorage.removeItem("finpilot_refresh_token");
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload;
    },
  },
});

export const { setUser, updateUser, logout, setLoading } = authSlice.actions;
export default authSlice.reducer;
