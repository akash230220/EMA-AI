// src/api/automationApi.js
import axiosClient from "./axiosClient";

const automationApi = {
  getRules: async (params = {}) => {
    const { data } = await axiosClient.get("/automation/rules", { params });
    return data;
  },

  getRuleBuilderSchema: async () => {
    const { data } = await axiosClient.get("/automation/rules/schema");
    return data;
  },

  getRuleExecutionLogs: async (ruleId, params = {}) => {
    const { data } = await axiosClient.get(`/automation/rules/${ruleId}/logs`, { params });
    return data;
  },

  createRule: async (payload) => {
    const { data } = await axiosClient.post("/automation/rules", payload);
    return data;
  },

  updateRule: async (ruleId, updates) => {
    const { data } = await axiosClient.patch(`/automation/rules/${ruleId}`, updates);
    return data;
  },

  setRuleEnabled: async (ruleId, enabled) => {
    const { data } = await axiosClient.patch(`/automation/rules/${ruleId}/enabled`, { enabled });
    return data;
  },

  reorderRules: async (rules) => {
    const { data } = await axiosClient.post("/automation/rules/reorder", { rules });
    return data;
  },

  deleteRule: async (ruleId) => {
    await axiosClient.delete(`/automation/rules/${ruleId}`);
  },

  testRule: async (payload) => {
    const { data } = await axiosClient.post("/automation/rules/test", payload);
    return data;
  },
};

export default automationApi;
