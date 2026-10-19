import * as React from "react";

/**
 * Debounces a rapidly-changing value (e.g. a search input) so
 * dependent effects (like firing an API call) only run after the
 * value has stopped changing for `delayMs`.
 *
 * @param {*} value
 * @param {number} [delayMs=400]
 * @returns {*} the debounced value
 *
 * Usage:
 *   const debouncedSearch = useDebounce(searchInput, 400);
 *   useEffect(() => { fetchResults(debouncedSearch) }, [debouncedSearch]);
 */
export function useDebounce(value, delayMs = 400) {
  const [debouncedValue, setDebouncedValue] = React.useState(value);

  React.useEffect(() => {
    const timeout = setTimeout(() => setDebouncedValue(value), delayMs);
    return () => clearTimeout(timeout);
  }, [value, delayMs]);

  return debouncedValue;
}