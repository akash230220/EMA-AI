import * as React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import Loader from "@/components/shared/Loader";

/**
 * Route guard for authenticated pages. Redirects to /login if the
 * user isn't authenticated, preserving the attempted destination
 * (via location state) so login can redirect back afterward.
 *
 * While the auth check is still resolving (initial app load,
 * verifying a token against the backend), shows a full-screen
 * loader rather than flashing the login page.
 *
 * Usage:
 *   <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
 *     <Route path="/dashboard" element={<DashboardPage />} />
 *   </Route>
 */
export default function ProtectedRoute({ children }) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <Loader fullScreen label="Loading your workspace..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}