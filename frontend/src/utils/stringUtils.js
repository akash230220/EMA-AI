/**
 * String manipulation helpers not already covered by
 * lib/formatters.js (which owns date/number/duration formatting).
 * This file owns general text transforms: casing, slugs, and
 * snake_case-to-label conversions used throughout badges/chips.
 */

/**
 * Converts a snake_case or SCREAMING_SNAKE string to a readable
 * label, e.g. "meeting_request" -> "Meeting request". Used for
 * intent/category/status badges across EmailListItem, TaskCard,
 * IntentBreakdownChart, ConditionRow, etc. (several of which
 * currently do this inline via .replace(/_/g, " ") — this is the
 * canonical version with proper capitalization).
 *
 * @param {string} value
 * @returns {string}
 */
export function snakeToLabel(value) {
  if (!value) return "";
  const spaced = String(value).toLowerCase().replace(/_/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

/**
 * Capitalizes just the first letter of a string, leaving the rest
 * untouched — lighter-weight than snakeToLabel when the string has
 * no underscores to convert (e.g. a plain "high"/"medium"/"low").
 *
 * @param {string} value
 * @returns {string}
 */
export function capitalize(value) {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

/**
 * Converts a string to a URL-safe slug, e.g. "Q3 Budget Review!" ->
 * "q3-budget-review" — could be used for shareable rule/task links
 * or export filenames.
 *
 * @param {string} value
 * @returns {string}
 */
export function slugify(value) {
  return String(value || "")
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/**
 * Pluralizes a simple English noun based on count, e.g.
 * pluralize(1, "email") -> "1 email", pluralize(5, "email") ->
 * "5 emails". Handles the common irregular case of words ending in
 * "y" (e.g. "reply" -> "replies").
 *
 * @param {number} count
 * @param {string} singular
 * @param {string} [plural]
 * @returns {string}
 */
export function pluralize(count, singular, plural) {
  if (count === 1) return `1 ${singular}`;
  if (plural) return `${count} ${plural}`;
  if (singular.endsWith("y") && !/[aeiou]y$/.test(singular)) {
    return `${count} ${singular.slice(0, -1)}ies`;
  }
  return `${count} ${singular}s`;
}

/**
 * Extracts a display name from an email address when no explicit
 * name is available, e.g. "jane.doe@company.com" -> "Jane Doe" —
 * a reasonable fallback for EmailListItem/ThreadView when
 * senderName is missing from the API response.
 *
 * @param {string} email
 * @returns {string}
 */
export function nameFromEmail(email) {
  if (!email) return "Unknown";
  const localPart = email.split("@")[0];
  return localPart
    .split(/[._-]+/)
    .filter(Boolean)
    .map(capitalize)
    .join(" ");
}

/**
 * Strips HTML tags from a string, leaving plain text — useful as a
 * defensive fallback when rendering an email snippet in a context
 * that must not contain markup (e.g. a browser notification body
 * or the Copilot source-citation tooltip), separate from the
 * intentional dangerouslySetInnerHTML rendering in ThreadView.
 *
 * @param {string} html
 * @returns {string}
 */
export function stripHtml(html) {
  if (!html) return "";
  return String(html).replace(/<[^>]*>/g, "").trim();
}