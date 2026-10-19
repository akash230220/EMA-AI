import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import meetingApi from "@/api/meetingApi";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Fetches a paginated, filtered list of meetings.
 */
export function useMeetings(filters = {}) {
  return useQuery({
    queryKey: ["meetings", filters],
    queryFn: () => meetingApi.getMeetings(filters),
  });
}

/**
 * Fetches a single meeting by ID.
 */
export function useMeeting(meetingId) {
  return useQuery({
    queryKey: ["meeting", meetingId],
    queryFn: () => meetingApi.getMeetingById(meetingId),
    enabled: Boolean(meetingId),
  });
}

/**
 * Fetches upcoming meetings for Dashboard widgets.
 */
export function useUpcomingMeetings(days = 7) {
  return useQuery({
    queryKey: ["meetings", "upcoming", days],
    queryFn: () => meetingApi.getUpcomingMeetings({ days }),
  });
}

/**
 * Fetches lightweight meeting stats.
 */
export function useMeetingStats() {
  return useQuery({
    queryKey: ["meeting-stats"],
    queryFn: () => meetingApi.getMeetingStats(),
  });
}

function useInvalidateMeetings() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["meetings"] });
    queryClient.invalidateQueries({ queryKey: ["meeting-stats"] });
  };
}

/** Creates a new manual meeting. */
export function useCreateMeeting() {
  const invalidate = useInvalidateMeetings();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (payload) => meetingApi.createMeeting(payload),
    onSuccess: () => {
      invalidate();
      toast({ type: "success", message: "Meeting created." });
    },
    onError: () => toast({ type: "error", message: "Couldn't create meeting." }),
  });
}

/** Updates an existing meeting. */
export function useUpdateMeeting() {
  const invalidate = useInvalidateMeetings();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, updates }) => meetingApi.updateMeeting(id, updates),
    onSuccess: () => {
      invalidate();
      toast({ type: "success", message: "Meeting updated." });
    },
    onError: () => toast({ type: "error", message: "Couldn't update meeting." }),
  });
}

/** Confirms an AI-detected meeting. */
export function useConfirmMeeting() {
  const invalidate = useInvalidateMeetings();
  return useMutation({
    mutationFn: (id) => meetingApi.confirmMeeting(id),
    onSuccess: invalidate,
  });
}

/** Declines/dismisses an AI-detected meeting. */
export function useDeclineMeeting() {
  const invalidate = useInvalidateMeetings();
  return useMutation({
    mutationFn: (id) => meetingApi.declineMeeting(id),
    onSuccess: invalidate,
  });
}

/** Pushes a confirmed meeting to Google Calendar. */
export function useSyncToCalendar() {
  const invalidate = useInvalidateMeetings();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id) => meetingApi.syncToCalendar(id),
    onSuccess: () => {
      invalidate();
      toast({ type: "success", message: "Meeting added to Google Calendar." });
    },
    onError: () => toast({ type: "error", message: "Failed to sync to calendar." }),
  });
}

/** Removes a meeting from Google Calendar (keeps the local record). */
export function useUnsyncFromCalendar() {
  const invalidate = useInvalidateMeetings();
  return useMutation({
    mutationFn: (id) => meetingApi.unsyncFromCalendar(id),
    onSuccess: invalidate,
  });
}

/** Deletes a meeting permanently. */
export function useDeleteMeeting() {
  const invalidate = useInvalidateMeetings();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id) => meetingApi.deleteMeeting(id),
    onSuccess: () => {
      invalidate();
      toast({ type: "success", message: "Meeting deleted." });
    },
    onError: () => toast({ type: "error", message: "Couldn't delete meeting." }),
  });
}