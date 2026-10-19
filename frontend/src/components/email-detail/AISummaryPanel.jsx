import * as React from "react";
import {
  Sparkles,
  RefreshCw,
  Tag,
  AlertTriangle,
  Smile,
  Meh,
  Frown,
  Target,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const PRIORITY_VARIANT = { high: "destructive", medium: "warning", low: "success" };

const SENTIMENT_CONFIG = {
  positive: { icon: Smile, color: "text-emerald-600 bg-emerald-50" },
  neutral: { icon: Meh, color: "text-gray-600 bg-gray-100" },
  negative: { icon: Frown, color: "text-red-600 bg-red-50" },
};

/**
 * Right-rail panel showing all AI-derived insights for the currently
 * open email: summary, category, priority, intent, sentiment, and a
 * "re-run AI" action wired to emailApi.reprocessEmail().
 *
 * @param {object} props
 * @param {object} props.email
 * @param {boolean} [props.isLoading]
 * @param {boolean} [props.isReprocessing]
 * @param {() => void} props.onReprocess
 */
export default function AISummaryPanel({ email, isLoading, isReprocessing, onReprocess }) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>
    );
  }

  const SentimentIcon = SENTIMENT_CONFIG[email?.sentiment]?.icon || Meh;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-1.5 text-base">
          <Sparkles className="h-4 w-4 text-indigo-600" />
          AI Insights
        </CardTitle>
        <Button
          variant="ghost"
          size="sm"
          onClick={onReprocess}
          disabled={isReprocessing}
          className="h-7 px-2 text-xs"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", isReprocessing && "animate-spin")} />
          {isReprocessing ? "Analyzing..." : "Re-analyze"}
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Summary */}
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Summary
          </p>
          <p className="text-sm leading-relaxed text-foreground">
            {email?.aiSummary || "No summary generated yet."}
          </p>
        </div>

        {/* Category / Priority / Intent chips */}
        <div className="flex flex-wrap gap-1.5">
          {email?.category && (
            <Badge variant="secondary" className="gap-1 capitalize">
              <Tag className="h-3 w-3" />
              {email.category}
            </Badge>
          )}
          {email?.priority && (
            <Badge variant={PRIORITY_VARIANT[email.priority] || "outline"} className="gap-1 capitalize">
              <AlertTriangle className="h-3 w-3" />
              {email.priority} priority
            </Badge>
          )}
          {email?.intent && (
            <Badge variant="outline" className="gap-1 capitalize">
              <Target className="h-3 w-3" />
              {email.intent.replace(/_/g, " ")}
            </Badge>
          )}
        </div>

        {/* Sentiment */}
        {email?.sentiment && (
          <div className="flex items-center gap-2 rounded-md border border-border p-2.5">
            <div className={cn("flex h-7 w-7 items-center justify-center rounded-full", SENTIMENT_CONFIG[email.sentiment]?.color)}>
              <SentimentIcon className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs font-medium capitalize">{email.sentiment} sentiment</p>
              <p className="text-[11px] text-muted-foreground">Detected by Sentiment Agent</p>
            </div>
          </div>
        )}

        {/* Key points extracted */}
        {email?.aiKeyPoints?.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Key Points
            </p>
            <ul className="space-y-1">
              {email.aiKeyPoints.map((point, i) => (
                <li key={i} className="flex gap-2 text-sm text-foreground">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-muted-foreground" />
                  {point}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}