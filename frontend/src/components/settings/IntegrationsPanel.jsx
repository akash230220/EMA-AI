import * as React from "react";
import { Mail, CalendarClock, CheckCircle2, AlertCircle, RefreshCw, Unlink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

/**
 * Card showing connection status for Gmail and Google Calendar
 * (the two OAuth-scoped integrations), with reconnect/disconnect
 * actions and last-sync timestamps.
 *
 * @param {object} props
 * @param {object} props.gmailStatus - { connected, lastSyncedAtLabel, email }
 * @param {object} props.calendarStatus - { connected, lastSyncedAtLabel }
 * @param {() => void} props.onReconnect
 * @param {() => void} props.onDisconnect
 * @param {boolean} [props.isReconnecting]
 * @param {boolean} [props.isDisconnecting]
 */
export default function IntegrationsPanel({
  gmailStatus,
  calendarStatus,
  onReconnect,
  onDisconnect,
  isReconnecting,
  isDisconnecting,
}) {
  const [disconnectDialogOpen, setDisconnectDialogOpen] = React.useState(false);

  const confirmDisconnect = () => {
    onDisconnect();
    setDisconnectDialogOpen(false);
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Integrations</CardTitle>
          <CardDescription>
            Manage the Google services connected to your AI Email OS account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <IntegrationRow
            icon={Mail}
            iconColor="text-red-600 bg-red-50"
            title="Gmail"
            description="Inbox sync, AI processing, and reply sending"
            connected={gmailStatus?.connected}
            detailLabel={
              gmailStatus?.connected
                ? `${gmailStatus.email} · Last synced ${gmailStatus.lastSyncedAtLabel}`
                : "Not connected"
            }
          />
          <IntegrationRow
            icon={CalendarClock}
            iconColor="text-blue-600 bg-blue-50"
            title="Google Calendar"
            description="Meeting detection and event creation"
            connected={calendarStatus?.connected}
            detailLabel={
              calendarStatus?.connected
                ? `Last synced ${calendarStatus.lastSyncedAtLabel}`
                : "Not connected"
            }
          />

          <div className="flex flex-wrap items-center gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={onReconnect} disabled={isReconnecting}>
              <RefreshCw className={cn("h-3.5 w-3.5", isReconnecting && "animate-spin")} />
              {isReconnecting ? "Reconnecting..." : "Reconnect Google account"}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
              onClick={() => setDisconnectDialogOpen(true)}
              disabled={isDisconnecting}
            >
              <Unlink className="h-3.5 w-3.5" />
              Disconnect
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={disconnectDialogOpen} onOpenChange={setDisconnectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Disconnect Google account?</DialogTitle>
            <DialogDescription>
              This will stop inbox syncing, AI processing, and calendar features. Your existing
              data will be preserved, but nothing new will sync until you reconnect.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDisconnectDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDisconnect}>
              Disconnect
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function IntegrationRow({ icon: Icon, iconColor, title, description, connected, detailLabel }) {
  return (
    <div className="flex items-center gap-3 rounded-md border border-border p-3">
      <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-lg", iconColor)}>
        <Icon className="h-4.5 w-4.5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium">{title}</p>
          {connected ? (
            <Badge variant="success" className="gap-1 text-[10px]">
              <CheckCircle2 className="h-2.5 w-2.5" />
              Connected
            </Badge>
          ) : (
            <Badge variant="outline" className="gap-1 text-[10px] border-amber-300 text-amber-700">
              <AlertCircle className="h-2.5 w-2.5" />
              Not connected
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground">{description}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{detailLabel}</p>
      </div>
    </div>
  );
}
