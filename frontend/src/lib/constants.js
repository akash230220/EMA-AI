/**
 * Centralized enum-like constants and their display config
 * (labels, colors, badge variants). Several components built
 * earlier (StatCard, EmailListItem, TaskCard, MeetingCard,
 * PriorityBreakdownChart, ResponseTimeChart, etc.) each redefined
 * their own PRIORITY_VARIANT / PRIORITY_COLORS map inline — this
 * file is the single source of truth going forward. Existing
 * inline maps still work as-is; consider migrating them here
 * during a cleanup pass.
 */

// ---------------------------------------------------------------------
// Priority
// ---------------------------------------------------------------------
export const PRIORITY = {
  HIGH: "high",
  MEDIUM: "medium",
  LOW: "low",
};

export const PRIORITY_CONFIG = {
  [PRIORITY.HIGH]: { label: "High", badgeVariant: "destructive", hex: "#EF4444" },
  [PRIORITY.MEDIUM]: { label: "Medium", badgeVariant: "warning", hex: "#F59E0B" },
  [PRIORITY.LOW]: { label: "Low", badgeVariant: "success", hex: "#10B981" },
};

// ---------------------------------------------------------------------
// Sentiment
// ---------------------------------------------------------------------
export const SENTIMENT = {
  POSITIVE: "positive",
  NEUTRAL: "neutral",
  NEGATIVE: "negative",
};

export const SENTIMENT_CONFIG = {
  [SENTIMENT.POSITIVE]: { label: "Positive", hex: "#10B981", dotClass: "bg-emerald-500" },
  [SENTIMENT.NEUTRAL]: { label: "Neutral", hex: "#9CA3AF", dotClass: "bg-gray-400" },
  [SENTIMENT.NEGATIVE]: { label: "Negative", hex: "#EF4444", dotClass: "bg-red-500" },
};

// ---------------------------------------------------------------------
// Intent
// ---------------------------------------------------------------------
export const INTENT = {
  MEETING_REQUEST: "meeting_request",
  TASK: "task",
  FYI: "fyi",
  FOLLOW_UP: "follow_up",
  URGENT_ACTION: "urgent_action",
  QUESTION: "question",
};

export const INTENT_CONFIG = {
  [INTENT.MEETING_REQUEST]: { label: "Meeting request", hex: "#4F46E5" },
  [INTENT.TASK]: { label: "Task", hex: "#7C3AED" },
  [INTENT.FYI]: { label: "FYI", hex: "#9CA3AF" },
  [INTENT.FOLLOW_UP]: { label: "Follow up", hex: "#F59E0B" },
  [INTENT.URGENT_ACTION]: { label: "Urgent action", hex: "#EF4444" },
  [INTENT.QUESTION]: { label: "Question", hex: "#06B6D4" },
};

// ---------------------------------------------------------------------
// Email category
// ---------------------------------------------------------------------
export const EMAIL_CATEGORY = {
  WORK: "work",
  FINANCE: "finance",
  PERSONAL: "personal",
  NEWSLETTERS: "newsletters",
  PROMOTIONS: "promotions",
  SOCIAL: "social",
};

export const CATEGORY_CHART_COLORS = [
  "#4F46E5", "#7C3AED", "#EC4899", "#F59E0B", "#10B981", "#06B6D4", "#8B5CF6",
];

// ---------------------------------------------------------------------
// Task status
// ---------------------------------------------------------------------
export const TASK_STATUS = {
  PENDING: "pending",
  IN_PROGRESS: "in_progress",
  COMPLETED: "completed",
  DISMISSED: "dismissed",
};

export const TASK_STATUS_CONFIG = {
  [TASK_STATUS.PENDING]: { label: "Pending", dotClass: "bg-gray-400" },
  [TASK_STATUS.IN_PROGRESS]: { label: "In Progress", dotClass: "bg-amber-500" },
  [TASK_STATUS.COMPLETED]: { label: "Completed", dotClass: "bg-emerald-500" },
  [TASK_STATUS.DISMISSED]: { label: "Dismissed", dotClass: "bg-gray-300" },
};

// ---------------------------------------------------------------------
// Meeting status
// ---------------------------------------------------------------------
export const MEETING_STATUS = {
  DETECTED: "detected",
  CONFIRMED: "confirmed",
  DECLINED: "declined",
  SYNCED: "synced",
};

export const MEETING_STATUS_CONFIG = {
  [MEETING_STATUS.DETECTED]: { label: "Needs review", badgeVariant: "warning" },
  [MEETING_STATUS.CONFIRMED]: { label: "Confirmed", badgeVariant: "secondary" },
  [MEETING_STATUS.DECLINED]: { label: "Declined", badgeVariant: "outline" },
  [MEETING_STATUS.SYNCED]: { label: "Synced to Calendar", badgeVariant: "success" },
};

// ---------------------------------------------------------------------
// Source (AI-detected vs. manual — shared by tasks & meetings)
// ---------------------------------------------------------------------
export const SOURCE = {
  AI_EXTRACTED: "ai_extracted",
  AI_DETECTED: "ai_detected",
  MANUAL: "manual",
};

// ---------------------------------------------------------------------
// Reply tone
// ---------------------------------------------------------------------
export const REPLY_TONE = {
  FORMAL: "formal",
  FRIENDLY: "friendly",
  CONCISE: "concise",
};

export const REPLY_TONE_OPTIONS = [
  { value: REPLY_TONE.FORMAL, label: "Formal" },
  { value: REPLY_TONE.FRIENDLY, label: "Friendly" },
  { value: REPLY_TONE.CONCISE, label: "Concise" },
];

// ---------------------------------------------------------------------
// Analytics date ranges
// ---------------------------------------------------------------------
export const DATE_RANGE_OPTIONS = [
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "90d", label: "Last 90 days" },
];

// ---------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------
export const DEFAULT_PAGE_SIZE = 20;

// ---------------------------------------------------------------------
// LocalStorage keys (single source of truth, avoids typo drift
// between AppShell.jsx, useUIStore.js, axiosClient.js, etc.)
// ---------------------------------------------------------------------
export const STORAGE_KEYS = {
  ACCESS_TOKEN: "ai_email_os_access_token",
  SIDEBAR_COLLAPSED: "ai_email_os_sidebar_collapsed",
  THEME: "ai_email_os_theme",
  UI_STORE: "ai_email_os_ui_store",
};