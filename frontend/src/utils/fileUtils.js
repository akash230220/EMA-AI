/**
 * File-handling helpers — used for attachment display (ThreadView)
 * and triggering browser downloads (AnalyticsPage's CSV/PDF export,
 * already used inline there; this is the reusable version).
 */

/**
 * Formats a byte count as a human-readable file size string, e.g.
 * 1536000 -> "1.5 MB" — used for EmailAttachment display in
 * ThreadView (currently attachments only show filename; this
 * supports adding a size label).
 *
 * @param {number} bytes
 * @returns {string}
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes < 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, exponent);
  return `${exponent === 0 ? value : value.toFixed(1)} ${units[exponent]}`;
}

/**
 * Extracts a file extension from a filename (lowercase, no dot),
 * e.g. "invoice.PDF" -> "pdf" — useful for choosing an attachment
 * icon by type in a richer ThreadView attachment chip.
 *
 * @param {string} filename
 * @returns {string}
 */
export function getFileExtension(filename) {
  if (!filename || !filename.includes(".")) return "";
  return filename.split(".").pop().toLowerCase();
}

/**
 * Triggers a browser download for a Blob with a given filename.
 * Extracted from the inline logic in AnalyticsPage.jsx's
 * exportMutation.onSuccess handler so it's reusable anywhere else
 * a file-download action is needed (e.g. exporting a single email
 * thread, or a future "export tasks as CSV" feature).
 *
 * @param {Blob} blob
 * @param {string} filename
 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}