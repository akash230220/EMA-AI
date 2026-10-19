import * as React from "react";

/**
 * Fires a callback when a click/touch occurs outside the referenced
 * element. Useful for custom dropdowns/popovers that aren't already
 * built on Radix primitives (which handle this internally).
 *
 * @param {(event: MouseEvent|TouchEvent) => void} onClickOutside
 * @returns {React.RefObject}
 *
 * Usage:
 *   const ref = useClickOutside(() => setOpen(false));
 *   return <div ref={ref}>...</div>;
 */
export function useClickOutside(onClickOutside) {
  const ref = React.useRef(null);

  React.useEffect(() => {
    const handler = (event) => {
      if (ref.current && !ref.current.contains(event.target)) {
        onClickOutside(event);
      }
    };
    document.addEventListener("mousedown", handler);
    document.addEventListener("touchstart", handler);
    return () => {
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("touchstart", handler);
    };
  }, [onClickOutside]);

  return ref;
}