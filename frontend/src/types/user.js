/**
 * @typedef {object} User
 * @property {string} id
 * @property {string} name
 * @property {string} email
 * @property {string} [avatarUrl]
 * @property {string} [timezone] - IANA timezone, e.g. "Asia/Kolkata"
 * @property {string} createdAt - ISO datetime
 */

/**
 * @typedef {object} NotificationPreferences
 * @property {boolean} highPriorityEmail
 * @property {boolean} meetingDetected
 * @property {boolean} taskDetected
 * @property {boolean} dailyBrief
 * @property {boolean} automationFired
 * @property {boolean} weeklyDigest
 */

/**
 * @typedef {object} AiPreferences
 * @property {"formal"|"friendly"|"concise"} defaultReplyTone
 * @property {"short"|"medium"|"detailed"} summaryLength
 * @property {boolean} autoProcessNewEmails
 * @property {boolean} autoSyncConfirmedMeetings
 */

/**
 * @typedef {object} IntegrationStatus
 * @property {boolean} connected
 * @property {string} [email]
 * @property {string} [lastSyncedAtLabel]
 */

/**
 * @typedef {object} Session
 * @property {string} id
 * @property {string} deviceLabel
 * @property {"desktop"|"mobile"} deviceType
 * @property {string} location
 * @property {string} lastActiveLabel
 * @property {boolean} isCurrent
 */

export {};