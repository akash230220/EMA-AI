// src/api/axiosClient.js
import axios from "axios";

/**
 * Centralized Axios instance for the AI Email OS frontend.
 *
 * Responsibilities:
 *  - Attaches JWT access token to every outgoing request
 *  - Handles 401 responses by attempting a silent token refresh
 *  - Queues concurrent requests while a refresh is in-flight
 *  - Normalizes error responses into a consistent shape
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const axiosClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  withCredentials: true, // allows secure httpOnly refresh-token cookie to be sent
  headers: {
    "Content-Type": "application/json",
  },
});

// ---------------------------------------------------------------------------
// Token storage helpers
// ---------------------------------------------------------------------------
const ACCESS_TOKEN_KEY = "ai_email_os_access_token";

export const tokenStorage = {
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  setAccessToken: (token) => localStorage.setItem(ACCESS_TOKEN_KEY, token),
  clearAccessToken: () => localStorage.removeItem(ACCESS_TOKEN_KEY),
};

// ---------------------------------------------------------------------------
// Request interceptor — attach Authorization header
// ---------------------------------------------------------------------------
axiosClient.interceptors.request.use(
  (config) => {
    const token = tokenStorage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ---------------------------------------------------------------------------
// Response interceptor — normalize errors + silent refresh on 401
// ---------------------------------------------------------------------------
let isRefreshing = false;
let refreshSubscribers = [];

function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback);
}

function onRefreshed(newToken) {
  refreshSubscribers.forEach((callback) => callback(newToken));
  refreshSubscribers = [];
}

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Network / no response at all
    if (!error.response) {
      return Promise.reject({
        message: "Network error. Please check your connection.",
        status: null,
        original: error,
      });
    }

    const { status } = error.response;

    // Attempt silent refresh exactly once per request on 401 (excluding refresh endpoint itself)
    const isRefreshRequest = originalRequest.url?.includes("/auth/refresh");
    if (status === 401 && !isRefreshRequest && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue this request until the in-flight refresh completes
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((newToken) => {
            if (!newToken) {
              reject(error);
              return;
            }
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(axiosClient(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(
          `${BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const newAccessToken = data?.access_token || data?.accessToken;

        if (!newAccessToken) {
          throw new Error("No access token returned from refresh endpoint");
        }

        tokenStorage.setAccessToken(newAccessToken);
        isRefreshing = false;
        onRefreshed(newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return axiosClient(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        onRefreshed(null);
        const requestToken = originalRequest.headers?.Authorization?.replace(/^Bearer\s+/i, "");
        if (requestToken && tokenStorage.getAccessToken() === requestToken) {
          tokenStorage.clearAccessToken();
        }

        // Redirect to login only if not already on the login page
        if (typeof window !== "undefined" && window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject({
          message: "Session expired. Please log in again.",
          status: 401,
          original: refreshError,
        });
      }
    }

    // Normalize all other error responses
    const normalizedError = {
      message:
        error.response?.data?.detail ||
        error.response?.data?.message ||
        "Something went wrong. Please try again.",
      status,
      errors: error.response?.data?.errors || null,
      original: error,
    };

    return Promise.reject(normalizedError);
  }
);

export default axiosClient;