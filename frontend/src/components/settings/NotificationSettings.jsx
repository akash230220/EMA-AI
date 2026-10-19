import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

const NOTIFICATION_ITEMS = [
  { key: "highPriorityEmail", label: "High priority emails", description: "Get notified when an urgent email arrives" },
  { key: "meetingDetected", label: "Meeting detected", description: "Get notified when a meeting is found in an email" },
  { key: "taskDetected", label: "Task detected", description: "Get notified when a task is extracted from an email" },
  { key: "dailyBrief", label: "Daily brief", description: "Receive your AI-generated daily summary each morning" },
  { key: "automationFired", label: "Automation activity", description: "Get notified when an automation rule takes action" },
  { key: "weeklyDigest", label: "Weekly analytics digest", description: "A summary of your inbox activity, sent weekly" },
];

/**
 * Toggle list for notification preferences. Controlled component —
 * parent SettingsPage owns state and persistence via a settings API.
 *
 * @param {object} props
 * @param {object} props.preferences - map of NOTIFICATION_ITEMS keys to booleans
 * @param {(key: string, value: boolean) => void} props.onToggle
 */
export default function NotificationSettings({ preferences = {}, onToggle }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        <CardDescription>Choose what you want to be notified about.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-1">
        {NOTIFICATION_ITEMS.map((item, i) => (
          <React.Fragment key={item.key}>
            <div className="flex items-center justify-between py-3">
              <div>
                <Label htmlFor={item.key} className="text-sm font-medium">
                  {item.label}
                </Label>
                <p className="text-xs text-muted-foreground">{item.description}</p>
              </div>
              <Switch
                id={item.key}
                checked={Boolean(preferences[item.key])}
                onCheckedChange={(checked) => onToggle(item.key, checked)}
              />
            </div>
            {i < NOTIFICATION_ITEMS.length - 1 && <Separator />}
          </React.Fragment>
        ))}
      </CardContent>
    </Card>
  );
}