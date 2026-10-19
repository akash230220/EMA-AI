/**
 * @typedef {"today"|"7d"|"30d"|"90d"} DateRange
 */

/**
 * @typedef {object} DashboardSummary
 * @property {number} totalEmails
 * @property {number} highPriorityEmails
 * @property {number} pendingReplies
 * @property {number} meetings
 * @property {number} tasks
 * @property {number} aiRepliesGenerated
 * @property {number} aiTimeSavedMinutes
 * @property {number} [avgResponseTimeMinutes]
 */

/**
 * @typedef {object} ActivityPoint
 * @property {string} date
 * @property {number} received
 * @property {number} replied
 */

/**
 * @typedef {object} MonthlyTrendPoint
 * @property {string} month
 * @property {number} totalEmails
 * @property {number} aiReplies
 * @property {number} timeSavedMinutes
 */

/**
 * @typedef {object} BreakdownEntry
 * @property {string} category - or priority/sentiment/intent, depending on endpoint
 * @property {number} count
 * @property {number} percentage
 */

/**
 * @typedef {object} ResponseTimeAnalytics
 * @property {number} averageResponseTimeMinutes
 * @property {{priority: string, avgMinutes: number}[]} byPriority
 * @property {{date: string, avgMinutes: number}[]} trend
 */

/**
 * @typedef {object} AiTimeSavedBreakdown
 * @property {number} totalMinutesSaved
 * @property {{activity: string, minutesSaved: number}[]} breakdown
 */

export {};