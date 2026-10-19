// src/App.jsx
import * as React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import { ToastProvider } from "@/components/shared/ToastProvider";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "@/components/shared/ErrorBoundary";

import AppRouter from "@/router/AppRouter";

/**
 * Single shared QueryClient instance for the whole app. Configured
 * with sane defaults for an inbox-style app:
 *  - retry: 1 (don't hammer a failing endpoint 3x by default)
 *  - refetchOnWindowFocus: false (avoids surprise re-fetches firing
 *    every time the user tabs back into the app mid-task — e.g.
 *    losing an in-progress ReplyComposer draft's "generating" state)
 *  - staleTime: 30s (short-lived cache; email/task/meeting data
 *    changes often enough that we don't want it stale for long, but
 *    don't want every render re-fetching either)
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
    mutations: {
      retry: 0,
    },
  },
});

/**
 * Root application component. Provider order (outside-in) matters:
 *
 *  1. QueryClientProvider — outermost; ToastProvider's mutations
 *     and every hook in hooks/ need React Query context available.
 *  2. ThemeProvider — applies the `dark` class to <html> before
 *     anything visual renders, avoiding a light-mode flash for
 *     users with a persisted dark preference.
 *  3. AuthProvider — bootstraps auth state (checks for an existing
 *     token, calls /auth/me) before ProtectedRoute/PublicRoute in
 *     AppRouter make their redirect decisions.
 *  4. ToastProvider — must be inside AuthProvider/QueryClientProvider
 *     since mutation hooks call useToast() on success/error.
 *  5. TooltipProvider — Radix tooltip context, needed by Sidebar's
 *     collapsed-state icon tooltips and any other <Tooltip> usage.
 *  6. ErrorBoundary — wraps the router as a last-resort catch-all,
 *     separate from the per-route boundaries already inside
 *     AppRouter.jsx (see router/AppRouter.jsx's withBoundary()).
 */
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <TooltipProvider>
              <ErrorBoundary>
                <AppRouter />
              </ErrorBoundary>
            </TooltipProvider>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>

      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} position="bottom-right" />}
    </QueryClientProvider>
  );
}