import * as React from "react";
import { PlayCircle, Loader2, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

/**
 * Dry-run preview panel inside the rule builder — lets the user test
 * their in-progress rule against recent emails before saving, via
 * automationApi.testRule(). Critical for avoiding silent, unwanted
 * bulk actions (e.g. accidentally archiving important emails).
 *
 * @param {object} props
 * @param {() => void} props.onRunTest
 * @param {boolean} props.isTesting
 * @param {{matchedCount: number, sampleMatches: object[]}|null} props.result
 */
export default function RuleTestPreview({ onRunTest, isTesting, result }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">Test this rule</p>
          <p className="text-xs text-muted-foreground">
            See which recent emails would match before saving.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onRunTest} disabled={isTesting}>
          {isTesting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <PlayCircle className="h-3.5 w-3.5" />}
          {isTesting ? "Testing..." : "Run test"}
        </Button>
      </div>

      {result && (
        <div className="mt-3 space-y-2">
          <p className="text-xs">
            <span className="font-semibold text-foreground">{result.matchedCount}</span>{" "}
            <span className="text-muted-foreground">
              email{result.matchedCount === 1 ? "" : "s"} would match this rule
            </span>
          </p>

          {result.sampleMatches?.length > 0 && (
            <div className="space-y-1.5">
              {result.sampleMatches.slice(0, 5).map((email) => (
                <Card key={email.id} className="shadow-none">
                  <CardContent className="flex items-center gap-2 p-2.5">
                    <Mail className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                    <span className="min-w-0 flex-1 truncate text-xs">{email.subject}</span>
                    <Badge variant="outline" className="shrink-0 text-[10px] px-1.5 py-0">
                      {email.senderName}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}