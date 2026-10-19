import * as React from "react";
import authApi from "@/api/authApi";
import { tokenStorage } from "@/api/axiosClient";

export const AuthContext = React.createContext(null);

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return context;
}

/**
 * Top-level auth provider. On mount, checks for an existing access
 * token and — if present — verifies it against the backend via
 * authApi.getCurrentUser() to hydrate `user` state. This is what
 * ProtectedRoute/PublicRoute check via `isLoading`/`isAuthenticated`
 * before deciding whether to redirect.
 *
 * Wrap the whole app with this, above <AppRouter />:
 *   <AuthProvider>
 *     <AppRouter />
 *   </AuthProvider>
 */
export function AuthProvider({ children }) {
  const [user, setUser] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;

    async function bootstrapAuth() {
      const token = tokenStorage.getAccessToken();

      // 1. If we have a local access token, try validating it with /auth/me
      if (token) {
        try {
          const currentUser = await authApi.getCurrentUser();
          if (!cancelled) {
            setUser(currentUser);
            setIsLoading(false);
            return;
          }
        } catch {
          // Token expired or invalid, proceed to refresh attempt
          tokenStorage.clearAccessToken();
        }
      }

      // 2. Try silent refresh using the httpOnly cookie
      try {
        const refreshData = await authApi.refreshToken();
        const currentUser = refreshData?.user || (await authApi.getCurrentUser());
        if (!cancelled) setUser(currentUser);
      } catch {
        // No active session
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    bootstrapAuth();
    return () => {
      cancelled = true;
    };
  }, []);

  const logout = React.useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const value = React.useMemo(
    () => ({
      user,
      setUser,
      isAuthenticated: Boolean(user),
      isLoading,
      logout,
    }),
    [user, isLoading, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}