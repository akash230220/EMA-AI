import { create } from "zustand";

/**
 * State for a floating/minimizable reply composer — mirrors the
 * Gmail pattern where starting a reply from one part of the app
 * (e.g. clicking "Quick Reply" on a RecentEmailsWidget row on the
 * Dashboard) can pop open a persistent composer that survives
 * navigating to a different page, rather than being tied to
 * EmailDetailPage's local component state.
 *
 * Not wired into any component yet in this codebase (ReplyComposer
 * currently lives inline on EmailDetailPage/AIReplyCenterPage) —
 * included here as the natural home for that behavior if/when you
 * want a global "compose anywhere" experience.
 *
 * Usage:
 *   const { openCompose } = useComposeStore();
 *   openCompose({ emailId: "123", subject: "Re: Q3 Budget" });
 */
export const useComposeStore = create((set) => ({
  isOpen: false,
  isMinimized: false,
  emailId: null,
  subject: null,
  draftBody: "",

  openCompose: ({ emailId, subject, draftBody = "" }) =>
    set({ isOpen: true, isMinimized: false, emailId, subject, draftBody }),

  minimize: () => set({ isMinimized: true }),
  restore: () => set({ isMinimized: false }),

  updateDraftBody: (body) => set({ draftBody: body }),

  closeCompose: () =>
    set({ isOpen: false, isMinimized: false, emailId: null, subject: null, draftBody: "" }),
}));