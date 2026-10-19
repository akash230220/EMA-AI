import * as React from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useNavigate } from "react-router-dom";
import { Sparkles, Mail, Calendar, MoreVertical, Check, X } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const PRIORITY_VARIANT = { high: "destructive", medium: "warning", low: "success" };

/**
 * Single draggable task card for the Kanban board. Shows AI-extracted
 * badge (source), priority, due date, and a link back to the source
 * email if AI-extracted.
 *
 * @param {object} props
 * @param {object} props.task
 * @param {(taskId: string) => void} props.onComplete
 * @param {(taskId: string) => void} props.onDismiss
 * @param {(taskId: string) => void} props.onEdit
 * @param {(taskId: string) => void} props.onDelete
 */
export default function TaskCard({ task, onComplete, onDismiss, onEdit, onDelete }) {
  const navigate = useNavigate();
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const isOverdue = task.dueDate && new Date(task.dueDate) < new Date() && task.status !== "completed";

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <Card
        className={cn(
          "mb-2 cursor-grab active:cursor-grabbing transition-shadow hover:shadow-md",
          isDragging && "opacity-50 shadow-lg"
        )}
      >
        <CardContent className="p-3 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <p className="flex-1 text-sm font-medium leading-snug">{task.title}</p>
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <button className="shrink-0 text-muted-foreground hover:text-foreground">
                  <MoreVertical className="h-3.5 w-3.5" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
                <DropdownMenuItem onClick={() => onEdit(task.id)}>Edit</DropdownMenuItem>
                {task.status !== "completed" && (
                  <DropdownMenuItem onClick={() => onComplete(task.id)}>
                    <Check className="mr-2 h-3.5 w-3.5" />
                    Mark complete
                  </DropdownMenuItem>
                )}
                {task.source === "ai_extracted" && task.status !== "dismissed" && (
                  <DropdownMenuItem onClick={() => onDismiss(task.id)}>
                    <X className="mr-2 h-3.5 w-3.5" />
                    Dismiss
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={() => onDelete(task.id)} className="text-destructive focus:text-destructive">
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {task.description && (
            <p className="line-clamp-2 text-xs text-muted-foreground">{task.description}</p>
          )}

          <div className="flex flex-wrap items-center gap-1.5">
            {task.priority && (
              <Badge variant={PRIORITY_VARIANT[task.priority] || "outline"} className="text-[10px] px-1.5 py-0 capitalize">
                {task.priority}
              </Badge>
            )}
            {task.source === "ai_extracted" && (
              <Badge variant="outline" className="gap-1 text-[10px] px-1.5 py-0 border-indigo-300 text-indigo-700">
                <Sparkles className="h-2.5 w-2.5" />
                AI
              </Badge>
            )}
          </div>

          <div className="flex items-center justify-between pt-0.5">
            {task.dueDateLabel && (
              <span
                className={cn(
                  "flex items-center gap-1 text-[11px]",
                  isOverdue ? "font-medium text-red-600" : "text-muted-foreground"
                )}
              >
                <Calendar className="h-3 w-3" />
                {task.dueDateLabel}
              </span>
            )}
            {task.sourceEmailId && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/inbox/${task.sourceEmailId}`);
                }}
                className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-primary"
                title="View source email"
              >
                <Mail className="h-3 w-3" />
              </button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}