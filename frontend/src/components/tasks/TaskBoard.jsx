import * as React from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from "@dnd-kit/core";
import TaskColumn from "./TaskColumn";
import TaskCard from "./TaskCard";

const COLUMNS = ["pending", "in_progress", "completed", "dismissed"];

/**
 * Kanban board for tasks — four droppable columns (pending,
 * in_progress, completed, dismissed) with drag-and-drop status
 * updates. Purely presentational: parent TasksPage owns task
 * state via React Query and passes down status-change handling.
 *
 * @param {object} props
 * @param {object[]} props.tasks
 * @param {boolean} [props.isLoading]
 * @param {(taskId: string, newStatus: string) => void} props.onStatusChange
 * @param {(taskId: string) => void} props.onComplete
 * @param {(taskId: string) => void} props.onDismiss
 * @param {(taskId: string) => void} props.onEdit
 * @param {(taskId: string) => void} props.onDelete
 */
export default function TaskBoard({
  tasks = [],
  isLoading,
  onStatusChange,
  onComplete,
  onDismiss,
  onEdit,
  onDelete,
}) {
  const [activeTask, setActiveTask] = React.useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  const tasksByStatus = React.useMemo(() => {
    const grouped = { pending: [], in_progress: [], completed: [], dismissed: [] };
    for (const task of tasks) {
      (grouped[task.status] || grouped.pending).push(task);
    }
    return grouped;
  }, [tasks]);

  const handleDragStart = (event) => {
    const task = tasks.find((t) => t.id === event.active.id);
    setActiveTask(task || null);
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    setActiveTask(null);
    if (!over) return;

    const taskId = active.id;
    const targetStatus = COLUMNS.includes(over.id) ? over.id : over.data?.current?.sortable?.containerId;
    const task = tasks.find((t) => t.id === taskId);

    if (task && targetStatus && task.status !== targetStatus) {
      onStatusChange(taskId, targetStatus);
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-3 overflow-x-auto pb-4">
        {COLUMNS.map((status) => (
          <TaskColumn
            key={status}
            status={status}
            tasks={tasksByStatus[status]}
            isLoading={isLoading}
            onComplete={onComplete}
            onDismiss={onDismiss}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </div>

      <DragOverlay>
        {activeTask ? (
          <div className="w-72 rotate-2 opacity-90">
            <TaskCard
              task={activeTask}
              onComplete={() => {}}
              onDismiss={() => {}}
              onEdit={() => {}}
              onDelete={() => {}}
            />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}