import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import PageHeader from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import RuleList from "@/components/automation/RuleList";
import RuleBuilder from "@/components/automation/RuleBuilder";
import RuleExecutionLogDialog from "@/components/automation/RuleExecutionLogDialog";
import ConfirmDialog from "@/components/shared/ConfirmDialog";
import automationApi from "@/api/automationApi";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Automation Rules — manage AI automation rules (trigger -> condition
 * -> action), including a schema-driven builder with dry-run testing.
 */
export default function AutomationRulesPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [builderOpen, setBuilderOpen] = React.useState(false);
  const [editingRule, setEditingRule] = React.useState(null);
  const [deleteTargetId, setDeleteTargetId] = React.useState(null);
  const [logsTargetRule, setLogsTargetRule] = React.useState(null);
  const [testResult, setTestResult] = React.useState(null);

  const rulesQuery = useQuery({
    queryKey: ["automation-rules"],
    queryFn: () => automationApi.getRules(),
  });

  const schemaQuery = useQuery({
    queryKey: ["automation-schema"],
    queryFn: () => automationApi.getRuleBuilderSchema(),
    staleTime: Infinity,
  });

  const logsQuery = useQuery({
    queryKey: ["automation-logs", logsTargetRule?.id],
    queryFn: () => automationApi.getRuleExecutionLogs(logsTargetRule.id),
    enabled: Boolean(logsTargetRule),
  });

  const invalidateRules = () => queryClient.invalidateQueries({ queryKey: ["automation-rules"] });

  const toggleEnabledMutation = useMutation({
    mutationFn: ({ id, enabled }) => automationApi.setRuleEnabled(id, enabled),
    onSuccess: invalidateRules,
  });

  const reorderMutation = useMutation({
    mutationFn: (orderedRules) => automationApi.reorderRules(orderedRules),
    onError: () => {
      toast({ type: "error", message: "Couldn't save the new rule order." });
      invalidateRules();
    },
  });

  const createMutation = useMutation({
    mutationFn: (payload) => automationApi.createRule(payload),
    onSuccess: () => {
      invalidateRules();
      toast({ type: "success", message: "Automation rule created." });
      setBuilderOpen(false);
      setTestResult(null);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }) => automationApi.updateRule(id, updates),
    onSuccess: () => {
      invalidateRules();
      toast({ type: "success", message: "Automation rule updated." });
      setBuilderOpen(false);
      setEditingRule(null);
      setTestResult(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => automationApi.deleteRule(id),
    onSuccess: () => {
      invalidateRules();
      toast({ type: "success", message: "Rule deleted." });
      setDeleteTargetId(null);
    },
  });

  const testMutation = useMutation({
    mutationFn: (payload) => automationApi.testRule(payload),
    onSuccess: (data) => setTestResult(data),
    onError: () => toast({ type: "error", message: "Test run failed." }),
  });

  const handleFormSubmit = (payload) => {
    if (editingRule) {
      updateMutation.mutate({ id: editingRule.id, updates: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const rules = rulesQuery.data?.items || [];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Automation Rules"
        description="Automatically archive, label, or forward emails based on AI-detected conditions."
        actions={
          <Button onClick={() => { setEditingRule(null); setTestResult(null); setBuilderOpen(true); }}>
            <Plus className="h-4 w-4" />
            New Rule
          </Button>
        }
      />

      <RuleList
        rules={rules}
        isLoading={rulesQuery.isLoading}
        onCreateRule={() => { setEditingRule(null); setTestResult(null); setBuilderOpen(true); }}
        onToggleEnabled={(id, enabled) => toggleEnabledMutation.mutate({ id, enabled })}
        onEdit={(id) => {
          setEditingRule(rules.find((r) => r.id === id));
          setTestResult(null);
          setBuilderOpen(true);
        }}
        onDelete={(id) => setDeleteTargetId(id)}
        onViewLogs={(id) => setLogsTargetRule(rules.find((r) => r.id === id))}
        onReorder={(orderedRules) => reorderMutation.mutate(orderedRules)}
      />

      <RuleBuilder
        open={builderOpen}
        onOpenChange={setBuilderOpen}
        initialRule={editingRule}
        fieldSchema={schemaQuery.data?.conditionFields || []}
        actionSchema={schemaQuery.data?.actionTypes || []}
        onSubmit={handleFormSubmit}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
        onRunTest={(payload) => testMutation.mutate(payload)}
        isTesting={testMutation.isPending}
        testResult={testResult}
      />

      <RuleExecutionLogDialog
        open={Boolean(logsTargetRule)}
        onOpenChange={(open) => !open && setLogsTargetRule(null)}
        ruleName={logsTargetRule?.name}
        logs={logsQuery.data?.items}
        isLoading={logsQuery.isLoading}
      />

      <ConfirmDialog
        open={Boolean(deleteTargetId)}
        onOpenChange={(open) => !open && setDeleteTargetId(null)}
        title="Delete this automation rule?"
        description="Emails will no longer be processed by this rule. This cannot be undone."
        confirmLabel="Delete"
        onConfirm={() => deleteMutation.mutate(deleteTargetId)}
        isConfirming={deleteMutation.isPending}
      />
    </div>
  );
}