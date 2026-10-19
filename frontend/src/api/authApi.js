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
   * The backend builds the Google consent URL (with client_id, scopes
   * for Gmail + Calendar, redirect_uri) and redirects to Google.
   */
  loginWithGoogle: () => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
    window.location.href = `${BASE_URL}/auth/google/login`;
  },

  /**
   * Called on the OAuth callback page after Google redirects back with
   * a `code` query param. Exchanges the code (via backend) for tokens.
   * Backend sets an httpOnly refresh-token cookie and returns an access token.
   *
   * @param {string} code - Authorization code from Google's redirect
   * @returns {Promise<{access_token: string, user: object}>}
   */
  exchangeCodeForToken: async (code) => {
    const { data } = await axiosClient.post("/auth/google/callback", { code });
    const accessToken = data?.access_token || data?.accessToken;
    if (accessToken) {
      tokenStorage.setAccessToken(accessToken);
    }
    return data;
  },

  /**
   * Fetches the currently authenticated user's profile.
   * Used on app load to determine auth state.
   *
   * @returns {Promise<object>} user profile
   */
  getCurrentUser: async () => {
    const { data } = await axiosClient.get("/auth/me");
    return data;
  },

  /**
   * Manually triggers a token refresh using the httpOnly cookie.
   * Normally handled transparently by the axiosClient response
   * interceptor on a 401 — exposed here for explicit use
   * (e.g. app bootstrap on first load).
   *
   * @returns {Promise<{access_token: string}>}
   */
  refreshToken: async () => {
    const { data } = await axiosClient.post("/auth/refresh");
    const accessToken = data?.access_token || data?.accessToken;
    if (accessToken) {
      tokenStorage.setAccessToken(accessToken);
    }
    return data;
  },

  /**
   * Logs the user out: clears the httpOnly refresh cookie server-side
   * and removes the local access token.
   *
   * @returns {Promise<void>}
   */
  logout: async () => {
    try {
      await axiosClient.post("/auth/logout");
    } finally {
      tokenStorage.clearAccessToken();
    }
  },

  /**
   * Developer / Demo mode quick login bypass for local testing.
   * @returns {Promise<{access_token: string, user: object}>}
   */
  devLogin: async () => {
    const { data } = await axiosClient.post("/auth/dev-login");
    const accessToken = data?.access_token || data?.accessToken;
    if (accessToken) {
      tokenStorage.setAccessToken(accessToken);
    }
    return data;
  },

  /**
   * Checks whether an access token currently exists in local storage.
   * A lightweight synchronous check for route guards — does NOT
   * validate the token against the backend.
   *
   * @returns {boolean}
   */
  hasLocalToken: () => Boolean(tokenStorage.getAccessToken()),
};

export default authApi;
