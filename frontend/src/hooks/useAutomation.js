import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import automationApi from "@/api/automationApi";
import { useToast } from "@/components/shared/ToastProvider";

/** Fetches all automation rules. */
export function useAutomationRules(params = {}) {
  return useQuery({
    queryKey: ["automation-rules", params],
    queryFn: () => automationApi.getRules(params),
  });
}

/** Fetches the schema (available condition fields / action types) that drives the RuleBuilder UI. */
export function useRuleBuilderSchema() {
  return useQuery({
    queryKey: ["automation-schema"],
    queryFn: () => automationApi.getRuleBuilderSchema(),
    staleTime: Infinity, // schema rarely changes; avoid re-fetching every mount
  });
}

/** Fetches execution logs for a single rule. */
export function useRuleExecutionLogs(ruleId, params = {}) {
  return useQuery({
    queryKey: ["automation-logs", ruleId, params],
    queryFn: () => automationApi.getRuleExecutionLogs(ruleId, params),
    enabled: Boolean(ruleId),
  });
}

function useInvalidateRules() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["automation-rules"] });
}

/** Creates a new automation rule. */
export function useCreateRule() {
  const invalidate = useInvalidateRules();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (payload) => automationApi.createRule(payload),
    onSuccess: () => {
      invalidate();
      toast({ type: "success", message: "Automation rule created." });
    },
    onError: () => toast({ type: "error", message: "Couldn't create rule." }),
  });
}

/** Updates an existing automation rule. */
export function useUpdateRule() {
  const invalidate = useInvalidateRules();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, updates }) => automationApi.updateRule(id, updates),
    onSuccess: () => {
      invalidate();
      toast({ type: "success", message: "Automation rule updated." });
    },
    onError: () => toast({ type: "error", message: "Couldn't update rule." }),
  });
}

/** Toggles a rule's enabled state. */
export function useToggleRuleEnabled() {
  const invalidate = useInvalidateRules();
  return useMutation({
    mutationFn: ({ id, enabled }) => automationApi.setRuleEnabled(id, enabled),
    onSuccess: invalidate,
  });
}

/** Persists a new drag-and-drop rule priority order. */
export function useReorderRules() {
  const invalidate = useInvalidateRules();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (orderedRules) => automationApi.reorderRules(orderedRules),
    onError: () => {
      toast({ type: "error", message: "Couldn't save the new rule order." });
      invalidate();
    },
  });
}

/** Deletes an automation rule. */
export function useDeleteRule() {
  const invalidate = useInvalidateRules();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id) => automationApi.deleteRule(id),
    onSuccess: () => {
      invalidate();
      toast({ type: "success", message: "Rule deleted." });
    },
    onError: () => toast({ type: "error", message: "Couldn't delete rule." }),
  });
}

/** Dry-runs a rule (or draft rule) against recent emails. */
export function useTestRule() {
  const { toast } = useToast();

  return useMutation({
    mutationFn: (payload) => automationApi.testRule(payload),
    onError: () => toast({ type: "error", message: "Test run failed." }),
  });
}