import * as React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import EmailDetailHeader from "@/components/email-detail/EmailDetailHeader";
import ThreadView from "@/components/email-detail/ThreadView";
import AISummaryPanel from "@/components/email-detail/AISummaryPanel";
import DetectedItemsPanel from "@/components/email-detail/DetectedItemsPanel";
import ReplyComposer from "@/components/email-detail/ReplyComposer";
import emailApi from "@/api/emailApi";
import taskApi from "@/api/taskApi";
import meetingApi from "@/api/meetingApi";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Email Detail — full thread view + AI insights rail + reply
 * composer for a single email, identified by :emailId route param.
 */
export default function EmailDetailPage() {
  const { emailId } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [replyDrafts, setReplyDrafts] = React.useState([]);

  const emailQuery = useQuery({
    queryKey: ["email", emailId],
    queryFn: () => emailApi.getEmailById(emailId),
    enabled: Boolean(emailId),
  });

  // Mark as read on open
  React.useEffect(() => {
    if (emailQuery.data && !emailQuery.data.isRead) {
      emailApi.markAsRead(emailId, true).then(() => {
        queryClient.invalidateQueries({ queryKey: ["emails"] });
      });
    }
  }, [emailQuery.data, emailId, queryClient]);

  const reprocessMutation = useMutation({
    mutationFn: () => emailApi.reprocessEmail(emailId),
    onSuccess: (data) => {
      queryClient.setQueryData(["email", emailId], data);
      toast({ type: "success", message: "Email re-analyzed." });
    },
    onError: () => toast({ type: "error", message: "Re-analysis failed. Please try again." }),
  });

  const archiveMutation = useMutation({
    mutationFn: (archived) => emailApi.setArchived(emailId, archived),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      toast({ type: "success", message: "Email archived." });
      navigate("/inbox");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => emailApi.deleteEmail(emailId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      toast({ type: "success", message: "Email deleted." });
      navigate("/inbox");
    },
  });

  const markUnreadMutation = useMutation({
    mutationFn: () => emailApi.markAsRead(emailId, false),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["emails"] }),
  });

  const generateReplyMutation = useMutation({
    mutationFn: (options) => emailApi.generateReply(emailId, options),
    onSuccess: (data) => setReplyDrafts(data.drafts || []),
    onError: () => toast({ type: "error", message: "Couldn't generate a reply. Please try again." }),
  });

  const sendReplyMutation = useMutation({
    mutationFn: (payload) => emailApi.sendReply(emailId, payload),
    onSuccess: () => {
      toast({ type: "success", message: "Reply sent!" });
      queryClient.invalidateQueries({ queryKey: ["email", emailId] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
    onError: () => toast({ type: "error", message: "Failed to send reply. Please try again." }),
  });

  const confirmMeetingMutation = useMutation({
    mutationFn: (meetingId) => meetingApi.confirmMeeting(meetingId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email", emailId] }),
  });
  const declineMeetingMutation = useMutation({
    mutationFn: (meetingId) => meetingApi.declineMeeting(meetingId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email", emailId] }),
  });
  const completeTaskMutation = useMutation({
    mutationFn: (taskId) => taskApi.completeTask(taskId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email", emailId] }),
  });
  const dismissTaskMutation = useMutation({
    mutationFn: (taskId) => taskApi.dismissTask(taskId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email", emailId] }),
  });

  const email = emailQuery.data;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
      <div className="min-w-0 space-y-4">
        <EmailDetailHeader
          email={email}
          onArchive={() => archiveMutation.mutate(true)}
          onDelete={() => deleteMutation.mutate()}
          onMarkUnread={() => markUnreadMutation.mutate()}
          onToggleStar={() => {}}
        />

        <ThreadView messages={email?.thread || (email ? [email] : [])} isLoading={emailQuery.isLoading} />

        <ReplyComposer
          drafts={replyDrafts}
          isGenerating={generateReplyMutation.isPending}
          isSending={sendReplyMutation.isPending}
          onGenerate={(options) => generateReplyMutation.mutate(options)}
          onSend={(payload) => sendReplyMutation.mutate(payload)}
        />
      </div>

      <div className="space-y-4">
        <AISummaryPanel
          email={email}
          isLoading={emailQuery.isLoading}
          isReprocessing={reprocessMutation.isPending}
          onReprocess={() => reprocessMutation.mutate()}
        />
        <DetectedItemsPanel
          detectedMeetings={email?.detectedMeetings}
          detectedTasks={email?.detectedTasks}
          onConfirmMeeting={(id) => confirmMeetingMutation.mutate(id)}
          onDeclineMeeting={(id) => declineMeetingMutation.mutate(id)}
          onCompleteTask={(id) => completeTaskMutation.mutate(id)}
          onDismissTask={(id) => dismissTaskMutation.mutate(id)}
        />
      </div>
    </div>
  );
}