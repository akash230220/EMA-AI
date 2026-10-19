import * as React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import ProtectedRoute from "./ProtectedRoute";
import PublicRoute from "./PublicRoute";
import AppShell from "@/components/layout/AppShell";
import ErrorBoundary from "@/components/shared/ErrorBoundary";

import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import InboxPage from "@/pages/InboxPage";
import EmailDetailPage from "@/pages/EmailDetailPage";
import AIReplyCenterPage from "@/pages/AIReplyCenterPage";
import CopilotChatPage from "@/pages/CopilotChatPage";
import TasksPage from "@/pages/TasksPage";
import MeetingsPage from "@/pages/MeetingsPage";
import AnalyticsPage from "@/pages/AnalyticsPage";
import AutomationRulesPage from "@/pages/AutomationRulesPage";
import SettingsPage from "@/pages/SettingsPage";

/**
 * Wraps a page element in its own ErrorBoundary so a crash in one
 * page shows a contained fallback (with a "Try again" / "Go to
 * Dashboard" action) rather than taking down the whole app shell.
 * Each route gets a fresh boundary keyed by path so navigating away
 * and back resets any previous error state.
 */
function withBoundary(path, element) {
  return <ErrorBoundary key={path}>{element}</ErrorBoundary>;
}

/**
 * Top-level application router. Two route groups:
 *  - Public: /login (redirects to /dashboard if already authenticated)
 *  - Protected: everything else, wrapped in AppShell (Sidebar + Topbar)
 *
 * Unmatched paths redirect to /dashboard (which itself redirects to
 * /login if unauthenticated via ProtectedRoute).
 */
export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              {withBoundary("/login", <LoginPage />)}
            </PublicRoute>
          }
        />

        {/* Protected — shared AppShell layout (Sidebar + Topbar + Outlet) */}
        <Route
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={withBoundary("/dashboard", <DashboardPage />)} />

          <Route path="/inbox" element={withBoundary("/inbox", <InboxPage />)} />
          <Route path="/inbox/:emailId" element={withBoundary("/inbox/:emailId", <EmailDetailPage />)} />

          <Route path="/reply-center" element={withBoundary("/reply-center", <AIReplyCenterPage />)} />

          <Route path="/copilot" element={withBoundary("/copilot", <CopilotChatPage />)} />

          <Route path="/tasks" element={withBoundary("/tasks", <TasksPage />)} />

          <Route path="/meetings" element={withBoundary("/meetings", <MeetingsPage />)} />
          <Route path="/meetings/:meetingId" element={withBoundary("/meetings/:meetingId", <MeetingsPage />)} />

          <Route path="/analytics" element={withBoundary("/analytics", <AnalyticsPage />)} />

          <Route path="/automation" element={withBoundary("/automation", <AutomationRulesPage />)} />

          <Route path="/settings" element={withBoundary("/settings", <SettingsPage />)} />

          {/* Default protected route */}
          <Route index element={<Navigate to="/dashboard" replace />} />
        </Route>

        {/* Catch-all: redirect anything unmatched to /dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}