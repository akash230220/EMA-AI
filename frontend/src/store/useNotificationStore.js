import { create } from "zustand";

/**
 * In-app notification bell state (Topbar.jsx's bell icon) — distinct
 * from ToastProvider's ephemeral toasts. Toasts are for "this action
 * just happened" feedback that disappears after a few seconds;
 * this store is for a persistent, dismissible notification feed
 * (e.g. "High priority email from X", "3 meetings detected today")
 * the user can review later by opening the bell dropdown.
 *
 * In a full implementation, this would likely be seeded by a
 * WebSocket/SSE subscription or periodic polling against a
 * notifications API endpoint — not built here since no such
 * endpoint exists yet in the api/ folder.
 *
 * Usage:
 *   const { notifications, unreadCount, addNotification, markAsRead } = useNotificationStore();
 */
export const useNotificationStore = create((set, get) => ({
  notifications: [],

  get unreadCount() {
    return get().notifications.filter((n) => !n.read).length;
  },

  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        { id: crypto.randomUUID(), read: false, createdAt: new Date().toISOString(), ...notification },
        ...state.notifications,
      ].slice(0, 50), // cap the in-memory feed to the most recent 50
    })),

  markAsRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) => (n.id === id ? { ...n, read: true } : n)),
    })),

  markAllAsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
    })),

  dismiss: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  clearAll: () => set({ notifications: [] }),
}));