import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Standard page title block used at the top of most pages (Inbox,
 * Tasks, Meetings, Automation Rules, Settings) — a consistent
 * title + description + optional right-aligned actions slot.
 *
 * @param {object} props
 * @param {string} props.title
 * @param {string} [props.description]
 * @param {React.ReactNode} [props.actions] - buttons/controls rendered on the right
 * @param {string} [props.className]
 */
export default function PageHeader({ title, description, actions, className }) {
  return (
    <div className={cn("mb-4 flex flex-wrap items-center justify-between gap-3", className)}>
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}