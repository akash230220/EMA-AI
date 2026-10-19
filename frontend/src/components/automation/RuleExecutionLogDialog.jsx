import * as React from "react";
import { Mail, CheckCircle2, XCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

/**
 * Modal showing execution history for a single automation rule —
 * which emails it fired on, what actions were taken, and whether
 * each execution succeeded. Backed by
 * automationApi.getRuleExecutionLogs(ruleId).
 *
 * @param {object} props
 * @param {boolean} props.open
 * @param {(open: boolean) => void} props.onOpenChange
 * @param {string} [props.ruleName]
 * @param {object[]} [props.logs]
 * @param {boolean} [props.isLoading]
 */
export default function RuleExecutionLogDialog({ open, onOpenChange, ruleName, logs = [], isLoading }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[75vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Execution History{ruleName ? ` — ${ruleName}` : ""}</DialogTitle>
        </DialogHeader>

        <div className="space-y-2">
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)
          ) : logs.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              This rule hasn't fired on any emails yet.
            </p>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className="flex items-start gap-3 rounded-md border border-border p-3"
              >
                {log.success ? (
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                ) : (
                  <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 text-sm">
                    <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="truncate font-medium">{log.emailSubject}</span>
                  </div>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {log.actionsPerformedLabel} &middot; {log.executedAtLabel}
                  </p>
                  {!log.success && log.errorMessage && (
                    <Badge variant="destructive" className="mt-1 text-[10px]">
                      {log.errorMessage}
                    </Badge>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}