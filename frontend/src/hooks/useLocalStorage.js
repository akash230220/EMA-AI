import * as React from "react";

/**
 * useState backed by localStorage — value persists across page
 * reloads and browser sessions. Used for lightweight UI preferences
 * like sidebar-collapsed state (see AppShell.jsx) rather than
 * anything sensitive (auth tokens use the dedicated tokenStorage
 * helper in api/axiosClient.js instead).
 *
 * @param {string} key
 * @param {*} initialValue
 * @returns {[*, (value: *|((prev: *) => *)) => void]}
 */
export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = React.useState(() => {
    if (typeof window === "undefined") return initialValue;
    try {
      const item = window.localStorage.getItem(key);
      return item !== null ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = React.useCallback(
    (value) => {
      setStoredValue((prev) => {
        const next = value instanceof Function ? value(prev) : value;
        try {
          window.localStorage.setItem(key, JSON.stringify(next));
        } catch {
          // Storage might be full or disabled (private browsing) — fail silently
        }
        return next;
      });
    },
    [key]
  );

  return [storedValue, setValue];
}