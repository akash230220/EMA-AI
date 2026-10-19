import * as React from "react";

/**
 * Reactively tracks whether a CSS media query currently matches.
 * Used for responsive JS logic that Tailwind's breakpoint classes
 * alone can't express (e.g. conditionally rendering a different
 * component tree, not just different styles).
 *
 * @param {string} query - e.g. "(min-width: 768px)"
 * @returns {boolean}
 *
 * Usage:
 *   const isDesktop = useMediaQuery("(min-width: 768px)");
 */
export function useMediaQuery(query) {
  const [matches, setMatches] = React.useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia(query).matches;
  });

  React.useEffect(() => {
    const mediaQueryList = window.matchMedia(query);
    const handler = (event) => setMatches(event.matches);

    setMatches(mediaQueryList.matches);
    mediaQueryList.addEventListener("change", handler);
    return () => mediaQueryList.removeEventListener("change", handler);
  }, [query]);

  return matches;
}

/** Convenience preset matching Tailwind's default `md` breakpoint. */
export function useIsMobile() {
  return !useMediaQuery("(min-width: 768px)");
}