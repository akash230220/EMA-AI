import * as React from "react";
import { useNavigate } from "react-router-dom";
import {
  CalendarClock,
  MapPin,
  Users,
  Mail,
  Check,
  X,
  CalendarPlus,
  CalendarCheck,
  MoreVertical,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const STATUS_CONFIG = {
  detected: { label: "Needs review", variant: "warning" },
  confirmed: { label: "Confirmed", variant: "secondary" },
  declined: { label: "Declined", variant: "outline" },
  synced: { label: "Synced to Calendar", variant: "success" },
};

/**
 * Single meeting card — shows title, time, location, attendees,
 * source (AI-detected vs manual), and status-appropriate actions
 * (confirm/decline for detected, sync/unsync for confirmed).
 *
 * @param {object} props
 * @param {object} props.meeting
 * @param {(id: string) => void} props.onConfirm
 * @param {(id: string) => void} props.onDecline
 * @param {(id: string) => void} props.onSyncToCalendar
 * @param {(id: string) => void} props.onUnsyncFromCalendar
 * @param {(id: string) => void} props.onEdit
 * @param {(id: string) => void} props.onDelete
 * @param {boolean} [props.isSyncing]
 */
export default function MeetingCard({
  meeting,
  onConfirm,
  onDecline,
  onSyncToCalendar,
  onUnsyncFromCalendar,
  onEdit,
  onDelete,
  isSyncing,
}) {
  const navigate = useNavigate();
  const status = STATUS_CONFIG[meeting.status] || STATUS_CONFIG.detected;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            <div className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-lg bg-indigo-50 text-indigo-700">
              <span className="text-[10px] font-medium uppercase leading-none">
                {meeting.dateShortLabel?.month}
              </span>
              <span className="text-base font-bold leading-none">{meeting.dateShortLabel?.day}</span>
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="truncate text-sm font-semibold">{meeting.title}</h3>
                {meeting.source === "ai_detected" && (
                  <Badge variant="outline" className="shrink-0 text-[10px] px-1.5 py-0 border-indigo-300 text-indigo-700">
                    AI
                  </Badge>
                )}
              </div>
              <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                <CalendarClock className="h-3 w-3" />
                {meeting.startTimeLabel} &ndash; {meeting.endTimeLabel}
              </p>
              {meeting.location && (
                <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                  <MapPin className="h-3 w-3" />
                  {meeting.location}
                </p>
              )}
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="shrink-0 text-muted-foreground hover:text-foreground">
                <MoreVertical className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(meeting.id)}>Edit</DropdownMenuItem>
              {meeting.sourceEmailId && (
                <DropdownMenuItem onClick={() => navigate(`/inbox/${meeting.sourceEmailId}`)}>
                  <Mail className="mr-2 h-3.5 w-3.5" />
                  View source email
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={() => onDelete(meeting.id)} className="text-destructive focus:text-destructive">
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {meeting.attendees?.length > 0 && (
          <div className="mt-3 flex items-center gap-1.5">
            <div className="flex -space-x-1.5">
              {meeting.attendees.slice(0, 4).map((attendee, i) => (
                <Avatar key={i} className="h-5 w-5 border-2 border-background">
                  <AvatarFallback className="text-[9px]">
                    {attendee[0]?.toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              ))}
            </div>
            {meeting.attendees.length > 4 && (
              <span className="text-[11px] text-muted-foreground">
                +{meeting.attendees.length - 4} more
              </span>
            )}
          </div>
        )}

        <div className="mt-3 flex items-center justify-between">
          <Badge variant={status.variant} className="text-[10px]">
            {status.label}
          </Badge>

          <div className="flex items-center gap-1.5">
            {meeting.status === "detected" && (
              <>
                <Button size="sm" className="h-7 px-2 text-xs" onClick={() => onConfirm(meeting.id)}>
                  <Check className="h-3 w-3" />
                  Confirm
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 px-2 text-xs"
                  onClick={() => onDecline(meeting.id)}
                >
                  <X className="h-3 w-3" />
                  Decline
                </Button>
              </>
            )}

            {meeting.status === "confirmed" && (
              <Button
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => onSyncToCalendar(meeting.id)}
                disabled={isSyncing}
              >
                <CalendarPlus className="h-3 w-3" />
                {isSyncing ? "Syncing..." : "Add to Calendar"}
              </Button>
            )}

            {meeting.status === "synced" && (
              <Button
                size="sm"
                variant="outline"
                className="h-7 px-2 text-xs"
                onClick={() => onUnsyncFromCalendar(meeting.id)}
                disabled={isSyncing}
              >
                <CalendarCheck className="h-3 w-3 text-emerald-600" />
                Synced
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}