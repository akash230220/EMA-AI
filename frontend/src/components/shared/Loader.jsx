import * as React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Generic loading spinner. Use `fullScreen` for page-level loading
 * states (e.g. initial auth check before routes render), or the
 * default inline size for buttons/small containers.
 *
 * @param {object} props
 * @param {"sm"|"md"|"lg"} [props.size="md"]
 * @param {string} [props.label] - optional text shown below the spinner
 * @param {boolean} [props.fullScreen] - centers within the full viewport
 * @param {string} [props.className]
 */
export default function Loader({ size = "md", label, fullScreen = false, className }) {
  const sizeMap = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-10 w-10",
  };

  const content = (
    <div className={cn("flex flex-col items-center justify-center gap-2", className)}>
      <Loader2 className={cn("animate-spin text-primary", sizeMap[size])} />
      {label && <p className="text-sm text-muted-foreground">{label}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        {content}
      </div>
    );
  }

  return content;
}