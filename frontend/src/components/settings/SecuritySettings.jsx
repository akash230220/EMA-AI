import * as React from "react";
import { Shield, Monitor, Smartphone, LogOut } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

/**
 * Security overview: active sessions list + "sign out everywhere"
 * action. Since auth is Google OAuth-only, there's no password
 * management here — just session/device visibility and revocation.
 *
 * @param {object} props
 * @param {object[]} [props.sessions] - { id, deviceLabel, deviceType, location, lastActiveLabel, isCurrent }
 * @param {(sessionId: string) => void} props.onRevokeSession
 * @param {() => void} props.onSignOutAllDevices
 */
export default function SecuritySettings({ sessions = [], onRevokeSession, onSignOutAllDevices }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5">
          <Shield className="h-4 w-4" />
          Security
        </CardTitle>
        <CardDescription>
          Review devices signed into your account. Authentication is managed via Google OAuth 2.0.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-1">
        {sessions.map((session, i) => (
          <React.Fragment key={session.id}>
            <div className="flex items-center gap-3 py-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                {session.deviceType === "mobile" ? (
                  <Smartphone className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Monitor className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{session.deviceLabel}</p>
                  {session.isCurrent && (
                    <Badge variant="success" className="text-[10px]">This device</Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  {session.location} &middot; Active {session.lastActiveLabel}
                </p>
              </div>
              {!session.isCurrent && (
                <Button variant="ghost" size="sm" onClick={() => onRevokeSession(session.id)}>
                  Revoke
                </Button>
              )}
            </div>
            {i < sessions.length - 1 && <Separator />}
          </React.Fragment>
        ))}

        <div className="pt-4">
          <Button variant="outline" onClick={onSignOutAllDevices}>
            <LogOut className="h-4 w-4" />
            Sign out of all devices
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}