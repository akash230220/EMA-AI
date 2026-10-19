/**
 * Barrel export for the utils/ folder. Note the distinction from
 * lib/: lib/ holds cn() (ShadCN's className merger), constants.js,
 * formatters.js (date/time/number display), validators.js, and
 * queryKeys.js/apiErrors.js (React Query-specific helpers). This
 * folder (utils/) holds general-purpose, framework-agnostic helpers
 * — array/object manipulation, string transforms, URL building,
 * and file handling — that don't depend on React Query, Tailwind,
 * or any app-specific data shape.
 *
 * Usage:
 *   import { groupBy, omitEmpty, snakeToLabel } from "@/utils";
 */
export * from "./arrayUtils";
export * from "./objectUtils";
export * from "./stringUtils";
export * from "./urlUtils";
export * from "./fileUtils";