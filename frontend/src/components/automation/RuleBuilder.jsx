import * as React from "react";
import { Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import ConditionRow from "./ConditionRow";
import ActionRow from "./ActionRow";
import RuleTestPreview from "./RuleTestPreview";

const EMPTY_CONDITION = { field: "", operator: "", value: "" };
const EMPTY_ACTION = { type: "", value: "" };

/**
 * Full rule builder modal — create or edit an automation rule with
 * multiple conditions (AND/OR), multiple actions, and a live dry-run
 * test panel. Schema (available fields/operators/actions) is fetched
 * from automationApi.getRuleBuilderSchema() by the parent and passed
 * in as `fieldSchema`/`actionSchema`.
 *
 * @param {object} props
 * @param {boolean} props.open
 * @param {(open: boolean) => void} props.onOpenChange
 * @param {object|null} [props.initialRule]
 * @param {{field: string, label: string, operators: string[], valueType: string}[]} props.fieldSchema
 * @param {{type: string, label: string, requiresValue: boolean}[]} props.actionSchema
 * @param {(payload: object) => void} props.onSubmit
 * @param {boolean} [props.isSubmitting]
 * @param {(payload: object) => void} props.onRunTest
 * @param {boolean} [props.isTesting]
 * @param {{matchedCount: number, sampleMatches: object[]}|null} [props.testResult]
 */
export default function RuleBuilder({
  open,
  onOpenChange,
  initialRule,
  fieldSchema = [],
  actionSchema = [],
  onSubmit,
  isSubmitting,
  onRunTest,
  isTesting,
  testResult,
}) {
  const isEditing = Boolean(initialRule);

  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [conditionLogic, setConditionLogic] = React.useState("AND");
  const [conditions, setConditions] = React.useState([EMPTY_CONDITION]);
  const [actions, setActions] = React.useState([EMPTY_ACTION]);

  React.useEffect(() => {
    if (open) {
      setName(initialRule?.name || "");
      setDescription(initialRule?.description || "");
      setConditionLogic(initialRule?.conditionLogic || "AND");
      setConditions(initialRule?.conditions?.length ? initialRule.conditions : [EMPTY_CONDITION]);
      setActions(initialRule?.actions?.length ? initialRule.actions : [EMPTY_ACTION]);
    }
  }, [open, initialRule]);

  const updateCondition = (index, updates) => {
    setConditions((prev) => prev.map((c, i) => (i === index ? { ...c, ...updates } : c)));
  };
  const removeCondition = (index) => {
    setConditions((prev) => prev.filter((_, i) => i !== index));
  };
  const addCondition = () => setConditions((prev) => [...prev, { ...EMPTY_CONDITION }]);

  const updateAction = (index, updates) => {
    setActions((prev) => prev.map((a, i) => (i === index ? { ...a, ...updates } : a)));
  };
  const removeAction = (index) => {
    setActions((prev) => prev.filter((_, i) => i !== index));
  };
  const addAction = () => setActions((prev) => [...prev, { ...EMPTY_ACTION }]);

  const isValid =
    name.trim() &&
    conditions.every((c) => c.field && c.operator && c.value) &&
    actions.every((a) => a.type);

  const buildPayload = () => ({
    name: name.trim(),
    description: description.trim() || undefined,
    conditionLogic,
    conditions,
    actions,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isValid) return;
    onSubmit(buildPayload());
  };

  const handleTest = () => {
    onRunTest({ conditions, conditionLogic, sampleSize: 50 });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Automation Rule" : "New Automation Rule"}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <Label htmlFor="rule-name">Rule name</Label>
            <Input
              id="rule-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Auto-archive newsletters"
              autoFocus
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="rule-description">Description</Label>
            <Textarea
              id="rule-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional notes about what this rule does"
              className="min-h-[60px]"
            />
          </div>

          {/* Conditions */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Conditions</Label>
              {conditions.length > 1 && (
                <Select value={conditionLogic} onValueChange={setConditionLogic}>
                  <SelectTrigger className="w-24 h-7 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="AND">Match ALL</SelectItem>
                    <SelectItem value="OR">Match ANY</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="space-y-2">
              {conditions.map((condition, i) => (
                <ConditionRow
                  key={i}
                  condition={condition}
                  fieldSchema={fieldSchema}
                  onChange={(updates) => updateCondition(i, updates)}
                  onRemove={() => removeCondition(i)}
                  canRemove={conditions.length > 1}
                />
              ))}
            </div>

            <Button type="button" variant="ghost" size="sm" onClick={addCondition} className="text-xs">
              <Plus className="h-3.5 w-3.5" />
              Add condition
            </Button>
          </div>

          {/* Actions */}
          <div className="space-y-2">
            <Label>Then perform these actions</Label>
            <div className="space-y-2">
              {actions.map((action, i) => (
                <ActionRow
                  key={i}
                  action={action}
                  actionSchema={actionSchema}
                  onChange={(updates) => updateAction(i, updates)}
                  onRemove={() => removeAction(i)}
                  canRemove={actions.length > 1}
                />
              ))}
            </div>

            <Button type="button" variant="ghost" size="sm" onClick={addAction} className="text-xs">
              <Plus className="h-3.5 w-3.5" />
              Add action
            </Button>
          </div>

          {/* Dry-run test */}
          <RuleTestPreview onRunTest={handleTest} isTesting={isTesting} result={testResult} />

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || isSubmitting}>
              {isSubmitting ? "Saving..." : isEditing ? "Save changes" : "Create rule"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}