/**
 * Centralized React Query key factories. Every hook in hooks/
 * (useEmails, useTasks, useMeetings, useAnalytics, useAutomation,
 * useCopilot) currently constructs its query keys inline as plain
 * arrays like ["emails", filters] — functionally fine, but scattered.
 *
 * This file is an OPTIONAL consolidation layer: adopting it means
 * every invalidateQueries() call and every useQuery() call reference
 * the same factory function, eliminating a class of bugs where an
 * invalidation call's key shape drifts from the query's actual key
 * (e.g. forgetting a filters param, breaking cache invalidation
 * silently). Existing inline array keys continue to work
 * side-by-side; migrate incrementally.
 *
 * Usage:
 *   useQuery({ queryKey: queryKeys.emails.list(filters), ... })
 *   queryClient.invalidateQueries({ queryKey: queryKeys.emails.all })
 */
export const queryKeys = {
  emails: {
    all: ["emails"],
    list: (filters) => ["emails", filters],
    detail: (id) => ["email", id],
    semanticSearch: (query) => ["semantic-search", query],
  },
  tasks: {
    all: ["tasks"],
    list: (filters) => ["tasks", filters],
    detail: (id) => ["task", id],
    stats: ["task-stats"],
  },
  meetings: {
    all: ["meetings"],
    list: (filters) => ["meetings", filters],
    detail: (id) => ["meeting", id],
    upcoming: (days) => ["meetings", "upcoming", days],
    stats: ["meeting-stats"],
  },
  analytics: {
    summary: (range) => ["analytics", "summary", range],
    weeklyActivity: (range) => ["analytics", "weekly-activity", range],
    monthlyTrends: (months) => ["monthly-trends", months],
    categoryBreakdown: (range) => ["analytics", "category-breakdown", range],
    priorityBreakdown: (range) => ["analytics", "priority-breakdown", range],
    sentimentBreakdown: (range) => ["analytics", "sentiment-breakdown", range],
    intentBreakdown: (range) => ["analytics", "intent-breakdown", range],
    responseTime: (range) => ["analytics", "response-time", range],
    aiTimeSaved: (range) => ["analytics", "ai-time-saved", range],
    dashboardSummary: ["dashboard-summary"],
  },
  automation: {
    all: ["automation-rules"],
    list: (params) => ["automation-rules", params],
    schema: ["automation-schema"],
    logs: (ruleId, params) => ["automation-logs", ruleId, params],
  },
  copilot: {
    conversations: (params) => ["copilot-conversations", params],
    conversation: (id) => ["copilot-conversation", id],
  },
  settings: {
    all: ["settings"],
  },
};