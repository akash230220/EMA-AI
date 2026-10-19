import * as React from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Lightweight toast notification system (success/error/info),
 * implemented without a UI-kit dependency for simplicity. Wrap the
 * app root with <ToastProvider> and use the `useToast()` hook
 * anywhere below it to fire notifications.
 *
 * Usage:
 *   const { toast } = useToast();
 *   toast({ type: "success", message: "Reply sent!" });
 */

const ToastContext = React.createContext(null);

const ICONS = {
  success: { Icon: CheckCircle2, className: "text-emerald-600 bg-emerald-50" },
  error: { Icon: XCircle, className: "text-red-600 bg-red-50" },
  info: { Icon: Info, className: "text-blue-600 bg-blue-50" },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = React.useState([]);

  const toast = React.useCallback(({ type = "info", message, duration = 4000 }) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { id, type, message }]);
    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }
    return id;
  }, []);

  const dismiss = React.useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast, dismiss }}>
      {children}
      {typeof document !== "undefined" &&
        createPortal(
          <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
            <AnimatePresence>
              {toasts.map((t) => {
                const { Icon, className } = ICONS[t.type] || ICONS.info;
                return (
                  <motion.div
                    key={t.id}
                    initial={{ opacity: 0, y: 12, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="flex w-80 items-start gap-2.5 rounded-lg border border-border bg-card p-3 shadow-lg"
                  >
                    <div className={cn("flex h-6 w-6 shrink-0 items-center justify-center rounded-full", className)}>
                      <Icon className="h-3.5 w-3.5" />
                    </div>
                    <p className="flex-1 text-sm text-foreground">{t.message}</p>
                    <button onClick={() => dismiss(t.id)} className="shrink-0 text-muted-foreground hover:text-foreground">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>,
          document.body
        )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a <ToastProvider>");
  }
  return ctx;
}