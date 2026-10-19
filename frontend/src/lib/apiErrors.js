/**
 * Helpers for working with the normalized error shape produced by
 * axiosClient.js's response interceptor:
 *   { message: string, status: number|null, errors: object|null, original: any }
 *
 * Used to keep toast/error-display logic in hooks and pages from
 * repeating the same `error?.message || "fallback"` pattern.
 */

const DEFAULT_ERROR_MESSAGE = "Something went wrong. Please try again.";

/**
 * Safely extracts a user-facing message from any thrown value —
 * axiosClient's normalized error, a raw Error, or a plain string.
 *
 * @param {*} error
 * @param {string} [fallback]
 * @returns {string}
 */
export function getErrorMessage(error, fallback = DEFAULT_ERROR_MESSAGE) {
  if (!error) return fallback;
  if (typeof error === "string") return error;
  if (error.message) return error.message;
  return fallback;
}

/**
 * Checks whether an error represents an auth failure (401) — useful
 * in edge cases outside axiosClient's own interceptor (e.g. the raw
 * fetch() call in copilotApi.streamMessage, which bypasses axios).
 *
 * @param {*} error
 * @returns {boolean}
 */
export function isAuthError(error) {
  return error?.status === 401;
}

/**
 * Checks whether an error represents a network failure (no response
 * received at all, e.g. offline / DNS failure) vs. a server-returned
 * error status.
 *
 * @param {*} error
 * @returns {boolean}
 */
export function isNetworkError(error) {
  return error?.status === null || error?.status === undefined;
}

/**
 * Extracts field-level validation errors, if present, e.g. for
 * mapping backend 422 responses to specific form fields.
 * Returns null if the error has no field-level detail.
 *
 * @param {*} error
 * @returns {object|null}
 */
export function getFieldErrors(error) {
  return error?.errors && typeof error.errors === "object" ? error.errors : null;
}