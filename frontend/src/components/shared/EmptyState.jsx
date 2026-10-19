import * as React from "react";
import { Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Generic empty-state block for lists/pages with no data — used
 * across Inbox, Tasks, Meetings, Automation Rules, etc. when the
 * per-feature empty state doesn't need bespoke copy/actions.
 *
 * @param {object} props
 * @param {React.ComponentType} [props.icon=Inbox] - lucide-react icon component
 * @param {string} props.title
 * @param {string} [props.description]
 * @param {{label: string, onClick: () => void}} [props.action]
 * @param {string} [props.className]
 */
export default function EmptyState({ icon: Icon = Inbox, title, description, action, className }) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 py-16 text-center", className)}>
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
        <Icon className="h-6 w-6 text-muted-foreground" />
      </div>
      <div>
        <p className="text-sm font-medium">{title}</p>
        {description && <p className="mt-1 max-w-xs text-xs text-muted-foreground">{description}</p>}
      </div>
      {action && (
        <Button size="sm" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}