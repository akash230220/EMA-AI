import * as React from "react";
import { Camera, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TIMEZONE_OPTIONS = [
  "Asia/Kolkata",
  "Asia/Dubai",
  "Asia/Singapore",
  "Europe/London",
  "America/New_York",
  "America/Los_Angeles",
  "UTC",
];

/**
 * Editable profile form: name, timezone, avatar (read-only,
 * sourced from Google account since login is OAuth-only), and
 * connected Google account email (read-only).
 *
 * @param {object} props
 * @param {object} props.user
 * @param {(updates: object) => void} props.onSave
 * @param {boolean} [props.isSaving]
 */
export default function ProfileForm({ user, onSave, isSaving }) {
  const [name, setName] = React.useState(user?.name || "");
  const [timezone, setTimezone] = React.useState(user?.timezone || "Asia/Kolkata");

  React.useEffect(() => {
    setName(user?.name || "");
    setTimezone(user?.timezone || "Asia/Kolkata");
  }, [user]);

  const hasChanges = name !== (user?.name || "") || timezone !== (user?.timezone || "Asia/Kolkata");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!hasChanges) return;
    onSave({ name: name.trim(), timezone });
  };

  const initials = React.useMemo(() => {
    if (!user?.name) return "U";
    return user.name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
  }, [user?.name]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile</CardTitle>
        <CardDescription>Manage your personal information and preferences.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Avatar className="h-16 w-16">
                <AvatarImage src={user?.avatarUrl} alt={user?.name} />
                <AvatarFallback className="text-lg">{initials}</AvatarFallback>
              </Avatar>
              <div className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-muted text-muted-foreground" title="Synced from Google account">
                <Camera className="h-3 w-3" />
              </div>
            </div>
            <div>
              <p className="text-sm font-medium">{user?.name}</p>
              <p className="text-xs text-muted-foreground">Avatar synced from your Google account</p>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="profile-name">Full name</Label>
            <Input id="profile-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="profile-email">Email</Label>
            <Input id="profile-email" value={user?.email || ""} disabled className="bg-muted" />
            <p className="text-xs text-muted-foreground">
              Connected via Google — email cannot be changed here.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label>Timezone</Label>
            <Select value={timezone} onValueChange={setTimezone}>
              <SelectTrigger className="w-full sm:w-64">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TIMEZONE_OPTIONS.map((tz) => (
                  <SelectItem key={tz} value={tz}>
                    {tz}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Used for daily briefs, meeting times, and analytics.
            </p>
          </div>

          <div className="flex justify-end">
            <Button type="submit" disabled={!hasChanges || isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
              {isSaving ? "Saving..." : "Save changes"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}