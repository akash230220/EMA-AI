// src/api/meetingApi.js
import axiosClient from "./axiosClient";

/**
 * Meeting API layer.
 *
 * Covers AI-detected meetings (from the Meeting Agent) as well as
 * Google Calendar event creation/sync. Pairs with backend endpoints
 * under /api/v1/meetings (see backend/app/api/v1/endpoints/meetings.py
 * and backend/app/integrations/calendar/calendar_client.py).
 */

const meetingApi = {
  /**
   * Fetches a paginated, filterable list of meetings.
   *
   * @param {object} params
   * @param {number} [params.page=1]
   * @param {number} [params.pageSize=20]
   * @param {string} [params.status] - "detected" | "confirmed" | "declined" | "synced"
   * @param {string} [params.source] - "ai_detected" | "manual"
   * @param {string} [params.emailId] - filter meetings linked to a specific email
   * @param {string} [params.fromDate] - ISO date string, lower bound
   * @param {string} [params.toDate] - ISO date string, upper bound
   * @param {string} [params.sortBy] - "start_time" | "created_at"
   * @param {string} [params.sortOrder] - "asc" | "desc"
   * @returns {Promise<{items: object[], total: number, page: number, pageSize: number}>}
   */
  getMeetings: async (params = {}) => {
    const { data } = await axiosClient.get("/meetings", { params });
    return data;
  },

  /**
   * Fetches a single meeting by ID, including its source email
   * reference (if AI-detected) and calendar sync status.
   * @param {string} meetingId
   * @returns {Promise<object>}
   */
  getMeetingById: async (meetingId) => {
    const { data } = await axiosClient.get(`/meetings/${meetingId}`);
    return data;
  },

  /**
   * Creates a new manual meeting (not derived from an email).
   *
   * @param {object} payload
   * @param {string} payload.title
   * @param {string} payload.startTime - ISO datetime string
   * @param {string} payload.endTime - ISO datetime string
   * @param {string} [payload.description]
   * @param {string} [payload.location]
   * @param {string[]} [payload.attendees] - list of email addresses
   * @returns {Promise<object>} created meeting
   */
  createMeeting: async (payload) => {
    const { data } = await axiosClient.post("/meetings", payload);
    return data;
  },

  /**
   * Updates an existing meeting's editable fields.
   *
   * @param {string} meetingId
   * @param {object} updates
   * @param {string} [updates.title]
   * @param {string} [updates.startTime]
   * @param {string} [updates.endTime]
   * @param {string} [updates.description]
   * @param {string} [updates.location]
   * @param {string[]} [updates.attendees]
   * @returns {Promise<object>} updated meeting
   */
  updateMeeting: async (meetingId, updates) => {
    const { data } = await axiosClient.patch(`/meetings/${meetingId}`, updates);
    return data;
  },

  /**
   * Confirms an AI-detected meeting suggestion, marking it accepted
   * by the user (does not yet push to Google Calendar — see syncToCalendar).
   * @param {string} meetingId
   * @returns {Promise<object>} updated meeting
   */
  confirmMeeting: async (meetingId) => {
    const { data } = await axiosClient.patch(`/meetings/${meetingId}/status`, { status: "confirmed" });
    return data;
  },

  /**
   * Declines/dismisses an AI-detected meeting suggestion
   * (e.g. a false positive from the Meeting Agent).
   * @param {string} meetingId
   * @returns {Promise<object>} updated meeting
   */
  declineMeeting: async (meetingId) => {
    const { data } = await axiosClient.patch(`/meetings/${meetingId}/status`, { status: "declined" });
    return data;
  },

  /**
   * Pushes a confirmed meeting to the user's Google Calendar via
   * the Calendar API integration. Backend creates the event and
   * stores the returned Google event ID for future updates/sync.
   * @param {string} meetingId
   * @returns {Promise<object>} updated meeting with calendar_event_id + status "synced"
   */
  syncToCalendar: async (meetingId) => {
    const { data } = await axiosClient.post(`/meetings/${meetingId}/sync-calendar`);
    return data;
  },

  /**
   * Removes a previously synced meeting from Google Calendar
   * (deletes the remote event, keeps the local record).
   * @param {string} meetingId
   * @returns {Promise<object>} updated meeting
   */
  unsyncFromCalendar: async (meetingId) => {
    const { data } = await axiosClient.delete(`/meetings/${meetingId}/sync-calendar`);
    return data;
  },

  /**
   * Permanently deletes a meeting record.
   * @param {string} meetingId
   * @returns {Promise<void>}
   */
  deleteMeeting: async (meetingId) => {
    await axiosClient.delete(`/meetings/${meetingId}`);
  },

  /**
   * Fetches upcoming meetings within a short horizon (e.g. next 7 days)
   * for the Dashboard's "Meetings" widget.
   * @param {{days?: number}} [options]
   * @returns {Promise<object[]>}
   */
  getUpcomingMeetings: async (options = {}) => {
    const { data } = await axiosClient.get("/meetings/upcoming", {
      params: { days: options.days ?? 7 },
    });
    return data;
  },

  /**
   * Fetches lightweight meeting summary stats for the Dashboard
   * (e.g. total this week, pending confirmations) without pulling
   * the full meeting list.
   * @returns {Promise<{total: number, pendingConfirmation: number, syncedToCalendar: number}>}
   */
  getMeetingStats: async () => {
    const { data } = await axiosClient.get("/meetings/stats");
    return data;
  },
};

export default meetingApi;