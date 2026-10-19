/**
 * @typedef {object} CopilotToolCall
 * @property {string} name
 * @property {string} [label] - human-readable description shown as a chip
 * @property {object} [input]
 */

/**
 * @typedef {object} CopilotSource
 * @property {string} email_id
 * @property {string} snippet
 * @property {number} score
 */

/**
 * @typedef {object} CopilotMessage
 * @property {string} id
 * @property {"user"|"assistant"} role
 * @property {string} content
 * @property {CopilotToolCall[]} [toolCalls]
 * @property {CopilotSource[]} [sources]
 * @property {"up"|"down"} [feedback]
 */

/**
 * @typedef {object} CopilotConversation
 * @property {string} id
 * @property {string} title
 * @property {string} lastMessageAt - ISO datetime
 * @property {CopilotMessage[]} [messages]
 */

/**
 * @typedef {object} CopilotStreamEvent
 * @property {"conversation_id"|"token"|"tool_call"|"sources"} type
 * @property {string} [conversationId]
 * @property {string} [content] - present when type === "token"
 * @property {CopilotToolCall} [toolCall] - present when type === "tool_call"
 * @property {CopilotSource[]} [sources] - present when type === "sources"
 */

export {};