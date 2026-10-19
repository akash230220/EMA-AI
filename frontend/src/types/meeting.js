/**
 * @typedef {"detected"|"confirmed"|"declined"|"synced"} MeetingStatus
 */

/**
 * @typedef {"ai_detected"|"manual"} MeetingSource
 */

/**
 * @typedef {object} Meeting
 * @property {string} id
 * @property {string} title
 * @property {string} startTime - ISO datetime
 * @property {string} endTime - ISO datetime
 * @property {string} startTimeLabel
 * @property {string} endTimeLabel
 * @property {{month: string, day: string}} [dateShortLabel]
 * @property {string} [dateGroupLabel] - "Today" | "Tomorrow" | "Mon, Jan 15" etc.
 * @property {string} [location]
 * @property {string} [description]
 * @property {string[]} [attendees] - email addresses
 * @property {MeetingStatus} status
 * @property {MeetingSource} source
 * @property {string} [sourceEmailId]
 * @property {string} [calendarEventId]
 */

/**
 * @typedef {object} MeetingFilters
 * @property {number} [page]
 * @property {number} [pageSize]
 * @property {MeetingStatus} [status]
 * @property {MeetingSource} [source]
 * @property {string} [emailId]
 * @property {string} [fromDate] - ISO date
 * @property {string} [toDate] - ISO date
 * @property {"start_time"|"created_at"} [sortBy]
 * @property {"asc"|"desc"} [sortOrder]
 */

/**
 * @typedef {object} MeetingStats
 * @property {number} total
 * @property {number} pendingConfirmation
 * @property {number} syncedToCalendar
 */

export {};