import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import PageHeader from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import TaskBoard from "@/components/tasks/TaskBoard";
import TaskFilters from "@/components/tasks/TaskFilters";
import TaskFormDialog from "@/components/tasks/TaskFormDialog";
import ConfirmDialog from "@/components/shared/ConfirmDialog";
import taskApi from "@/api/taskApi";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Tasks — Kanban board of AI-extracted and manually created tasks.
 */
export default function TasksPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [filters, setFilters] = React.useState({});
  const [formOpen, setFormOpen] = React.useState(false);
  const [editingTask, setEditingTask] = React.useState(null);
  const [deleteTargetId, setDeleteTargetId] = React.useState(null);

  const tasksQuery = useQuery({
    queryKey: ["tasks", filters],
    queryFn: () => taskApi.getTasks({ ...filters, page: 1, pageSize: 200 }),
  });

  const invalidateTasks = () => queryClient.invalidateQueries({ queryKey: ["tasks"] });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }) => taskApi.updateTaskStatus(id, status),
    onMutate: async ({ id, status }) => {
      await queryClient.cancelQueries({ queryKey: ["tasks", filters] });
      const previous = queryClient.getQueryData(["tasks", filters]);
      queryClient.setQueryData(["tasks", filters], (old) =>
        old
          ? { ...old, items: old.items.map((t) => (t.id === id ? { ...t, status } : t)) }
          : old
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(["tasks", filters], context.previous);
      toast({ type: "error", message: "Couldn't update task status." });
    },
    onSettled: invalidateTasks,
  });

  const createMutation = useMutation({
    mutationFn: (payload) => taskApi.createTask(payload),
    onSuccess: () => {
      invalidateTasks();
      toast({ type: "success", message: "Task created." });
      setFormOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }) => taskApi.updateTask(id, updates),
    onSuccess: () => {
      invalidateTasks();
      toast({ type: "success", message: "Task updated." });
      setFormOpen(false);
      setEditingTask(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => taskApi.deleteTask(id),
    onSuccess: () => {
      invalidateTasks();
      toast({ type: "success", message: "Task deleted." });
      setDeleteTargetId(null);
    },
  });

  const handleFormSubmit = (payload) => {
    if (editingTask) {
      updateMutation.mutate({ id: editingTask.id, updates: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const tasks = tasksQuery.data?.items || [];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Tasks"
        description="AI-extracted and manual tasks, organized by status."
        actions={
          <Button onClick={() => { setEditingTask(null); setFormOpen(true); }}>
            <Plus className="h-4 w-4" />
            New Task
          </Button>
        }
      />

      <TaskFilters filters={filters} onFiltersChange={setFilters} />

      <TaskBoard
        tasks={tasks}
        isLoading={tasksQuery.isLoading}
        onStatusChange={(id, status) => statusMutation.mutate({ id, status })}
        onComplete={(id) => statusMutation.mutate({ id, status: "completed" })}
        onDismiss={(id) => statusMutation.mutate({ id, status: "dismissed" })}
        onEdit={(id) => {
          setEditingTask(tasks.find((t) => t.id === id));
          setFormOpen(true);
        }}
        onDelete={(id) => setDeleteTargetId(id)}
      />

      <TaskFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        initialTask={editingTask}
        onSubmit={handleFormSubmit}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      />

      <ConfirmDialog
        open={Boolean(deleteTargetId)}
        onOpenChange={(open) => !open && setDeleteTargetId(null)}
        title="Delete this task?"
        description="This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={() => deleteMutation.mutate(deleteTargetId)}
        isConfirming={deleteMutation.isPending}
      />
    </div>
  );
}