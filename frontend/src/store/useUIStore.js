import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * Global UI chrome state — sidebar collapse, mobile nav drawer, and
 * the command palette. Kept separate from AuthContext/ThemeContext
 * (which are React Context) because this state changes frequently
 * and is read by components that don't need a full context
 * provider re-render cascade (Zustand only re-renders subscribers
 * of the specific slice they select).
 *
 * `sidebarCollapsed` persists to localStorage via Zustand's
 * `persist` middleware — this replaces the manual localStorage
 * read/write that was previously inlined in AppShell.jsx.
 *
 * Usage:
 *   const collapsed = useUIStore((s) => s.sidebarCollapsed);
 *   const toggleSidebar = useUIStore((s) => s.toggleSidebar);
 */
export const useUIStore = create(
  persist(
    (set) => ({
      // Sidebar
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      // Mobile nav drawer
      mobileNavOpen: false,
      openMobileNav: () => set({ mobileNavOpen: true }),
      closeMobileNav: () => set({ mobileNavOpen: false }),

      // Command palette (Cmd+K style quick nav/search)
      commandPaletteOpen: false,
      openCommandPalette: () => set({ commandPaletteOpen: true }),
      closeCommandPalette: () => set({ commandPaletteOpen: false }),
      toggleCommandPalette: () => set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen })),
    }),
    {
      name: "ai_email_os_ui_store",
      // Only persist sidebar preference — mobile nav / command palette
      // should always start closed on a fresh page load.
      partialize: (state) => ({ sidebarCollapsed: state.sidebarCollapsed }),
    }
  )
);