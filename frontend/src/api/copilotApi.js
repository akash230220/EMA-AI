// src/api/copilotApi.js
import axiosClient from "./axiosClient";

const copilotApi = {
  getConversations: async (params = {}) => {
    const { data } = await axiosClient.get("/copilot/conversations", { params });
    return data;
  },

  getConversationById: async (conversationId) => {
    const { data } = await axiosClient.get(`/copilot/conversations/${conversationId}`);
    return data;
  },

  renameConversation: async (conversationId, title) => {
    const { data } = await axiosClient.patch(`/copilot/conversations/${conversationId}`, { title });
    return data;
  },

  deleteConversation: async (conversationId) => {
    await axiosClient.delete(`/copilot/conversations/${conversationId}`);
  },

  submitFeedback: async (messageId, rating, comment) => {
    await axiosClient.post(`/copilot/messages/${messageId}/feedback`, { rating, comment });
  },

  streamMessage: async (payload, signal) => {
    const response = await fetch(`${axiosClient.defaults.baseURL}/copilot/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      throw new Error(`Copilot request failed with status ${response.status}`);
    }

    return response;
  },
};

export default copilotApi;
