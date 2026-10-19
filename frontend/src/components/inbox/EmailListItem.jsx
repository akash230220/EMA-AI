import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Star, Paperclip, CalendarClock, CheckSquare } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

const PRIORITY_VARIANT = {
  high: "destructive",
  medium: "warning",
  low: "success",
};

const SENTIMENT_DOT = {
  positive: "bg-emerald-500",
  neutral: "bg-gray-400",
  negative: "bg-red-500",
};

/**
 * Single row in the email list. Handles read/unread styling,
 * multi-select checkbox, AI badges (priority/category), and
 * quick indicators for attachments, detected meetings, and tasks.
 *
 * @param {object} props
 * @param {object} props.email
 * @param {boolean} props.selected
 * @param {(id: string, checked: boolean) => void} props.onSelectChange
 */
export default function EmailListItem({ email, selected, onSelectChange }) {
  const navigate = useNavigate();

  return (
    <div
      className={cn(
        "group flex items-start gap-3 border-b border-border px-3 py-3 transition-colors hover:bg-accent cursor-pointer",
        !email.isRead && "bg-primary/[0.03]"
      )}
      onClick={() => navigate(`/inbox/${email.id}`)}
    >
      <div
        className="flex items-center pt-1"
        onClick={(e) => e.stopPropagation()}
      >
        <Checkbox
          checked={selected}
          onCheckedChange={(checked) => onSelectChange(email.id, Boolean(checked))}
          aria-label={`Select email from ${email.senderName}`}
        />
      </div>

      <Avatar className="mt-0.5 h-9 w-9 shrink-0">
        <AvatarFallback className="text-xs">
          {email.senderName?.[0]?.toUpperCase() || "?"}
        </AvatarFallback>
      </Avatar>

      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className={cn("truncate text-sm", !email.isRead ? "font-semibold" : "font-medium")}>
            {email.senderName || email.senderEmail}
          </p>
          <div className="flex shrink-0 items-center gap-1.5">
            {email.sentiment && (
              <span
                className={cn("h-1.5 w-1.5 rounded-full", SENTIMENT_DOT[email.sentiment] || "bg-gray-300")}
                title={`Sentiment: ${email.sentiment}`}
              />
            )}
            <span className="text-xs text-muted-foreground">{email.receivedAtLabel}</span>
          </div>
        </div>

        <p className={cn("truncate text-sm", !email.isRead ? "font-medium text-foreground" : "text-muted-foreground")}>
          {email.subject}
        </p>

        <div className="mt-0.5 flex items-center gap-2">
          <p className="truncate text-xs text-muted-foreground flex-1">{email.aiSummary || email.snippet}</p>

          <div className="flex shrink-0 items-center gap-1.5">
            {email.hasAttachment && <Paperclip className="h-3.5 w-3.5 text-muted-foreground" />}
            {email.hasMeeting && (
              <CalendarClock className="h-3.5 w-3.5 text-indigo-500" title="Meeting detected" />
            )}
            {email.hasTask && (
              <CheckSquare className="h-3.5 w-3.5 text-violet-500" title="Task detected" />
            )}
          </div>
        </div>

        <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
          {email.priority && (
            <Badge variant={PRIORITY_VARIANT[email.priority] || "outline"} className="capitalize text-[10px] px-1.5 py-0">
              {email.priority}
            </Badge>
          )}
          {email.category && (
            <Badge variant="secondary" className="capitalize text-[10px] px-1.5 py-0">
              {email.category}
            </Badge>
          )}
          {email.pendingReply && (
            <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-amber-300 text-amber-700">
              Awaiting reply
            </Badge>
          )}
        </div>
      </div>

      <button
        onClick={(e) => {
          e.stopPropagation();
          // starring handled by parent via a passed callback in a fuller impl
        }}
        className="mt-0.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
        aria-label="Star email"
      >
        <Star className={cn("h-4 w-4", email.isStarred ? "fill-amber-400 text-amber-400 opacity-100" : "text-muted-foreground")} />
      </button>
    </div>
  );
}