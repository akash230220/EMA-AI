/**
 * Array manipulation helpers used across list-heavy components
 * (EmailList, TaskBoard, MeetingList, RuleList) for grouping,
 * sorting, and deduplication.
 */

/**
 * Groups an array of items by a key derived from each item.
 * Used by MeetingList (grouping by dateGroupLabel) and could
 * replace similar inline logic elsewhere.
 *
 * @template T
 * @param {T[]} items
 * @param {(item: T) => string} keyFn
 * @returns {Map<string, T[]>}
 */
export function groupBy(items, keyFn) {
  const map = new Map();
  for (const item of items) {
    const key = keyFn(item);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(item);
  }
  return map;
}

/**
 * Buckets an array into a fixed set of named groups (e.g. task
 * status columns). Any item whose key isn't in `groupKeys` falls
 * into the first group as a safe default — mirrors TaskBoard.jsx's
 * tasksByStatus logic.
 *
 * @template T
 * @param {T[]} items
 * @param {string[]} groupKeys
 * @param {(item: T) => string} keyFn
 * @returns {Record<string, T[]>}
 */
export function bucketBy(items, groupKeys, keyFn) {
  const result = Object.fromEntries(groupKeys.map((k) => [k, []]));
  for (const item of items) {
    const key = keyFn(item);
    (result[key] || result[groupKeys[0]]).push(item);
  }
  return result;
}

/**
 * Moves an array item from one index to another, returning a new
 * array (does not mutate). Used as a fallback if @dnd-kit's
 * arrayMove isn't imported in a given file.
 *
 * @template T
 * @param {T[]} array
 * @param {number} fromIndex
 * @param {number} toIndex
 * @returns {T[]}
 */
export function moveItem(array, fromIndex, toIndex) {
  const result = [...array];
  const [removed] = result.splice(fromIndex, 1);
  result.splice(toIndex, 0, removed);
  return result;
}

/**
 * Deduplicates an array of objects by a given key, keeping the
 * first occurrence. Useful when merging paginated results (e.g.
 * semantic search results across repeated queries).
 *
 * @template T
 * @param {T[]} items
 * @param {(item: T) => string} keyFn
 * @returns {T[]}
 */
export function dedupeBy(items, keyFn) {
  const seen = new Set();
  const result = [];
  for (const item of items) {
    const key = keyFn(item);
    if (!seen.has(key)) {
      seen.add(key);
      result.push(item);
    }
  }
  return result;
}

/**
 * Sorts an array of objects by a numeric or string field,
 * descending by default (most common case: sort by count/score).
 *
 * @template T
 * @param {T[]} items
 * @param {(item: T) => number|string} valueFn
 * @param {"asc"|"desc"} [direction="desc"]
 * @returns {T[]} a new sorted array
 */
export function sortBy(items, valueFn, direction = "desc") {
  const sorted = [...items].sort((a, b) => {
    const aVal = valueFn(a);
    const bVal = valueFn(b);
    if (aVal < bVal) return -1;
    if (aVal > bVal) return 1;
    return 0;
  });
  return direction === "desc" ? sorted.reverse() : sorted;
}

/**
 * Splits an array into chunks of a given size — useful for batching
 * bulk API calls (e.g. bulkAction on a very large selection) to
 * avoid oversized request payloads.
 *
 * @template T
 * @param {T[]} items
 * @param {number} size
 * @returns {T[][]}
 */
export function chunk(items, size) {
  const chunks = [];
  for (let i = 0; i < items.length; i += size) {
    chunks.push(items.slice(i, i + size));
  }
  return chunks;
}