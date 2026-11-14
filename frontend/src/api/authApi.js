// src/api/authApi.js
import axiosClient, { tokenStorage } from "./axiosClient";

/**
 * Auth API layer.
 *
 * Handles Google OAuth 2.0 login flow, session bootstrapping,
 * token refresh, and logout. Pairs with backend endpoints under
 * /api/v1/auth (see backend/app/api/v1/endpoints/auth.py).
 */

const authApi = {
  /**
   * Redirects the browser to the backend's Google OAuth entrypoint.
   */
  loginWithGoogle: () => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
    window.location.href = `${BASE_URL}/auth/google/login`;
  },

  /**
   * Exchanges the authorization code and browser-bound OAuth state
   * for an application session.
   */
  exchangeCodeForToken: async (code, state) => {
    const { data } = await axiosClient.post("/auth/google/callback", { code, state });
    const accessToken = data?.access_token || data?.accessToken;
    if (accessToken) {
      tokenStorage.setAccessToken(accessToken);
    }
    return data;
  },

  getCurrentUser: async () => {
    const { data } = await axiosClient.get("/auth/me");
    return data;
  },

  refreshToken: async () => {
    const { data } = await axiosClient.post("/auth/refresh");
    const accessToken = data?.access_token || data?.accessToken;
    if (accessToken) {
      tokenStorage.setAccessToken(accessToken);
    }
    return data;
  },

  logout: async () => {
    try {
      await axiosClient.post("/auth/logout");
    } finally {
      tokenStorage.clearAccessToken();
    }
  },

  devLogin: async () => {
    const { data } = await axiosClient.post("/auth/dev-login");
    const accessToken = data?.access_token || data?.accessToken;
    if (accessToken) {
      tokenStorage.setAccessToken(accessToken);
    }
    return data;
  },

  hasLocalToken: () => Boolean(tokenStorage.getAccessToken()),
};

export default authApi;
