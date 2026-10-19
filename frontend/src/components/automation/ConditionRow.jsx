import * as React from "react";
import { X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/**
 * Single condition row inside the rule builder: field + operator +
 * value. Field/operator options come from
 * automationApi.getRuleBuilderSchema() so the UI always matches what
 * the backend Automation Agent actually supports.
 *
 * @param {object} props
 * @param {object} props.condition - { field, operator, value }
 * @param {{field: string, label: string, operators: string[], valueType: string}[]} props.fieldSchema
 * @param {(updates: object) => void} props.onChange
 * @param {() => void} props.onRemove
 * @param {boolean} [props.canRemove]
 */
export default function ConditionRow({ condition, fieldSchema, onChange, onRemove, canRemove }) {
  const selectedFieldDef = fieldSchema.find((f) => f.field === condition.field);
  const availableOperators = selectedFieldDef?.operators || ["equals"];

  return (
    <div className="flex items-center gap-2">
      <Select value={condition.field} onValueChange={(v) => onChange({ field: v, operator: undefined, value: "" })}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Field" />
        </SelectTrigger>
        <SelectContent>
          {fieldSchema.map((f) => (
            <SelectItem key={f.field} value={f.field}>
              {f.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={condition.operator} onValueChange={(v) => onChange({ operator: v })}>
        <SelectTrigger className="w-36">
          <SelectValue placeholder="Operator" />
        </SelectTrigger>
        <SelectContent>
          {availableOperators.map((op) => (
            <SelectItem key={op} value={op} className="capitalize">
              {op.replace(/_/g, " ")}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Input
        value={condition.value}
        onChange={(e) => onChange({ value: e.target.value })}
        placeholder="Value"
        className="flex-1"
      />

      {canRemove && (
        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={onRemove}>
          <X className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );
}