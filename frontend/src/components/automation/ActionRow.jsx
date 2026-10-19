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
 * Single action row inside the rule builder: action type + optional
 * value (e.g. label name, forward-to email).
 *
 * @param {object} props
 * @param {object} props.action - { type, value? }
 * @param {{type: string, label: string, requiresValue: boolean}[]} props.actionSchema
 * @param {(updates: object) => void} props.onChange
 * @param {() => void} props.onRemove
 * @param {boolean} [props.canRemove]
 */
export default function ActionRow({ action, actionSchema, onChange, onRemove, canRemove }) {
  const selectedActionDef = actionSchema.find((a) => a.type === action.type);

  return (
    <div className="flex items-center gap-2">
      <Select value={action.type} onValueChange={(v) => onChange({ type: v, value: "" })}>
        <SelectTrigger className="w-48">
          <SelectValue placeholder="Action" />
        </SelectTrigger>
        <SelectContent>
          {actionSchema.map((a) => (
            <SelectItem key={a.type} value={a.type}>
              {a.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {selectedActionDef?.requiresValue && (
        <Input
          value={action.value || ""}
          onChange={(e) => onChange({ value: e.target.value })}
          placeholder={selectedActionDef.type === "forward" ? "Email address" : "Value"}
          className="flex-1"
        />
      )}

      {canRemove && (
        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={onRemove}>
          <X className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );
}