import * as React from "react";
import { Download, Loader2 } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";

const RANGE_OPTIONS = [
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "90d", label: "Last 90 days" },
];

/**
 * Top toolbar for the Analytics page: date-range selector +
 * export button (CSV/PDF via analyticsApi.exportAnalyticsReport).
 *
 * @param {object} props
 * @param {string} props.range - "7d" | "30d" | "90d"
 * @param {(range: string) => void} props.onRangeChange
 * @param {(format: "csv"|"pdf") => void} props.onExport
 * @param {boolean} [props.isExporting]
 */
export default function AnalyticsFilters({ range, onRangeChange, onExport, isExporting }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Insights into your email activity and AI performance
        </p>
      </div>

      <div className="flex items-center gap-2">
        <Select value={range} onValueChange={onRangeChange}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {RANGE_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button variant="outline" onClick={() => onExport("csv")} disabled={isExporting}>
          {isExporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          Export CSV
        </Button>
      </div>
    </div>
  );
}