// src/api/taskApi.js
import axiosClient from "./axiosClient";

/**
 * Task API layer.
 *
 * Covers AI-extracted tasks (from the Task Agent) as well as
 * manually created tasks. Pairs with backend endpoints under
 * /api/v1/tasks (see backend/app/api/v1/endpoints/tasks.py).
 */

const taskApi = {
  /**
   * Fetches a paginated, filterable list of tasks.
   *
   * @param {object} params
   * @param {number} [params.page=1]
   * @param {number} [params.pageSize=20]
   * @param {string} [params.status] - "pending" | "in_progress" | "completed" | "dismissed"
   * @param {string} [params.priority] - "high" | "medium" | "low"
   * @param {string} [params.source] - "ai_extracted" | "manual"
   * @param {string} [params.emailId] - filter tasks linked to a specific email
   * @param {string} [params.dueBefore] - ISO date string
   * @param {string} [params.sortBy] - "due_date" | "priority" | "created_at"
   * @param {string} [params.sortOrder] - "asc" | "desc"
   * @returns {Promise<{items: object[], total: number, page: number, pageSize: number}>}
   */
  getTasks: async (params = {}) => {
    const { data } = await axiosClient.get("/tasks", { params });
    return data;
  },

  /**
   * Fetches a single task by ID, including its source email reference
   * (if AI-extracted) and any linked meeting.
   * @param {string} taskId
   * @returns {Promise<object>}
   */
  getTaskById: async (taskId) => {
    const { data } = await axiosClient.get(`/tasks/${taskId}`);
    return data;
  },

  /**
   * Creates a new manual task (not derived from an email).
   *
   * @param {object} payload
   * @param {string} payload.title
   * @param {string} [payload.description]
   * @param {string} [payload.dueDate] - ISO date string
   * @param {string} [payload.priority] - "high" | "medium" | "low"
   * @returns {Promise<object>} created task
   */
  createTask: async (payload) => {
    const { data } = await axiosClient.post("/tasks", payload);
    return data;
  },

  /**
   * Updates an existing task's editable fields.
   *
   * @param {string} taskId
   * @param {object} updates
   * @param {string} [updates.title]
   * @param {string} [updates.description]
   * @param {string} [updates.dueDate]
   * @param {string} [updates.priority]
   * @returns {Promise<object>} updated task
   */
  updateTask: async (taskId, updates) => {
    const { data } = await axiosClient.patch(`/tasks/${taskId}`, updates);
    return data;
  },

  /**
   * Updates just the status of a task (e.g. drag-and-drop on a Kanban board).
   * @param {string} taskId
   * @param {"pending"|"in_progress"|"completed"|"dismissed"} status
   * @returns {Promise<object>} updated task
   */
  updateTaskStatus: async (taskId, status) => {
    const { data } = await axiosClient.patch(`/tasks/${taskId}/status`, { status });
    return data;
  },

  /**
   * Marks a task complete. Convenience wrapper around updateTaskStatus.
   * @param {string} taskId
   * @returns {Promise<object>} updated task
   */
  completeTask: async (taskId) => {
    const { data } = await axiosClient.patch(`/tasks/${taskId}/status`, { status: "completed" });
    return data;
  },

  /**
   * Dismisses an AI-extracted task the user doesn't want to track
   * (e.g. a false positive from the Task Agent).
   * @param {string} taskId
   * @returns {Promise<object>} updated task
   */
  dismissTask: async (taskId) => {
    const { data } = await axiosClient.patch(`/tasks/${taskId}/status`, { status: "dismissed" });
    return data;
  },

  /**
   * Permanently deletes a task.
   * @param {string} taskId
   * @returns {Promise<void>}
   */
  deleteTask: async (taskId) => {
    await axiosClient.delete(`/tasks/${taskId}`);
  },

  /**
   * Applies a bulk status update to multiple tasks at once
   * (e.g. Kanban board multi-select, "mark all complete").
   * @param {string[]} taskIds
   * @param {"pending"|"in_progress"|"completed"|"dismissed"} status
   * @returns {Promise<{affected: number}>}
   */
  bulkUpdateStatus: async (taskIds, status) => {
    const { data } = await axiosClient.post("/tasks/bulk/status", {
      task_ids: taskIds,
      status,
    });
    return data;
  },

  /**
   * Fetches lightweight task summary stats for the Dashboard
   * (e.g. total pending, overdue count) without pulling full task list.
   * @returns {Promise<{total: number, pending: number, completed: number, overdue: number}>}
   */
  getTaskStats: async () => {
    const { data } = await axiosClient.get("/tasks/stats");
    return data;
  },
};

export default taskApi;