// src/api/emailApi.js
import axiosClient from "./axiosClient";

/**
 * Email API layer.
 *
 * Covers inbox sync, listing/filtering emails, single-email detail,
 * AI-generated insights (summary/categorization/priority/sentiment),
 * semantic/RAG search, and AI reply generation.
 *
 * Pairs with backend endpoints under /api/v1 (see
 * backend/app/api/v1/endpoints/inbox.py, emails.py, reply.py).
 */

const emailApi = {
  // ---------------------------------------------------------------------
  // Inbox sync
  // ---------------------------------------------------------------------

  /**
   * Triggers a Gmail inbox sync for the current user.
   * Backend fetches new messages via Gmail API and runs them
   * through the LangGraph multi-agent pipeline.
   *
   * @param {{full?: boolean}} options - full=true forces a complete re-sync
   * @returns {Promise<{synced_count: number, last_synced_at: string}>}
   */
  syncInbox: async (options = {}) => {
    const { data } = await axiosClient.post("/inbox/sync", options);
    return data;
  },

  /**
   * Gets the current sync status (useful for polling a "Syncing..." UI state).
   * @returns {Promise<{status: "idle"|"syncing"|"error", last_synced_at: string|null}>}
   */
  getSyncStatus: async () => {
    const { data } = await axiosClient.get("/inbox/sync/status");
    return data;
  },

  // ---------------------------------------------------------------------
  // Listing & filtering
  // ---------------------------------------------------------------------

  /**
   * Fetches a paginated, filterable list of emails.
   *
   * @param {object} params
   * @param {number} [params.page=1]
   * @param {number} [params.pageSize=20]
   * @param {string} [params.category] - e.g. "work", "finance", "personal"
   * @param {string} [params.priority] - "high" | "medium" | "low"
   * @param {string} [params.intent] - e.g. "meeting_request", "task", "fyi"
   * @param {string} [params.sentiment] - "positive" | "neutral" | "negative"
   * @param {boolean} [params.unreadOnly]
   * @param {boolean} [params.pendingReplyOnly]
   * @param {string} [params.search] - free-text search over subject/sender/body
   * @param {string} [params.sortBy] - "date" | "priority"
   * @param {string} [params.sortOrder] - "asc" | "desc"
   * @returns {Promise<{items: object[], total: number, page: number, pageSize: number}>}
   */
  getEmails: async (params = {}) => {
    const { data } = await axiosClient.get("/emails", { params });
    return data;
  },

  /**
   * Fetches a single email (full thread) by ID, including AI-derived fields.
   * @param {string} emailId
   * @returns {Promise<object>}
   */
  getEmailById: async (emailId) => {
    const { data } = await axiosClient.get(`/emails/${emailId}`);
    return data;
  },

  /**
   * Marks an email as read/unread.
   * @param {string} emailId
   * @param {boolean} isRead
   * @returns {Promise<object>}
   */
  markAsRead: async (emailId, isRead = true) => {
    const { data } = await axiosClient.patch(`/emails/${emailId}/read`, { is_read: isRead });
    return data;
  },

  /**
   * Archives or unarchives an email.
   * @param {string} emailId
   * @param {boolean} archived
   * @returns {Promise<object>}
   */
  setArchived: async (emailId, archived = true) => {
    const { data } = await axiosClient.patch(`/emails/${emailId}/archive`, { archived });
    return data;
  },

  /**
   * Deletes (soft-delete) an email from the app's view.
   * @param {string} emailId
   * @returns {Promise<void>}
   */
  deleteEmail: async (emailId) => {
    await axiosClient.delete(`/emails/${emailId}`);
  },

  // ---------------------------------------------------------------------
  // AI insights (on-demand re-run, if user wants a fresh pass)
  // ---------------------------------------------------------------------

  /**
   * Re-runs the full AI agent pipeline (categorization, intent, priority,
   * sentiment, summarization, task/meeting extraction) on a single email.
   * @param {string} emailId
   * @returns {Promise<object>} updated email with refreshed AI fields
   */
  reprocessEmail: async (emailId) => {
    const { data } = await axiosClient.post(`/emails/${emailId}/reprocess`);
    return data;
  },

  /**
   * Fetches just the AI summary for an email (fast path, no full reprocess).
   * @param {string} emailId
   * @returns {Promise<{summary: string}>}
   */
  getSummary: async (emailId) => {
    const { data } = await axiosClient.get(`/emails/${emailId}/summary`);
    return data;
  },

  // ---------------------------------------------------------------------
  // AI Reply generation
  // ---------------------------------------------------------------------

  /**
   * Generates one or more AI-drafted reply options for an email.
   * @param {string} emailId
   * @param {object} [options]
   * @param {string} [options.tone] - "formal" | "friendly" | "concise"
   * @param {string} [options.instructions] - free-text guidance from user
   * @returns {Promise<{drafts: {id: string, tone: string, body: string}[]}>}
   */
  generateReply: async (emailId, options = {}) => {
    const { data } = await axiosClient.post(`/emails/${emailId}/reply/generate`, options);
    return data;
  },

  /**
   * Sends a reply (either an edited AI draft or a fully manual message).
   * @param {string} emailId
   * @param {{body: string, draftId?: string}} payload
   * @returns {Promise<object>}
   */
  sendReply: async (emailId, payload) => {
    const { data } = await axiosClient.post(`/emails/${emailId}/reply/send`, payload);
    return data;
  },

  // ---------------------------------------------------------------------
  // Semantic / RAG search across historical emails
  // ---------------------------------------------------------------------

  /**
   * Runs a semantic search query against the ChromaDB-backed RAG index.
   * @param {string} query
   * @param {{limit?: number}} [options]
   * @returns {Promise<{results: {email_id: string, snippet: string, score: number}[]}>}
   */
  semanticSearch: async (query, options = {}) => {
    const { data } = await axiosClient.post("/emails/search/semantic", {
      query,
      limit: options.limit ?? 10,
    });
    return data;
  },

  // ---------------------------------------------------------------------
  // Bulk actions
  // ---------------------------------------------------------------------

  /**
   * Applies a bulk action (archive/delete/mark-read) to multiple emails at once.
   * @param {string[]} emailIds
   * @param {"archive"|"delete"|"mark_read"|"mark_unread"} action
   * @returns {Promise<{affected: number}>}
   */
  bulkAction: async (emailIds, action) => {
    const { data } = await axiosClient.post("/emails/bulk", {
      email_ids: emailIds,
      action,
    });
    return data;
  },
};

export default emailApi;