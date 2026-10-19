import * as React from "react";
import { CalendarClock } from "lucide-react";
import MeetingCard from "./MeetingCard";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Groups meetings by date and renders them as day-sectioned cards
 * (e.g. "Today", "Tomorrow", "Mon, Aug 24"). Purely presentational —
 * parent MeetingsPage owns fetching/mutations via React Query +
 * meetingApi.
 *
 * @param {object} props
 * @param {object[]} props.meetings - each item includes a `dateGroupLabel` field
 * @param {boolean} [props.isLoading]
 * @param {string|null} [props.syncingMeetingId]
 * @param {(id: string) => void} props.onConfirm
 * @param {(id: string) => void} props.onDecline
 * @param {(id: string) => void} props.onSyncToCalendar
 * @param {(id: string) => void} props.onUnsyncFromCalendar
 * @param {(id: string) => void} props.onEdit
 * @param {(id: string) => void} props.onDelete
 */
export default function MeetingList({
  meetings = [],
  isLoading,
  syncingMeetingId,
  onConfirm,
  onDecline,
  onSyncToCalendar,
  onUnsyncFromCalendar,
  onEdit,
  onDelete,
}) {
  const grouped = React.useMemo(() => {
    const map = new Map();
    for (const meeting of meetings) {
      const key = meeting.dateGroupLabel || "Upcoming";
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(meeting);
    }
    return Array.from(map.entries());
  }, [meetings]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (meetings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
          <CalendarClock className="h-6 w-6 text-muted-foreground" />
        </div>
        <div>
          <p className="text-sm font-medium">No meetings found</p>
          <p className="text-xs text-muted-foreground">
            Meetings detected from your emails will appear here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {grouped.map(([dateLabel, dayMeetings]) => (
        <div key={dateLabel}>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {dateLabel}
          </h3>
          <div className="space-y-2">
            {dayMeetings.map((meeting) => (
              <MeetingCard
                key={meeting.id}
                meeting={meeting}
                onConfirm={onConfirm}
                onDecline={onDecline}
                onSyncToCalendar={onSyncToCalendar}
                onUnsyncFromCalendar={onUnsyncFromCalendar}
                onEdit={onEdit}
                onDelete={onDelete}
                isSyncing={syncingMeetingId === meeting.id}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}