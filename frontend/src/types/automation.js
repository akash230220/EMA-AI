/**
 * @typedef {object} RuleCondition
 * @property {string} field - e.g. "category", "sender_domain"
 * @property {string} operator - e.g. "equals", "contains", "starts_with"
 * @property {string} value
 */

/**
 * @typedef {object} RuleAction
 * @property {"archive"|"delete"|"label"|"mark_read"|"forward"|"auto_reply"|"notify"} type
 * @property {string} [value] - e.g. label name, forward-to email
 */

/**
 * @typedef {object} AutomationRule
 * @property {string} id
 * @property {string} name
 * @property {string} [description]
 * @property {RuleCondition[]} conditions
 * @property {"AND"|"OR"} conditionLogic
 * @property {RuleAction[]} actions
 * @property {boolean} enabled
 * @property {number} priority - execution order
 * @property {string} createdAt - ISO datetime
 */

/**
 * @typedef {object} RuleFieldSchema
 * @property {string} field
 * @property {string} label
 * @property {string[]} operators
 * @property {"string"|"number"|"date"} valueType
 */

/**
 * @typedef {object} RuleActionSchema
 * @property {string} type
 * @property {string} label
 * @property {boolean} requiresValue
 */

/**
 * @typedef {object} RuleBuilderSchema
 * @property {RuleFieldSchema[]} conditionFields
 * @property {RuleActionSchema[]} actionTypes
 */

/**
 * @typedef {object} RuleTestResult
 * @property {number} matchedCount
 * @property {{id: string, subject: string, senderName: string}[]} sampleMatches
 */

/**
 * @typedef {object} RuleExecutionLog
 * @property {string} id
 * @property {string} emailSubject
 * @property {string} actionsPerformedLabel
 * @property {string} executedAtLabel
 * @property {boolean} success
 * @property {string} [errorMessage]
 */

export {};