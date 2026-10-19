import * as React from "react";
import { User, Plug, Bell, Shield, Sparkles, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

export const SETTINGS_SECTIONS = [
  { id: "profile", label: "Profile", icon: User },
  { id: "integrations", label: "Integrations", icon: Plug },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "ai-preferences", label: "AI Preferences", icon: Sparkles },
  { id: "security", label: "Security", icon: Shield },
  { id: "danger-zone", label: "Danger Zone", icon: Trash2 },
];

/**
 * Vertical section nav for the Settings page (tabs-as-sidebar
 * pattern). Purely presentational — parent SettingsPage owns the
 * active section state.
 *
 * @param {object} props
 * @param {string} props.activeSection
 * @param {(id: string) => void} props.onSectionChange
 */
export default function SettingsNav({ activeSection, onSectionChange }) {
  return (
    <nav className="w-full shrink-0 space-y-0.5 md:w-52">
      {SETTINGS_SECTIONS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          onClick={() => onSectionChange(id)}
          className={cn(
            "flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
            activeSection === id
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            id === "danger-zone" && activeSection !== id && "text-destructive/80 hover:text-destructive"
          )}
        >
          <Icon className="h-4 w-4 shrink-0" />
          {label}
        </button>
      ))}
    </nav>
  );
}