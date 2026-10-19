/**
 * Barrel export for all Zustand stores — lets components import
 * from a single "@/store" path rather than reaching into individual
 * files, e.g.:
 *
 *   import { useUIStore, useInboxSelectionStore } from "@/store";
 */
export { useUIStore } from "./useUIStore";
export { useInboxSelectionStore } from "./useInboxSelectionStore";
export { useComposeStore } from "./useComposeStore";
export { useNotificationStore } from "./useNotificationStore";