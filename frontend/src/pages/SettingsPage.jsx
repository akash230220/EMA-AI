import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import PageHeader from "@/components/shared/PageHeader";
import SettingsNav from "@/components/settings/SettingsNav";
import ProfileForm from "@/components/settings/ProfileForm";
import IntegrationsPanel from "@/components/settings/IntegrationsPanel";
import NotificationSettings from "@/components/settings/NotificationSettings";
import AiPreferences from "@/components/settings/AiPreferences";
import SecuritySettings from "@/components/settings/SecuritySettings";
import DangerZone from "@/components/settings/DangerZone";
import axiosClient from "@/api/axiosClient";
import authApi from "@/api/authApi";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/shared/ToastProvider";
import { useNavigate } from "react-router-dom";

/**
 * Settings — account profile, integrations, notifications, AI
 * behavior preferences, security, and destructive account actions.
 *
 * NOTE: assumes a backend "/settings" endpoint group for
 * preferences/integration-status/sessions not defined in the
 * earlier api/ folder — add a settingsApi.js file (or fold these
 * into authApi.js) to match your backend's actual routes.
 */
export default function SettingsPage() {
  const { user, setUser, logout } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const [activeSection, setActiveSection] = React.useState("profile");

  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: async () => (await axiosClient.get("/settings")).data,
  });

  const updateProfileMutation = useMutation({
    mutationFn: (updates) => axiosClient.patch("/settings/profile", updates).then((r) => r.data),
    onSuccess: (data) => {
      setUser((prev) => ({ ...prev, ...data }));
      toast({ type: "success", message: "Profile updated." });
    },
  });

  const updateNotificationsMutation = useMutation({
    mutationFn: (preferences) => axiosClient.patch("/settings/notifications", preferences).then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["settings"] }),
  });

  const updateAiPreferencesMutation = useMutation({
    mutationFn: (updates) => axiosClient.patch("/settings/ai-preferences", updates).then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["settings"] }),
  });

  const disconnectMutation = useMutation({
    mutationFn: () => axiosClient.post("/settings/integrations/disconnect"),
    onSuccess: () => {
      toast({ type: "success", message: "Google account disconnected." });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });

  const revokeSessionMutation = useMutation({
    mutationFn: (sessionId) => axiosClient.delete(`/settings/sessions/${sessionId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["settings"] }),
  });

  const signOutAllMutation = useMutation({
    mutationFn: () => axiosClient.post("/settings/sessions/revoke-all"),
    onSuccess: async () => {
      await logout();
      navigate("/login");
    },
  });

  const clearAiDataMutation = useMutation({
    mutationFn: () => axiosClient.post("/settings/clear-ai-data"),
    onSuccess: () => toast({ type: "success", message: "AI data cleared. Re-processing on next sync." }),
  });

  const deleteAccountMutation = useMutation({
    mutationFn: () => axiosClient.delete("/settings/account"),
    onSuccess: async () => {
      await logout();
      navigate("/login");
    },
  });

  const settings = settingsQuery.data || {};

  return (
    <div className="space-y-4">
      <PageHeader title="Settings" description="Manage your account, integrations, and AI preferences." />

      <div className="flex flex-col gap-6 md:flex-row">
        <SettingsNav activeSection={activeSection} onSectionChange={setActiveSection} />

        <div className="flex-1 space-y-4">
          {activeSection === "profile" && (
            <ProfileForm
              user={user}
              onSave={(updates) => updateProfileMutation.mutate(updates)}
              isSaving={updateProfileMutation.isPending}
            />
          )}

          {activeSection === "integrations" && (
            <IntegrationsPanel
              gmailStatus={settings.gmailStatus}
              calendarStatus={settings.calendarStatus}
              onReconnect={() => authApi.loginWithGoogle()}
              onDisconnect={() => disconnectMutation.mutate()}
              isDisconnecting={disconnectMutation.isPending}
            />
          )}

          {activeSection === "notifications" && (
            <NotificationSettings
              preferences={settings.notificationPreferences}
              onToggle={(key, value) =>
                updateNotificationsMutation.mutate({ ...settings.notificationPreferences, [key]: value })
              }
            />
          )}

          {activeSection === "ai-preferences" && (
            <AiPreferences
              preferences={settings.aiPreferences}
              onChange={(updates) =>
                updateAiPreferencesMutation.mutate({ ...settings.aiPreferences, ...updates })
              }
            />
          )}

          {activeSection === "security" && (
            <SecuritySettings
              sessions={settings.sessions}
              onRevokeSession={(id) => revokeSessionMutation.mutate(id)}
              onSignOutAllDevices={() => signOutAllMutation.mutate()}
            />
          )}

          {activeSection === "danger-zone" && (
            <DangerZone
              onClearAiData={() => clearAiDataMutation.mutate()}
              onDeleteAccount={() => deleteAccountMutation.mutate()}
              isClearing={clearAiDataMutation.isPending}
              isDeleting={deleteAccountMutation.isPending}
            />
          )}
        </div>
      </div>
    </div>
  );
}