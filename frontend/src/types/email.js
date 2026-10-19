/**
 * @typedef {"high"|"medium"|"low"} Priority
 */

/**
 * @typedef {"positive"|"neutral"|"negative"} Sentiment
 */

/**
 * @typedef {"meeting_request"|"task"|"fyi"|"follow_up"|"urgent_action"|"question"} Intent
 */

/**
 * @typedef {"work"|"finance"|"personal"|"newsletters"|"promotions"|"social"} EmailCategory
 */

/**
 * @typedef {object} EmailAttachment
 * @property {string} id
 * @property {string} filename
 * @property {string} downloadUrl
 * @property {number} [sizeBytes]
 */

/**
 * @typedef {object} EmailListItem
 * @property {string} id
 * @property {string} senderName
 * @property {string} senderEmail
 * @property {string} subject
 * @property {string} snippet
 * @property {string} [aiSummary]
 * @property {boolean} isRead
 * @property {boolean} isStarred
 * @property {boolean} hasAttachment
 * @property {boolean} hasMeeting
 * @property {boolean} hasTask
 * @property {boolean} [pendingReply]
 * @property {Priority} [priority]
 * @property {EmailCategory} [category]
 * @property {Intent} [intent]
 * @property {Sentiment} [sentiment]
 * @property {string} receivedAtLabel - pre-formatted display label (see lib/formatters.js)
 * @property {string} receivedAt - ISO datetime
 */

/**
 * @typedef {object} ThreadMessage
 * @property {string} id
 * @property {string} senderName
 * @property {string} senderEmail
 * @property {string} [recipientsLabel]
 * @property {string} snippet
 * @property {string} [bodyHtml]
 * @property {string} [bodyText]
 * @property {string} sentAtLabel
 * @property {string} sentAt - ISO datetime
 * @property {EmailAttachment[]} [attachments]
 */

/**
 * @typedef {object} DetectedMeetingRef
 * @property {string} id
 * @property {string} title
 * @property {string} startTimeLabel
 * @property {string} [location]
 * @property {"detected"|"confirmed"|"declined"|"synced"} status
 */

/**
 * @typedef {object} DetectedTaskRef
 * @property {string} id
 * @property {string} title
 * @property {string} [dueDateLabel]
 * @property {"pending"|"in_progress"|"completed"|"dismissed"} status
 */

/**
 * @typedef {EmailListItem & object} EmailDetail
 * @property {ThreadMessage[]} thread
 * @property {string} [aiSummary]
 * @property {string[]} [aiKeyPoints]
 * @property {DetectedMeetingRef[]} [detectedMeetings]
 * @property {DetectedTaskRef[]} [detectedTasks]
 */

/**
 * @typedef {object} ReplyDraft
 * @property {string} id
 * @property {"formal"|"friendly"|"concise"} tone
 * @property {string} body
 */

/**
 * @typedef {object} EmailFilters
 * @property {number} [page]
 * @property {number} [pageSize]
 * @property {EmailCategory} [category]
 * @property {Priority} [priority]
 * @property {Intent} [intent]
 * @property {Sentiment} [sentiment]
 * @property {boolean} [unreadOnly]
 * @property {boolean} [pendingReplyOnly]
 * @property {string} [search]
 * @property {"date"|"priority"} [sortBy]
 * @property {"asc"|"desc"} [sortOrder]
 */

/**
 * @typedef {object} PaginatedEmails
 * @property {EmailListItem[]} items
 * @property {number} total
 * @property {number} page
 * @property {number} pageSize
 */

/**
 * @typedef {object} SemanticSearchResult
 * @property {string} email_id
 * @property {string} snippet
 * @property {number} score
 */

export {};