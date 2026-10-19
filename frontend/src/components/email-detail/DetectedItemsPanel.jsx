import * as React from "react";
import { useNavigate } from "react-router-dom";
import { CalendarClock, CheckSquare, Check, X, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

/**
 * Shows any meeting(s) or task(s) the AI pipeline (Meeting Agent /
 * Task Agent) detected within this email, with quick confirm/dismiss
 * actions and a jump-to link once created.
 *
 * @param {object} props
 * @param {object[]} [props.detectedMeetings]
 * @param {object[]} [props.detectedTasks]
 * @param {(meetingId: string) => void} props.onConfirmMeeting
 * @param {(meetingId: string) => void} props.onDeclineMeeting
 * @param {(taskId: string) => void} props.onCompleteTask
 * @param {(taskId: string) => void} props.onDismissTask
 */
export default function DetectedItemsPanel({
  detectedMeetings = [],
  detectedTasks = [],
  onConfirmMeeting,
  onDeclineMeeting,
  onCompleteTask,
  onDismissTask,
}) {
  const navigate = useNavigate();

  if (detectedMeetings.length === 0 && detectedTasks.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Detected Items</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {detectedMeetings.map((meeting) => (
          <div key={meeting.id} className="rounded-md border border-indigo-200 bg-indigo-50/50 p-3">
            <div className="flex items-start gap-2">
              <CalendarClock className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{meeting.title}</p>
                <p className="text-xs text-muted-foreground">
                  {meeting.startTimeLabel}
                  {meeting.location ? ` · ${meeting.location}` : ""}
                </p>
                {meeting.status === "detected" ? (
                  <div className="mt-2 flex items-center gap-1.5">
                    <Button size="sm" className="h-7 px-2 text-xs" onClick={() => onConfirmMeeting(meeting.id)}>
                      <Check className="h-3 w-3" />
                      Confirm
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 px-2 text-xs"
                      onClick={() => onDeclineMeeting(meeting.id)}
                    >
                      <X className="h-3 w-3" />
                      Dismiss
                    </Button>
                  </div>
                ) : (
                  <div className="mt-2 flex items-center gap-2">
                    <Badge variant="outline" className="capitalize text-[10px]">
                      {meeting.status}
                    </Badge>
                    <button
                      onClick={() => navigate(`/meetings/${meeting.id}`)}
                      className="flex items-center gap-0.5 text-[11px] text-primary hover:underline"
                    >
                      View <ExternalLink className="h-3 w-3" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {detectedTasks.map((task) => (
          <div key={task.id} className="rounded-md border border-violet-200 bg-violet-50/50 p-3">
            <div className="flex items-start gap-2">
              <CheckSquare className="mt-0.5 h-4 w-4 shrink-0 text-violet-600" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{task.title}</p>
                {task.dueDateLabel && (
                  <p className="text-xs text-muted-foreground">Due {task.dueDateLabel}</p>
                )}
                {task.status === "pending" ? (
                  <div className="mt-2 flex items-center gap-1.5">
                    <Button size="sm" className="h-7 px-2 text-xs" onClick={() => onCompleteTask(task.id)}>
                      <Check className="h-3 w-3" />
                      Complete
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 px-2 text-xs"
                      onClick={() => onDismissTask(task.id)}
                    >
                      <X className="h-3 w-3" />
                      Dismiss
                    </Button>
                  </div>
                ) : (
                  <div className="mt-2 flex items-center gap-2">
                    <Badge variant="outline" className="capitalize text-[10px]">
                      {task.status}
                    </Badge>
                    <button
                      onClick={() => navigate(`/tasks?highlight=${task.id}`)}
                      className="flex items-center gap-0.5 text-[11px] text-primary hover:underline"
                    >
                      View <ExternalLink className="h-3 w-3" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}