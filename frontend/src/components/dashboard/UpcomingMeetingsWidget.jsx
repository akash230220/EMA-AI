import * as React from "react";
import { useNavigate } from "react-router-dom";
import { CalendarClock, ChevronRight, Video } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

/**
 * Compact upcoming-meetings list for the Dashboard.
 *
 * @param {object} props
 * @param {{id: string, title: string, startTimeLabel: string, dateLabel: string, location?: string}[]} [props.meetings]
 * @param {boolean} [props.isLoading]
 */
export default function UpcomingMeetingsWidget({ meetings = [], isLoading }) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Upcoming Meetings</CardTitle>
        <Button variant="ghost" size="sm" onClick={() => navigate("/meetings")}>
          View all <ChevronRight className="h-3.5 w-3.5" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-1">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)
        ) : meetings.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
            <CalendarClock className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No upcoming meetings</p>
          </div>
        ) : (
          meetings.map((meeting) => (
            <button
              key={meeting.id}
              onClick={() => navigate(`/meetings/${meeting.id}`)}
              className="flex w-full items-center gap-3 rounded-lg px-2 py-2.5 text-left transition-colors hover:bg-accent"
            >
              <div className="flex h-10 w-10 shrink-0 flex-col items-center justify-center rounded-lg bg-indigo-50 text-indigo-700">
                <Video className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{meeting.title}</p>
                <p className="truncate text-xs text-muted-foreground">
                  {meeting.dateLabel} &middot; {meeting.startTimeLabel}
                  {meeting.location ? ` · ${meeting.location}` : ""}
                </p>
              </div>
            </button>
          ))
        )}
      </CardContent>
    </Card>
  );
}