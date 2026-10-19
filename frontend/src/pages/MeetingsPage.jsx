import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import PageHeader from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import MeetingList from "@/components/meetings/MeetingList";
import MeetingFilters from "@/components/meetings/MeetingFilters";
import MeetingFormDialog from "@/components/meetings/MeetingFormDialog";
import CalendarSync from "@/components/meetings/CalendarSync";
import ConfirmDialog from "@/components/shared/ConfirmDialog";
import meetingApi from "@/api/meetingApi";
import authApi from "@/api/authApi";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Meetings — list of AI-detected and manually created meetings,
 * grouped by date, with Google Calendar sync controls.
 */
export default function MeetingsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [filters, setFilters] = React.useState({});
  const [formOpen, setFormOpen] = React.useState(false);
  const [editingMeeting, setEditingMeeting] = React.useState(null);
  const [deleteTargetId, setDeleteTargetId] = React.useState(null);
  const [syncingMeetingId, setSyncingMeetingId] = React.useState(null);

  const meetingsQuery = useQuery({
    queryKey: ["meetings", filters],
    queryFn: () => meetingApi.getMeetings({ ...filters, page: 1, pageSize: 100, sortBy: "start_time", sortOrder: "asc" }),
  });

  const statsQuery = useQuery({
    queryKey: ["meeting-stats"],
    queryFn: () => meetingApi.getMeetingStats(),
  });

  const invalidateMeetings = () => {
    queryClient.invalidateQueries({ queryKey: ["meetings"] });
    queryClient.invalidateQueries({ queryKey: ["meeting-stats"] });
  };

  const confirmMutation = useMutation({
    mutationFn: (id) => meetingApi.confirmMeeting(id),
    onSuccess: invalidateMeetings,
  });
  const declineMutation = useMutation({
    mutationFn: (id) => meetingApi.declineMeeting(id),
    onSuccess: invalidateMeetings,
  });

  const syncMutation = useMutation({
    mutationFn: (id) => meetingApi.syncToCalendar(id),
    onMutate: (id) => setSyncingMeetingId(id),
    onSuccess: () => {
      toast({ type: "success", message: "Meeting added to Google Calendar." });
      invalidateMeetings();
    },
    onError: () => toast({ type: "error", message: "Failed to sync to calendar." }),
    onSettled: () => setSyncingMeetingId(null),
  });

  const unsyncMutation = useMutation({
    mutationFn: (id) => meetingApi.unsyncFromCalendar(id),
    onMutate: (id) => setSyncingMeetingId(id),
    onSuccess: invalidateMeetings,
    onSettled: () => setSyncingMeetingId(null),
  });

  const createMutation = useMutation({
    mutationFn: (payload) => meetingApi.createMeeting(payload),
    onSuccess: () => {
      invalidateMeetings();
      toast({ type: "success", message: "Meeting created." });
      setFormOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }) => meetingApi.updateMeeting(id, updates),
    onSuccess: () => {
      invalidateMeetings();
      toast({ type: "success", message: "Meeting updated." });
      setFormOpen(false);
      setEditingMeeting(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => meetingApi.deleteMeeting(id),
    onSuccess: () => {
      invalidateMeetings();
      toast({ type: "success", message: "Meeting deleted." });
      setDeleteTargetId(null);
    },
  });

  const handleFormSubmit = (payload) => {
    if (editingMeeting) {
      updateMutation.mutate({ id: editingMeeting.id, updates: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const meetings = meetingsQuery.data?.items || [];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Meetings"
        description="Meetings detected from your inbox and synced with Google Calendar."
        actions={
          <Button onClick={() => { setEditingMeeting(null); setFormOpen(true); }}>
            <Plus className="h-4 w-4" />
            New Meeting
          </Button>
        }
      />

      <CalendarSync
        isConnected={statsQuery.data ? statsQuery.data.syncedToCalendar >= 0 : true}
        syncedCount={statsQuery.data?.syncedToCalendar}
        pendingCount={statsQuery.data?.pendingConfirmation}
        onReconnect={() => authApi.loginWithGoogle()}
      />

      <MeetingFilters filters={filters} onFiltersChange={setFilters} />

      <MeetingList
        meetings={meetings}
        isLoading={meetingsQuery.isLoading}
        syncingMeetingId={syncingMeetingId}
        onConfirm={(id) => confirmMutation.mutate(id)}
        onDecline={(id) => declineMutation.mutate(id)}
        onSyncToCalendar={(id) => syncMutation.mutate(id)}
        onUnsyncFromCalendar={(id) => unsyncMutation.mutate(id)}
        onEdit={(id) => {
          setEditingMeeting(meetings.find((m) => m.id === id));
          setFormOpen(true);
        }}
        onDelete={(id) => setDeleteTargetId(id)}
      />

      <MeetingFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        initialMeeting={editingMeeting}
        onSubmit={handleFormSubmit}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      />

      <ConfirmDialog
        open={Boolean(deleteTargetId)}
        onOpenChange={(open) => !open && setDeleteTargetId(null)}
        title="Delete this meeting?"
        description="This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={() => deleteMutation.mutate(deleteTargetId)}
        isConfirming={deleteMutation.isPending}
      />
    </div>
  );
}