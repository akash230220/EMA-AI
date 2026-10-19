import * as React from "react";
import { ListFilter } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/**
 * Toolbar above the meetings list: status/source filters.
 *
 * @param {object} props
 * @param {object} props.filters
 * @param {(filters: object) => void} props.onFiltersChange
 */
export default function MeetingFilters({ filters, onFiltersChange }) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <ListFilter className="h-4 w-4 text-muted-foreground" />

      <Select
        value={filters.status || "all"}
        onValueChange={(v) => onFiltersChange({ ...filters, status: v === "all" ? undefined : v })}
      >
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All statuses</SelectItem>
          <SelectItem value="detected">Needs review</SelectItem>
          <SelectItem value="confirmed">Confirmed</SelectItem>
          <SelectItem value="synced">Synced</SelectItem>
          <SelectItem value="declined">Declined</SelectItem>
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
          <SelectItem value="ai_detected">AI-detected</SelectItem>
          <SelectItem value="manual">Manual</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}