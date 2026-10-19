import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

/**
 * Modal form for creating a new manual meeting or editing an
 * existing one (including AI-detected meetings the user wants to
 * adjust before confirming). Parent owns the create/update mutation
 * via meetingApi.
 *
 * @param {object} props
 * @param {boolean} props.open
 * @param {(open: boolean) => void} props.onOpenChange
 * @param {object|null} [props.initialMeeting]
 * @param {(payload: object) => void} props.onSubmit
 * @param {boolean} [props.isSubmitting]
 */
export default function MeetingFormDialog({ open, onOpenChange, initialMeeting, onSubmit, isSubmitting }) {
  const isEditing = Boolean(initialMeeting);

  const [title, setTitle] = React.useState("");
  const [startTime, setStartTime] = React.useState("");
  const [endTime, setEndTime] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [attendeesInput, setAttendeesInput] = React.useState("");

  React.useEffect(() => {
    if (open) {
      setTitle(initialMeeting?.title || "");
      setStartTime(initialMeeting?.startTime ? toLocalInputValue(initialMeeting.startTime) : "");
      setEndTime(initialMeeting?.endTime ? toLocalInputValue(initialMeeting.endTime) : "");
      setLocation(initialMeeting?.location || "");
      setDescription(initialMeeting?.description || "");
      setAttendeesInput((initialMeeting?.attendees || []).join(", "));
    }
  }, [open, initialMeeting]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim() || !startTime || !endTime) return;

    onSubmit({
      title: title.trim(),
      startTime: new Date(startTime).toISOString(),
      endTime: new Date(endTime).toISOString(),
      location: location.trim() || undefined,
      description: description.trim() || undefined,
      attendees: attendeesInput
        .split(",")
        .map((email) => email.trim())
        .filter(Boolean),
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Meeting" : "New Meeting"}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="meeting-title">Title</Label>
            <Input
              id="meeting-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Q3 Budget Review"
              autoFocus
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="meeting-start">Start time</Label>
              <Input
                id="meeting-start"
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="meeting-end">End time</Label>
              <Input
                id="meeting-end"
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="meeting-location">Location</Label>
            <Input
              id="meeting-location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Google Meet, Conference Room A"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="meeting-attendees">Attendees</Label>
            <Input
              id="meeting-attendees"
              value={attendeesInput}
              onChange={(e) => setAttendeesInput(e.target.value)}
              placeholder="comma-separated emails"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="meeting-description">Description</Label>
            <Textarea
              id="meeting-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="min-h-[70px]"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !title.trim() || !startTime || !endTime}>
              {isSubmitting ? "Saving..." : isEditing ? "Save changes" : "Create meeting"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Converts an ISO datetime string to the value format required by
 * <input type="datetime-local"> (local time, no timezone/seconds).
 */
function toLocalInputValue(isoString) {
  const date = new Date(isoString);
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}