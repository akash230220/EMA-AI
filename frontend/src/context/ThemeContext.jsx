import * as React from "react";

export const ThemeContext = React.createContext(null);

const THEME_STORAGE_KEY = "ai_email_os_theme";
const THEMES = ["light", "dark", "system"];

/**
 * Theme provider supporting light/dark/system modes. Applies the
 * resolved theme as a `dark` class on <html> (Tailwind's default
 * dark-mode strategy — requires `darkMode: "class"` in
 * tailwind.config.js). Persists the user's choice to localStorage
 * and reacts live to OS-level theme changes when set to "system".
 *
 * Wrap the app root with this, typically above <AuthProvider>:
 *   <ThemeProvider>
 *     <AuthProvider>
 *       <AppRouter />
 *     </AuthProvider>
 *   </ThemeProvider>
 */
export function ThemeProvider({ children }) {
  const [theme, setThemeState] = React.useState(() => {
    if (typeof window === "undefined") return "system";
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    return THEMES.includes(stored) ? stored : "system";
  });

  const resolvedTheme = useResolvedTheme(theme);

  React.useEffect(() => {
    const root = window.document.documentElement;
    root.classList.toggle("dark", resolvedTheme === "dark");
  }, [resolvedTheme]);

  const setTheme = React.useCallback((next) => {
    setThemeState(next);
    window.localStorage.setItem(THEME_STORAGE_KEY, next);
  }, []);

  const value = React.useMemo(
    () => ({ theme, resolvedTheme, setTheme }),
    [theme, resolvedTheme, setTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * Resolves "system" down to an actual "light"/"dark" value by
 * reading (and subscribing to changes in) the OS color-scheme
 * media query. Returns the theme as-is if it's already explicit.
 */
function useResolvedTheme(theme) {
  const [systemTheme, setSystemTheme] = React.useState(() => {
    if (typeof window === "undefined") return "light";
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  React.useEffect(() => {
    if (theme !== "system") return;
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e) => setSystemTheme(e.matches ? "dark" : "light");
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, [theme]);

  return theme === "system" ? systemTheme : theme;
}