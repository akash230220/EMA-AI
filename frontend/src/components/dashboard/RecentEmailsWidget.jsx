import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Mail, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

const PRIORITY_VARIANT = {
  high: "destructive",
  medium: "warning",
  low: "success",
};

/**
 * Compact list of the most recent emails for the Dashboard,
 * with priority badges and a link to the full Inbox.
 *
 * @param {object} props
 * @param {object[]} [props.emails]
 * @param {boolean} [props.isLoading]
 */
export default function RecentEmailsWidget({ emails = [], isLoading }) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Recent Emails</CardTitle>
        <Button variant="ghost" size="sm" onClick={() => navigate("/inbox")}>
          View all <ChevronRight className="h-3.5 w-3.5" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-1">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)
        ) : emails.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
            <Mail className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No recent emails</p>
          </div>
        ) : (
          emails.map((email) => (
            <button
              key={email.id}
              onClick={() => navigate(`/inbox/${email.id}`)}
              className="flex w-full items-start gap-3 rounded-lg px-2 py-2.5 text-left transition-colors hover:bg-accent"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
                {email.senderName?.[0]?.toUpperCase() || "?"}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm font-medium">{email.senderName || email.senderEmail}</p>
                  <span className="shrink-0 text-xs text-muted-foreground">{email.receivedAtLabel}</span>
                </div>
                <p className="truncate text-sm text-muted-foreground">{email.subject}</p>
              </div>
              {email.priority && (
                <Badge variant={PRIORITY_VARIANT[email.priority] || "outline"} className="shrink-0 capitalize">
                  {email.priority}
                </Badge>
              )}
            </button>
          ))
        )}
      </CardContent>
    </Card>
  );
}