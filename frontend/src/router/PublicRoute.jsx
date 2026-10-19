import * as React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import Loader from "@/components/shared/Loader";

/**
 * Inverse guard for public-only pages (currently just Login).
 * If the user is already authenticated, redirect them straight to
 * the Dashboard instead of showing the login screen again — avoids
 * a confusing "log in" prompt for someone who's already signed in.
 *
 * Skips the redirect while `code`/`error` OAuth callback params are
 * present so LoginPage can still process the Google redirect even
 * if auth state hasn't updated yet.
 */
export default function PublicRoute({ children }) {
  const { isLoading, isAuthenticated } = useAuth();
  const hasOAuthCallbackParams =
    typeof window !== "undefined" &&
    (window.location.search.includes("code=") || window.location.search.includes("error="));

  if (isLoading) {
    return <Loader fullScreen label="Loading..." />;
  }

  if (isAuthenticated && !hasOAuthCallbackParams) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}