import * as React from "react";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import TaskCard from "./TaskCard";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const STATUS_CONFIG = {
  pending: { label: "Pending", dot: "bg-gray-400" },
  in_progress: { label: "In Progress", dot: "bg-amber-500" },
  completed: { label: "Completed", dot: "bg-emerald-500" },
  dismissed: { label: "Dismissed", dot: "bg-gray-300" },
};

/**
 * A single droppable Kanban column for one task status.
 *
 * @param {object} props
 * @param {string} props.status - "pending" | "in_progress" | "completed" | "dismissed"
 * @param {object[]} props.tasks
 * @param {boolean} [props.isLoading]
 * @param {(taskId: string) => void} props.onComplete
 * @param {(taskId: string) => void} props.onDismiss
 * @param {(taskId: string) => void} props.onEdit
 * @param {(taskId: string) => void} props.onDelete
 */
export default function TaskColumn({ status, tasks, isLoading, onComplete, onDismiss, onEdit, onDelete }) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  const config = STATUS_CONFIG[status] || { label: status, dot: "bg-gray-400" };

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex w-72 shrink-0 flex-col rounded-lg bg-muted/40 transition-colors",
        isOver && "bg-primary/5 ring-2 ring-primary/30"
      )}
    >
      <div className="flex items-center gap-2 px-3 py-2.5">
        <span className={cn("h-2 w-2 rounded-full", config.dot)} />
        <h3 className="text-sm font-semibold">{config.label}</h3>
        <span className="ml-auto rounded-full bg-background px-2 py-0.5 text-[11px] text-muted-foreground">
          {tasks.length}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        ) : tasks.length === 0 ? (
          <div className="flex h-20 items-center justify-center text-xs text-muted-foreground">
            No tasks
          </div>
        ) : (
          <SortableContext items={tasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onComplete={onComplete}
                onDismiss={onDismiss}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </SortableContext>
        )}
      </div>
    </div>
  );
}