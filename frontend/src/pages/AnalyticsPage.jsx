import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { useMutation } from "@tanstack/react-query";
import AnalyticsFilters from "@/components/analytics/AnalyticsFilters";
import MetricSummaryRow from "@/components/analytics/MetricSummaryRow";
import EmailVolumeChart from "@/components/analytics/EmailVolumeChart";
import CategoryDistributionChart from "@/components/analytics/CategoryDistributionChart";
import SentimentTrendChart from "@/components/analytics/SentimentTrendChart";
import IntentBreakdownChart from "@/components/analytics/IntentBreakdownChart";
import ResponseTimeAnalyticsChart from "@/components/analytics/ResponseTimeAnalyticsChart";
import AiTimeSavedPanel from "@/components/analytics/AiTimeSavedPanel";
import analyticsApi from "@/api/analyticsApi";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Analytics — deep-dive dashboard with a shared date-range filter
 * driving every chart below it.
 */
export default function AnalyticsPage() {
  const { toast } = useToast();
  const [range, setRange] = React.useState("30d");

  const summaryQuery = useQuery({
    queryKey: ["analytics", "summary", range],
    queryFn: () => analyticsApi.getDashboardSummary({ range }),
  });

  const volumeQuery = useQuery({
    queryKey: ["analytics", "volume", range],
    queryFn: () => analyticsApi.getWeeklyActivity({ weeks: range === "7d" ? 1 : range === "30d" ? 4 : 12 }),
  });

  const categoryQuery = useQuery({
    queryKey: ["analytics", "category", range],
    queryFn: () => analyticsApi.getCategoryBreakdown({ range }),
  });

  const sentimentQuery = useQuery({
    queryKey: ["analytics", "sentiment", range],
    queryFn: () => analyticsApi.getSentimentBreakdown({ range }),
  });

  const intentQuery = useQuery({
    queryKey: ["analytics", "intent", range],
    queryFn: () => analyticsApi.getIntentBreakdown({ range }),
  });

  const responseTimeQuery = useQuery({
    queryKey: ["analytics", "response-time", range],
    queryFn: () => analyticsApi.getResponseTimeAnalytics({ range }),
  });

  const timeSavedQuery = useQuery({
    queryKey: ["analytics", "time-saved", range],
    queryFn: () => analyticsApi.getAiTimeSavedBreakdown({ range }),
  });

  const exportMutation = useMutation({
    mutationFn: (format) => analyticsApi.exportAnalyticsReport({ range, format }),
    onSuccess: (blob, format) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `analytics-${range}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    },
    onError: () => toast({ type: "error", message: "Export failed. Please try again." }),
  });

  return (
    <div className="space-y-6">
      <AnalyticsFilters
        range={range}
        onRangeChange={setRange}
        onExport={(format) => exportMutation.mutate(format)}
        isExporting={exportMutation.isPending}
      />

      <MetricSummaryRow summary={summaryQuery.data} isLoading={summaryQuery.isLoading} />

      <EmailVolumeChart data={volumeQuery.data} isLoading={volumeQuery.isLoading} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <CategoryDistributionChart data={categoryQuery.data} isLoading={categoryQuery.isLoading} />
        <IntentBreakdownChart data={intentQuery.data} isLoading={intentQuery.isLoading} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <SentimentTrendChart data={sentimentQuery.data} isLoading={sentimentQuery.isLoading} />
        <ResponseTimeAnalyticsChart data={responseTimeQuery.data} isLoading={responseTimeQuery.isLoading} />
      </div>

      <AiTimeSavedPanel data={timeSavedQuery.data} isLoading={timeSavedQuery.isLoading} />
    </div>
  );
}