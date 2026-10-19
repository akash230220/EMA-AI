import { useContext } from "react";
import { AuthContext } from "@/context/AuthContext";

/**
 * Convenience re-export of the auth context. Kept as a separate
 * hooks/useAuth.js file (rather than requiring every component to
 * import from context/AuthContext directly) so the import path
 * stays consistent with the rest of the hooks/ folder, and so the
 * underlying context implementation can change without touching
 * every consumer.
 *
 * @returns {{
 *   user: object|null,
 *   setUser: (user: object|((prev: object|null) => object)) => void,
 *   isAuthenticated: boolean,
 *   isLoading: boolean,
 *   logout: () => Promise<void>
 * }}
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return context;
}