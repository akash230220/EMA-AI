import * as React from "react";
import { Plus, ListFilter } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/**
 * Toolbar above the Task Board: priority/source filters + the
 * "New Task" action that opens TaskFormDialog.
 *
 * @param {object} props
 * @param {object} props.filters
 * @param {(filters: object) => void} props.onFiltersChange
 * @param {() => void} props.onCreateTask
 */
export default function TaskFilters({ filters, onFiltersChange }) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <ListFilter className="h-4 w-4 text-muted-foreground" />

      <Select
        value={filters.priority || "all"}
        onValueChange={(v) => onFiltersChange({ ...filters, priority: v === "all" ? undefined : v })}
      >
        <SelectTrigger className="w-32">
          <SelectValue placeholder="Priority" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All priority</SelectItem>
          <SelectItem value="high">High</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="low">Low</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.source || "all"}
        onValueChange={(v) => onFiltersChange({ ...filters, source: v === "all" ? undefined : v })}
      >
        <SelectTrigger className="w-36">
          <SelectValue placeholder="Source" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All sources</SelectItem>
          <SelectItem value="ai_extracted">AI-extracted</SelectItem>
          <SelectItem value="manual">Manual</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}