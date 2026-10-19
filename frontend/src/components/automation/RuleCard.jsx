import * as React from "react";
import { Zap, MoreVertical, Pencil, Trash2, History, GripVertical } from "lucide-react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Card, CardContent } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

/**
 * Single automation rule row — shows name, condition/action summary,
 * enabled toggle, and a drag handle for reordering priority.
 *
 * @param {object} props
 * @param {object} props.rule
 * @param {(id: string, enabled: boolean) => void} props.onToggleEnabled
 * @param {(id: string) => void} props.onEdit
 * @param {(id: string) => void} props.onDelete
 * @param {(id: string) => void} props.onViewLogs
 */
export default function RuleCard({ rule, onToggleEnabled, onEdit, onDelete, onViewLogs }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: rule.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const conditionSummary = (rule.conditions || [])
    .map((c) => `${formatField(c.field)} ${formatOperator(c.operator)} "${c.value}"`)
    .join(rule.conditionLogic === "OR" ? "  OR  " : "  AND  ");

  const actionSummary = (rule.actions || []).map((a) => formatActionLabel(a)).join(", ");

  return (
    <div ref={setNodeRef} style={style} className={cn(isDragging && "opacity-50")}>
      <Card className={cn("transition-shadow", !rule.enabled && "opacity-60")}>
        <CardContent className="flex items-start gap-3 p-4">
          <button
            {...attributes}
            {...listeners}
            className="mt-1 shrink-0 cursor-grab text-muted-foreground active:cursor-grabbing"
            aria-label="Reorder rule"
          >
            <GripVertical className="h-4 w-4" />
          </button>

          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
            <Zap className="h-4 w-4" />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="truncate text-sm font-semibold">{rule.name}</h3>
              {!rule.enabled && (
                <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                  Disabled
                </Badge>
              )}
            </div>
            {rule.description && (
              <p className="mt-0.5 truncate text-xs text-muted-foreground">{rule.description}</p>
            )}
            <p className="mt-1.5 truncate text-xs text-muted-foreground">
              <span className="font-medium text-foreground">If</span> {conditionSummary || "no conditions"}{" "}
              <span className="font-medium text-foreground">then</span> {actionSummary || "no actions"}
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <Switch
              checked={rule.enabled}
              onCheckedChange={(checked) => onToggleEnabled(rule.id, checked)}
              aria-label={`${rule.enabled ? "Disable" : "Enable"} rule`}
            />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="text-muted-foreground hover:text-foreground">
                  <MoreVertical className="h-4 w-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEdit(rule.id)}>
                  <Pencil className="mr-2 h-3.5 w-3.5" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onViewLogs(rule.id)}>
                  <History className="mr-2 h-3.5 w-3.5" />
                  Execution history
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onDelete(rule.id)} className="text-destructive focus:text-destructive">
                  <Trash2 className="mr-2 h-3.5 w-3.5" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function formatField(field) {
  return String(field || "").replace(/_/g, " ");
}
function formatOperator(operator) {
  const map = { equals: "=", not_equals: "≠", contains: "contains", starts_with: "starts with" };
  return map[operator] || operator;
}
function formatActionLabel(action) {
  const map = {
    archive: "Archive",
    delete: "Delete",
    label: `Label "${action.value}"`,
    mark_read: "Mark as read",
    forward: `Forward to ${action.value}`,
    auto_reply: "Auto-reply",
    notify: "Send notification",
  };
  return map[action.type] || action.type;
}