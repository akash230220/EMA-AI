import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import taskApi from "@/api/taskApi";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Fetches a paginated, filtered list of tasks.
 * @param {object} filters
 */
export function useTasks(filters = {}) {
  return useQuery({
    queryKey: ["tasks", filters],
    queryFn: () => taskApi.getTasks(filters),
  });
}

/**
 * Fetches a single task by ID.
 * @param {string} taskId
 */
export function useTask(taskId) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: () => taskApi.getTaskById(taskId),
    enabled: Boolean(taskId),
  });
}

/**
 * Fetches lightweight task stats for Dashboard widgets.
 */
export function useTaskStats() {
  return useQuery({
    queryKey: ["task-stats"],
    queryFn: () => taskApi.getTaskStats(),
  });
}

/**
 * Creates a new manual task.
 */
export function useCreateTask() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (payload) => taskApi.createTask(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["task-stats"] });
      toast({ type: "success", message: "Task created." });
    },
    onError: () => toast({ type: "error", message: "Couldn't create task." }),
  });
}

/**
 * Updates an existing task's editable fields.
 */
export function useUpdateTask() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, updates }) => taskApi.updateTask(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast({ type: "success", message: "Task updated." });
    },
    onError: () => toast({ type: "error", message: "Couldn't update task." }),
  });
}

/**
 * Updates a task's status with an optimistic cache update — used by
 * the Kanban board's drag-and-drop so moves feel instant.
 * @param {object} filters - the same filters key used by useTasks(),
 *   needed to target the right cached list for the optimistic patch.
 */
export function useUpdateTaskStatus(filters = {}) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const queryKey = ["tasks", filters];

  return useMutation({
    mutationFn: ({ id, status }) => taskApi.updateTaskStatus(id, status),
    onMutate: async ({ id, status }) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData(queryKey);
      queryClient.setQueryData(queryKey, (old) =>
        old ? { ...old, items: old.items.map((t) => (t.id === id ? { ...t, status } : t)) } : old
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(queryKey, context.previous);
      toast({ type: "error", message: "Couldn't update task status." });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["task-stats"] });
    },
  });
}

/**
 * Deletes a task permanently.
 */
export function useDeleteTask() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id) => taskApi.deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["task-stats"] });
      toast({ type: "success", message: "Task deleted." });
    },
    onError: () => toast({ type: "error", message: "Couldn't delete task." }),
  });
}