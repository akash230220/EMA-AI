import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TONE_OPTIONS = [
  { value: "formal", label: "Formal" },
  { value: "friendly", label: "Friendly" },
  { value: "concise", label: "Concise" },
];

const SUMMARY_LENGTH_OPTIONS = [
  { value: "short", label: "Short (1-2 sentences)" },
  { value: "medium", label: "Medium (3-4 sentences)" },
  { value: "detailed", label: "Detailed" },
];

/**
 * AI behavior preferences: default reply tone, summary length, and
 * toggles for auto-processing new emails vs. requiring manual
 * trigger, and whether AI can auto-send low-risk replies.
 *
 * @param {object} props
 * @param {object} props.preferences
 * @param {(updates: object) => void} props.onChange
 */
export default function AiPreferences({ preferences = {}, onChange }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Preferences</CardTitle>
        <CardDescription>Control how the AI pipeline behaves across your inbox.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-1">
        <div className="flex items-center justify-between py-3">
          <div>
            <Label className="text-sm font-medium">Default reply tone</Label>
            <p className="text-xs text-muted-foreground">Used when generating new AI replies</p>
          </div>
          <Select
            value={preferences.defaultReplyTone || "friendly"}
            onValueChange={(v) => onChange({ defaultReplyTone: v })}
          >
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TONE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Separator />

        <div className="flex items-center justify-between py-3">
          <div>
            <Label className="text-sm font-medium">Summary length</Label>
            <p className="text-xs text-muted-foreground">How detailed AI email summaries should be</p>
          </div>
          <Select
            value={preferences.summaryLength || "medium"}
            onValueChange={(v) => onChange({ summaryLength: v })}
          >
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SUMMARY_LENGTH_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Separator />

        <div className="flex items-center justify-between py-3">
          <div>
            <Label htmlFor="auto-process" className="text-sm font-medium">
              Auto-process new emails
            </Label>
            <p className="text-xs text-muted-foreground">
              Run the full AI pipeline automatically on every synced email
            </p>
          </div>
          <Switch
            id="auto-process"
            checked={preferences.autoProcessNewEmails ?? true}
            onCheckedChange={(checked) => onChange({ autoProcessNewEmails: checked })}
          />
        </div>
        <Separator />

        <div className="flex items-center justify-between py-3">
          <div>
            <Label htmlFor="auto-meeting-sync" className="text-sm font-medium">
              Auto-sync confirmed meetings
            </Label>
            <p className="text-xs text-muted-foreground">
              Push confirmed meetings to Google Calendar without a manual step
            </p>
          </div>
          <Switch
            id="auto-meeting-sync"
            checked={preferences.autoSyncConfirmedMeetings ?? false}
            onCheckedChange={(checked) => onChange({ autoSyncConfirmedMeetings: checked })}
          />
        </div>
      </CardContent>
    </Card>
  );
}