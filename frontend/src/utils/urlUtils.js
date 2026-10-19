/**
 * URL and query-string helpers — used for syncing filter state to
 * the URL (e.g. InboxPage reading ?search= on mount) and building
 * external links (mailto, Google Calendar "add event" fallback).
 */

/**
 * Builds a query string from a params object, omitting
 * undefined/null/empty values. Thin wrapper around URLSearchParams
 * that matches the same "skip empties" behavior as
 * objectUtils.omitEmpty, since axios/fetch don't do this
 * automatically.
 *
 * @param {object} params
 * @returns {string} query string including leading "?", or "" if empty
 */
export function buildQueryString(params) {
  const filtered = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== ""
  );
  if (filtered.length === 0) return "";
  const search = new URLSearchParams(filtered.map(([k, v]) => [k, String(v)]));
  return `?${search.toString()}`;
}

/**
 * Parses the current URL's query string into a plain object —
 * lighter-weight alternative to useSearchParams() for one-off reads
 * outside a component (e.g. utility functions, non-hook contexts).
 *
 * @param {string} [search] - defaults to window.location.search
 * @returns {Record<string, string>}
 */
export function parseQueryString(search = window.location.search) {
  return Object.fromEntries(new URLSearchParams(search).entries());
}

/**
 * Builds a mailto: link for quickly composing an email outside the
 * app (e.g. a "contact support" link in Settings), with proper
 * encoding of subject/body.
 *
 * @param {object} options
 * @param {string} options.to
 * @param {string} [options.subject]
 * @param {string} [options.body]
 * @returns {string}
 */
export function buildMailtoLink({ to, subject, body }) {
  const params = buildQueryString({ subject, body });
  return `mailto:${to}${params}`;
}

/**
 * Checks whether a string is a well-formed absolute URL — used
 * before rendering user-controlled links (e.g. an automation rule's
 * "forward" action value, or a meeting location that might be a
 * video-call URL) to avoid crashing on `new URL()` elsewhere.
 *
 * @param {string} value
 * @returns {boolean}
 */
export function isValidUrl(value) {
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
}