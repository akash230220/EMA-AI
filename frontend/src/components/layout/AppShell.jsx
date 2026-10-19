import * as React from "react";
import { Outlet } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import MobileNav from "./MobileNav";
import emailApi from "@/api/emailApi";

const SIDEBAR_COLLAPSED_KEY = "ai_email_os_sidebar_collapsed";

/**
 * Top-level authenticated layout: Sidebar (desktop) + MobileNav (mobile
 * drawer) + Topbar + routed page content via <Outlet />.
 *
 * Wrap all protected routes with this shell in AppRouter.jsx, e.g.:
 *   <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
 *     <Route path="/dashboard" element={<DashboardPage />} />
 *     ...
 *   </Route>
 */
export default function AppShell() {
  const [collapsed, setCollapsed] = React.useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
  });
  const [mobileNavOpen, setMobileNavOpen] = React.useState(false);
  const queryClient = useQueryClient();

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(next));
      return next;
    });
  };

  const syncMutation = useMutation({
    mutationFn: () => emailApi.syncInbox(),
    onSuccess: () => {
      // Refresh anything derived from inbox state after a sync completes
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
    },
  });

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <Sidebar collapsed={collapsed} onToggleCollapsed={toggleCollapsed} />
      <MobileNav open={mobileNavOpen} onOpenChange={setMobileNavOpen} />

      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar
          onOpenMobileNav={() => setMobileNavOpen(true)}
          isSyncing={syncMutation.isPending}
          onSyncInbox={() => syncMutation.mutate()}
        />

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[1600px] p-4 md:p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}