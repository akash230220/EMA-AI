import { create } from "zustand";

/**
 * Cross-component email multi-select state for the Inbox. Lives
 * outside EmailList's local useState so other parts of the UI
 * (e.g. a future floating "bulk actions" bar rendered in AppShell,
 * or keyboard-shortcut handlers registered at the page level) can
 * read/react to the current selection without prop drilling through
 * EmailList -> EmailListItem.
 *
 * Deliberately NOT persisted — selection should always reset on
 * navigation/reload, unlike sidebar preference.
 *
 * Usage:
 *   const selectedIds = useInboxSelectionStore((s) => s.selectedIds);
 *   const toggle = useInboxSelectionStore((s) => s.toggle);
 */
export const useInboxSelectionStore = create((set, get) => ({
  selectedIds: new Set(),

  toggle: (id) =>
    set((state) => {
      const next = new Set(state.selectedIds);
      next.has(id) ? next.delete(id) : next.add(id);
      return { selectedIds: next };
    }),

  selectAll: (ids) => set({ selectedIds: new Set(ids) }),

  clear: () => set({ selectedIds: new Set() }),

  isSelected: (id) => get().selectedIds.has(id),

  get count() {
    return get().selectedIds.size;
  },
}));