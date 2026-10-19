// src/api/analyticsApi.js
import axiosClient from "./axiosClient";

/**
 * Analytics API layer.
 *
 * Powers the Dashboard metrics and the dedicated Analytics page:
 * volume trends, priority/category/sentiment breakdowns, response
 * time analytics, and AI time-saved estimates. Pairs with backend
 * endpoints under /api/v1/analytics (see
 * backend/app/api/v1/endpoints/analytics.py and
 * backend/app/ai/agents/analytics_agent.py).
 */

const analyticsApi = {
  /**
   * Fetches the core Dashboard summary metrics in a single call:
   * total emails, high priority count, pending replies, meetings,
   * tasks, AI replies generated, AI time saved.
   *
   * @param {{range?: "today"|"7d"|"30d"|"90d"}} [params]
   * @returns {Promise<{
   *   totalEmails: number,
   *   highPriorityEmails: number,
   *   pendingReplies: number,
   *   meetings: number,
   *   tasks: number,
   *   aiRepliesGenerated: number,
   *   aiTimeSavedMinutes: number
   * }>}
   */
  getDashboardSummary: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/summary", { params });
    return data;
  },

  /**
   * Fetches weekly activity data (email volume by day) for the
   * Dashboard's weekly activity chart.
   *
   * @param {{weeks?: number}} [params] - how many past weeks to include
   * @returns {Promise<{date: string, received: number, replied: number}[]>}
   */
  getWeeklyActivity: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/weekly-activity", { params });
    return data;
  },

  /**
   * Fetches monthly trend data for longer-range charts
   * (e.g. email volume, AI replies, time saved over months).
   *
   * @param {{months?: number}} [params]
   * @returns {Promise<{month: string, totalEmails: number, aiReplies: number, timeSavedMinutes: number}[]>}
   */
  getMonthlyTrends: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/monthly-trends", { params });
    return data;
  },

  /**
   * Fetches response time analytics — how quickly the user (or AI-assisted
   * replies) responds to emails, bucketed by priority/category.
   *
   * @param {{range?: "7d"|"30d"|"90d"}} [params]
   * @returns {Promise<{
   *   averageResponseTimeMinutes: number,
   *   byPriority: {priority: string, avgMinutes: number}[],
   *   trend: {date: string, avgMinutes: number}[]
   * }>}
   */
  getResponseTimeAnalytics: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/response-time", { params });
    return data;
  },

  /**
   * Fetches the breakdown of emails by AI-assigned category
   * (e.g. work, finance, personal, newsletters) for pie/bar charts.
   *
   * @param {{range?: "7d"|"30d"|"90d"}} [params]
   * @returns {Promise<{category: string, count: number, percentage: number}[]>}
   */
  getCategoryBreakdown: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/category-breakdown", { params });
    return data;
  },

  /**
   * Fetches the breakdown of emails by AI-assigned priority level.
   *
   * @param {{range?: "7d"|"30d"|"90d"}} [params]
   * @returns {Promise<{priority: string, count: number, percentage: number}[]>}
   */
  getPriorityBreakdown: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/priority-breakdown", { params });
    return data;
  },

  /**
   * Fetches the breakdown of emails by AI-assigned sentiment
   * (positive/neutral/negative) for trend visualization.
   *
   * @param {{range?: "7d"|"30d"|"90d"}} [params]
   * @returns {Promise<{sentiment: string, count: number, percentage: number}[]>}
   */
  getSentimentBreakdown: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/sentiment-breakdown", { params });
    return data;
  },

  /**
   * Fetches intent distribution (e.g. meeting_request, task, fyi,
   * follow_up, urgent_action) for the Intent Detection insight chart.
   *
   * @param {{range?: "7d"|"30d"|"90d"}} [params]
   * @returns {Promise<{intent: string, count: number, percentage: number}[]>}
   */
  getIntentBreakdown: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/intent-breakdown", { params });
    return data;
  },

  /**
   * Fetches AI time-saved estimate details — how the total minutes
   * saved figure breaks down (auto-replies, summaries, categorization
   * time avoided, etc.) for a transparency panel.
   *
   * @param {{range?: "7d"|"30d"|"90d"}} [params]
   * @returns {Promise<{
   *   totalMinutesSaved: number,
   *   breakdown: {activity: string, minutesSaved: number}[]
   * }>}
   */
  getAiTimeSavedBreakdown: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/ai-time-saved", { params });
    return data;
  },

  /**
   * Exports analytics data as a downloadable file (CSV/PDF report).
   *
   * @param {{range?: "7d"|"30d"|"90d", format?: "csv"|"pdf"}} [params]
   * @returns {Promise<Blob>}
   */
  exportAnalyticsReport: async (params = {}) => {
    const { data } = await axiosClient.get("/analytics/export", {
      params,
      responseType: "blob",
    });
    return data;
  },
};

export default analyticsApi;