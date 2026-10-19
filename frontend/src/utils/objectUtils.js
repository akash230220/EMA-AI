/**
 * Object manipulation helpers, primarily for working with filter
 * state objects (InboxFilters, TaskFilters, MeetingFilters) and
 * form payloads before sending them to the API layer.
 */

/**
 * Removes keys with undefined/null/empty-string values from an
 * object — used before sending filter params to an API call so
 * "no filter selected" doesn't get serialized as `?priority=`.
 *
 * @param {object} obj
 * @returns {object}
 */
export function omitEmpty(obj) {
  return Object.fromEntries(
    Object.entries(obj).filter(([, value]) => value !== undefined && value !== null && value !== "")
  );
}

/**
 * Picks a subset of keys from an object — useful when constructing
 * a partial update payload from full form state.
 *
 * @param {object} obj
 * @param {string[]} keys
 * @returns {object}
 */
export function pick(obj, keys) {
  return Object.fromEntries(keys.filter((k) => k in obj).map((k) => [k, obj[k]]));
}

/**
 * Omits a set of keys from an object — inverse of pick(). Used when
 * stripping internal-only fields (e.g. a temp client-side `_id`)
 * before submitting a payload.
 *
 * @param {object} obj
 * @param {string[]} keys
 * @returns {object}
 */
export function omit(obj, keys) {
  const keySet = new Set(keys);
  return Object.fromEntries(Object.entries(obj).filter(([k]) => !keySet.has(k)));
}

/**
 * Shallow-compares two objects for equality across a given set of
 * keys (or all keys of `a` if not specified) — used by form
 * components (ProfileForm, TaskFormDialog) to compute a `hasChanges`
 * flag that enables/disables the Save button.
 *
 * @param {object} a
 * @param {object} b
 * @param {string[]} [keys]
 * @returns {boolean}
 */
export function shallowEqual(a, b, keys) {
  const compareKeys = keys || Object.keys(a);
  return compareKeys.every((k) => a[k] === b[k]);
}

/**
 * Deep-clones a plain JSON-serializable object/array — used when a
 * component needs to mutate a copy of query-cache data without
 * risking accidental mutation of the React Query cache itself
 * (e.g. RuleBuilder's local conditions/actions arrays seeded from
 * an initialRule prop).
 *
 * @param {*} value
 * @returns {*}
 */
export function deepClone(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

/**
 * Checks whether an object has no own enumerable keys — used for
 * empty-filters checks (e.g. "no active filters" state in
 * InboxFilters/TaskFilters/MeetingFilters badge counts).
 *
 * @param {object} obj
 * @returns {boolean}
 */
export function isEmptyObject(obj) {
  return !obj || Object.keys(obj).length === 0;
}