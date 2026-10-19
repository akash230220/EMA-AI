import * as React from "react";
import { CalendarCheck2, AlertCircle, RefreshCw } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

/**
 * Status banner showing whether Google Calendar is connected, and
 * a summary of how many meetings are synced vs. pending. Lives at
 * the top of the Meetings page. Connection itself happens via the
 * Google OAuth flow (scopes requested at login) — this component
 * reflects status and lets the user re-trigger connection if it
 * lapses (e.g. revoked access, expired refresh token).
 *
 * @param {object} props
 * @param {boolean} props.isConnected
 * @param {number} [props.syncedCount]
 * @param {number} [props.pendingCount]
 * @param {() => void} [props.onReconnect]
 * @param {boolean} [props.isReconnecting]
 */
export default function CalendarSync({
  isConnected,
  syncedCount = 0,
  pendingCount = 0,
  onReconnect,
  isReconnecting,
}) {
  if (isConnected) {
    return (
      <Card className="border-emerald-200 bg-emerald-50/50">
        <CardContent className="flex items-center justify-between gap-3 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
              <CalendarCheck2 className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-medium">Google Calendar connected</p>
              <p className="text-xs text-muted-foreground">
                {syncedCount} synced &middot; {pendingCount} pending confirmation
              </p>
            </div>
          </div>
          {pendingCount > 0 && (
            <Badge variant="warning" className="text-[11px]">
              {pendingCount} awaiting review
            </Badge>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-amber-200 bg-amber-50/50">
      <CardContent className="flex items-center justify-between gap-3 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-amber-100 text-amber-700">
            <AlertCircle className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-medium">Google Calendar not connected</p>
            <p className="text-xs text-muted-foreground">
              Connect your calendar to sync confirmed meetings automatically.
            </p>
          </div>
        </div>
        <Button size="sm" onClick={onReconnect} disabled={isReconnecting}>
          <RefreshCw className={cn("h-3.5 w-3.5", isReconnecting && "animate-spin")} />
          {isReconnecting ? "Connecting..." : "Connect"}
        </Button>
      </CardContent>
    </Card>
  );
}