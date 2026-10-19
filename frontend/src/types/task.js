/**
 * @typedef {"pending"|"in_progress"|"completed"|"dismissed"} TaskStatus
 */

/**
 * @typedef {"ai_extracted"|"manual"} TaskSource
 */

/**
 * @typedef {object} Task
 * @property {string} id
 * @property {string} title
 * @property {string} [description]
 * @property {string} [dueDate] - ISO date
 * @property {string} [dueDateLabel]
 * @property {"high"|"medium"|"low"} [priority]
 * @property {TaskStatus} status
 * @property {TaskSource} source
 * @property {string} [sourceEmailId]
 * @property {string} createdAt - ISO datetime
 */

/**
 * @typedef {object} TaskFilters
 * @property {number} [page]
 * @property {number} [pageSize]
 * @property {TaskStatus} [status]
 * @property {"high"|"medium"|"low"} [priority]
 * @property {TaskSource} [source]
 * @property {string} [emailId]
 * @property {string} [dueBefore] - ISO date
 * @property {"due_date"|"priority"|"created_at"} [sortBy]
 * @property {"asc"|"desc"} [sortOrder]
 */

/**
 * @typedef {object} TaskStats
 * @property {number} total
 * @property {number} pending
 * @property {number} completed
 * @property {number} overdue
 */

export {};