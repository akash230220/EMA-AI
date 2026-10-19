import * as React from "react";
import { Sparkles, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Transparency panel breaking down the aggregate "AI time saved"
 * figure into its contributing activities (auto-replies, summaries,
 * categorization, etc.), so the number doesn't feel like a black box.
 *
 * @param {object} props
 * @param {object} [props.data] - analyticsApi.getAiTimeSavedBreakdown() result
 * @param {boolean} [props.isLoading]
 */
export default function AiTimeSavedPanel({ data, isLoading }) {
  const breakdown = data?.breakdown ?? [];
  const total = data?.totalMinutesSaved ?? 0;
  const maxMinutes = Math.max(...breakdown.map((b) => b.minutesSaved), 1);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-1.5 text-base">
          <Sparkles className="h-4 w-4 text-indigo-600" />
          AI Time Saved
        </CardTitle>
        <span className="flex items-center gap-1 text-sm font-semibold text-emerald-600">
          <Clock className="h-3.5 w-3.5" />
          {total} min
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        {breakdown.length === 0 ? (
          <p className="text-sm text-muted-foreground">No activity recorded for this period.</p>
        ) : (
          breakdown.map((item) => (
            <div key={item.activity}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-foreground">{item.activity}</span>
                <span className="text-muted-foreground">{item.minutesSaved} min</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
                  style={{ width: `${(item.minutesSaved / maxMinutes) * 100}%` }}
                />
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}