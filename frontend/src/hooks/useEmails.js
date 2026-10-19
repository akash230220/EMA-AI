import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import emailApi from "@/api/emailApi";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Fetches a paginated, filtered list of emails.
 * @param {object} filters - see emailApi.getEmails params
 * @param {object} [options] - additional React Query options (e.g. enabled)
 */
export function useEmails(filters = {}, options = {}) {
  return useQuery({
    queryKey: ["emails", filters],
    queryFn: () => emailApi.getEmails(filters),
    keepPreviousData: true,
    ...options,
  });
}

/**
 * Fetches a single email by ID.
 * @param {string} emailId
 */
export function useEmail(emailId) {
  return useQuery({
    queryKey: ["email", emailId],
    queryFn: () => emailApi.getEmailById(emailId),
    enabled: Boolean(emailId),
  });
}

/**
 * Triggers a Gmail inbox sync and invalidates every query whose
 * data could change as a result (emails, dashboard, tasks, meetings).
 */
export function useSyncInbox() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (options) => emailApi.syncInbox(options),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      toast({ type: "success", message: `Synced ${data.synced_count} new email(s).` });
    },
    onError: () => toast({ type: "error", message: "Inbox sync failed. Please try again." }),
  });
}

/**
 * Marks a single email as read/unread with an optimistic cache
 * update against the currently-active email list queries.
 */
export function useMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ emailId, isRead }) => emailApi.markAsRead(emailId, isRead),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}

/**
 * Archives/unarchives a single email.
 */
export function useArchiveEmail() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ emailId, archived }) => emailApi.setArchived(emailId, archived),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      toast({ type: "success", message: "Email archived." });
    },
    onError: () => toast({ type: "error", message: "Couldn't archive that email." }),
  });
}

/**
 * Deletes a single email.
 */
export function useDeleteEmail() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (emailId) => emailApi.deleteEmail(emailId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      toast({ type: "success", message: "Email deleted." });
    },
    onError: () => toast({ type: "error", message: "Couldn't delete that email." }),
  });
}

/**
 * Applies a bulk action (archive/delete/mark_read/mark_unread) to
 * multiple emails at once — powers the Inbox multi-select toolbar.
 */
export function useBulkEmailAction() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ action, ids }) => emailApi.bulkAction(ids, action),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      toast({ type: "success", message: `${variables.ids.length} email(s) updated.` });
    },
    onError: () => toast({ type: "error", message: "Bulk action failed. Please try again." }),
  });
}

/**
 * Re-runs the full AI agent pipeline on a single email (categorization,
 * intent, priority, sentiment, summarization, extraction).
 */
export function useReprocessEmail(emailId) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: () => emailApi.reprocessEmail(emailId),
    onSuccess: (data) => {
      queryClient.setQueryData(["email", emailId], data);
      toast({ type: "success", message: "Email re-analyzed." });
    },
    onError: () => toast({ type: "error", message: "Re-analysis failed. Please try again." }),
  });
}

/**
 * Generates AI reply draft(s) for a given email.
 */
export function useGenerateReply(emailId) {
  const { toast } = useToast();

  return useMutation({
    mutationFn: (options) => emailApi.generateReply(emailId, options),
    onError: () => toast({ type: "error", message: "Couldn't generate a reply. Please try again." }),
  });
}

/**
 * Sends a reply (AI draft, edited draft, or fully manual) for a
 * given email.
 */
export function useSendReply(emailId) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (payload) => emailApi.sendReply(emailId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email", emailId] });
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      toast({ type: "success", message: "Reply sent!" });
    },
    onError: () => toast({ type: "error", message: "Failed to send reply. Please try again." }),
  });
}

/**
 * Runs a semantic/RAG search across historical emails.
 * @param {string} query
 * @param {object} [options]
 */
export function useSemanticSearch(query, options = {}) {
  return useQuery({
    queryKey: ["semantic-search", query],
    queryFn: () => emailApi.semanticSearch(query),
    enabled: Boolean(query?.trim()),
    ...options,
  });
}