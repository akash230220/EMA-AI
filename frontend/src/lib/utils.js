import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind classes safely, resolving conflicts
 * (e.g. "px-2" + "px-4" -> "px-4"). Used by every ShadCN component.
 * (Same file referenced back in components/ui/ — included here for
 * completeness since lib/ is its canonical home.)
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}