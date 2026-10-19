/**
 * Date, time, and number formatting helpers. Centralizes logic that
 * several components assumed was pre-formatted on API responses
 * (e.g. `receivedAtLabel`, `dateShortLabel`, `startTimeLabel`) —
 * use these client-side if your backend returns raw ISO timestamps
 * instead of pre-labeled strings.
 */

/**
 * Formats an ISO date/datetime as a relative-friendly label:
 * "2:45 PM" for today, "Yesterday", "Mon", or "Jan 14" for older.
 * Mirrors Gmail's inbox list date column.
 *
 * @param {string} isoString
 * @returns {string}
 */
export function formatRelativeDate(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  const now = new Date();

  const isToday = date.toDateString() === now.toDateString();
  if (isToday) {
    return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  }

  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) {
    return "Yesterday";
  }

  const daysDiff = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  if (daysDiff < 7) {
    return date.toLocaleDateString(undefined, { weekday: "short" });
  }

  const sameYear = date.getFullYear() === now.getFullYear();
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: sameYear ? undefined : "numeric",
  });
}

/**
 * Formats an ISO datetime as a full readable timestamp, e.g.
 * "Mon, Jan 15, 2:30 PM" — used in ThreadView message headers.
 *
 * @param {string} isoString
 * @returns {string}
 */
export function formatFullDateTime(isoString) {
  if (!isoString) return "";
  return new Date(isoString).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/**
 * Formats just the time portion, e.g. "2:30 PM" — used for
 * meeting start/end times.
 *
 * @param {string} isoString
 * @returns {string}
 */
export function formatTime(isoString) {
  if (!isoString) return "";
  return new Date(isoString).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

/**
 * Returns a { month, day } short label for calendar-style date
 * chips, e.g. { month: "JAN", day: "15" } — used in MeetingCard.
 *
 * @param {string} isoString
 * @returns {{month: string, day: string}}
 */
export function formatShortDateParts(isoString) {
  if (!isoString) return { month: "", day: "" };
  const date = new Date(isoString);
  return {
    month: date.toLocaleDateString(undefined, { month: "short" }).toUpperCase(),
    day: String(date.getDate()),
  };
}

/**
 * Groups a date into a relative bucket label for list-sectioning,
 * e.g. "Today", "Tomorrow", or "Mon, Jan 15" — used by
 * MeetingList's date-grouping logic.
 *
 * @param {string} isoString
 * @returns {string}
 */
export function formatDateGroupLabel(isoString) {
  if (!isoString) return "Upcoming";
  const date = new Date(isoString);
  const now = new Date();

  const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDays = Math.round((startOfDay(date) - startOfDay(now)) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Tomorrow";
  if (diffDays === -1) return "Yesterday";

  return date.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

/**
 * Converts an ISO datetime string to the value format required by
 * <input type="datetime-local"> (local time, no timezone/seconds).
 * (Same helper previously inlined in MeetingFormDialog.jsx — moved
 * here as the canonical version.)
 *
 * @param {string} isoString
 * @returns {string}
 */
export function toDatetimeLocalValue(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}

/**
 * Formats a duration in minutes as a human-readable string,
 * e.g. 95 -> "1h 35m", 45 -> "45m" — used for AI time-saved metrics.
 *
 * @param {number} minutes
 * @returns {string}
 */
export function formatDuration(minutes) {
  if (!minutes || minutes < 1) return "0m";
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  if (hours === 0) return `${mins}m`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}m`;
}

/**
 * Formats a count with a compact suffix for large numbers,
 * e.g. 1250 -> "1.3k" — used for stat cards with potentially
 * large values (Total Emails, etc.).
 *
 * @param {number} value
 * @returns {string}
 */
export function formatCompactNumber(value) {
  if (value == null) return "0";
  return new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

/**
 * Truncates a string to a max length with an ellipsis, breaking on
 * a word boundary where possible — used for email snippets/subjects
 * in tight layout contexts (notification chips, source citations).
 *
 * @param {string} text
 * @param {number} [maxLength=80]
 * @returns {string}
 */
export function truncateText(text, maxLength = 80) {
  if (!text || text.length <= maxLength) return text || "";
  const truncated = text.slice(0, maxLength);
  const lastSpace = truncated.lastIndexOf(" ");
  return `${lastSpace > 0 ? truncated.slice(0, lastSpace) : truncated}…`;
}

/**
 * Returns initials (up to 2 characters) from a display name, for
 * Avatar fallbacks — used across Topbar, ProfileForm, EmailListItem,
 * ThreadView, ConversationSidebar, etc.
 *
 * @param {string} name
 * @returns {string}
 */
export function getInitials(name) {
  if (!name) return "?";
  return name
    .trim()
    .split(/\s+/)
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}