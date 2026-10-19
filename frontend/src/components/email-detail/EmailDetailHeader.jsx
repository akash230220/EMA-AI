import * as React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Archive, Trash2, MailOpen, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const PRIORITY_VARIANT = { high: "destructive", medium: "warning", low: "success" };

/**
 * Top header bar for the Email Detail page: subject line, back
 * navigation, priority badge, and quick actions (archive/delete/
 * mark unread/star).
 *
 * @param {object} props
 * @param {object} props.email
 * @param {() => void} props.onArchive
 * @param {() => void} props.onDelete
 * @param {() => void} props.onMarkUnread
 * @param {() => void} props.onToggleStar
 */
export default function EmailDetailHeader({ email, onArchive, onDelete, onMarkUnread, onToggleStar }) {
  const navigate = useNavigate();

  return (
    <div className="mb-4 space-y-3">
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" onClick={() => navigate("/inbox")}>
          <ArrowLeft className="h-4 w-4" />
          Back to Inbox
        </Button>

        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={onToggleStar} aria-label="Star email">
            <Star className={cn("h-4 w-4", email?.isStarred ? "fill-amber-400 text-amber-400" : "text-muted-foreground")} />
          </Button>
          <Button variant="ghost" size="icon" onClick={onMarkUnread} aria-label="Mark as unread">
            <MailOpen className="h-4 w-4 text-muted-foreground" />
          </Button>
          <Button variant="ghost" size="icon" onClick={onArchive} aria-label="Archive">
            <Archive className="h-4 w-4 text-muted-foreground" />
          </Button>
          <Button variant="ghost" size="icon" onClick={onDelete} aria-label="Delete">
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <h1 className="text-xl font-semibold tracking-tight">{email?.subject}</h1>
        {email?.priority && (
          <Badge variant={PRIORITY_VARIANT[email.priority] || "outline"} className="capitalize">
            {email.priority}
          </Badge>
        )}
        {email?.category && (
          <Badge variant="secondary" className="capitalize">
            {email.category}
          </Badge>
        )}
      </div>
    </div>
  );
}