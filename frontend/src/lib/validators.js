/**
 * Lightweight, dependency-free form validation helpers. Kept simple
 * on purpose — none of the forms built so far (TaskFormDialog,
 * MeetingFormDialog, RuleBuilder, ProfileForm) need a full schema
 * library; a handful of pure functions covers all current cases.
 */

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * @param {string} email
 * @returns {boolean}
 */
export function isValidEmail(email) {
  return EMAIL_REGEX.test(String(email || "").trim());
}

/**
 * Validates a comma-separated list of email addresses (used by
 * MeetingFormDialog's attendees field). Returns which entries, if
 * any, are invalid.
 *
 * @param {string} commaSeparated
 * @returns {{valid: string[], invalid: string[]}}
 */
export function parseAndValidateEmailList(commaSeparated) {
  const entries = String(commaSeparated || "")
    .split(",")
    .map((e) => e.trim())
    .filter(Boolean);

  const valid = entries.filter(isValidEmail);
  const invalid = entries.filter((e) => !isValidEmail(e));
  return { valid, invalid };
}

/**
 * @param {string} value
 * @returns {boolean}
 */
export function isNonEmpty(value) {
  return Boolean(String(value || "").trim());
}

/**
 * Validates that endTime is strictly after startTime — used by
 * MeetingFormDialog before submit.
 *
 * @param {string} startIso
 * @param {string} endIso
 * @returns {boolean}
 */
export function isValidTimeRange(startIso, endIso) {
  if (!startIso || !endIso) return false;
  return new Date(endIso).getTime() > new Date(startIso).getTime();
}

/**
 * Validates an automation rule condition row has all required
 * fields filled — used by RuleBuilder's `isValid` check.
 *
 * @param {{field?: string, operator?: string, value?: string}} condition
 * @returns {boolean}
 */
export function isValidCondition(condition) {
  return Boolean(condition?.field && condition?.operator && String(condition?.value ?? "").trim());
}

/**
 * Validates an automation rule action row — action type is always
 * required; value is only required if the action's schema entry
 * says so (e.g. "label" needs a value, "archive" doesn't).
 *
 * @param {{type?: string, value?: string}} action
 * @param {{type: string, requiresValue: boolean}[]} actionSchema
 * @returns {boolean}
 */
export function isValidAction(action, actionSchema = []) {
  if (!action?.type) return false;
  const def = actionSchema.find((a) => a.type === action.type);
  if (def?.requiresValue) return isNonEmpty(action.value);
  return true;
}