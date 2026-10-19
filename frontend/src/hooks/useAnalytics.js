import { useQuery, useMutation } from "@tanstack/react-query";
import analyticsApi from "@/api/analyticsApi";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Bundles every Analytics-page query behind a single `range` param,
 * so pages/components just call useAnalytics(range) instead of
 * wiring 7 separate useQuery calls by hand.
 *
 * @param {"today"|"7d"|"30d"|"90d"} range
 */
export function useAnalytics(range = "30d") {
  const summary = useQuery({
    queryKey: ["analytics", "summary", range],
    queryFn: () => analyticsApi.getDashboardSummary({ range }),
  });

  const weeklyActivity = useQuery({
    queryKey: ["analytics", "weekly-activity", range],
    queryFn: () => analyticsApi.getWeeklyActivity({ weeks: range === "7d" ? 1 : range === "30d" ? 4 : 12 }),
  });

  const categoryBreakdown = useQuery({
    queryKey: ["analytics", "category-breakdown", range],
    queryFn: () => analyticsApi.getCategoryBreakdown({ range }),
  });

  const priorityBreakdown = useQuery({
    queryKey: ["analytics", "priority-breakdown", range],
    queryFn: () => analyticsApi.getPriorityBreakdown({ range }),
  });

  const sentimentBreakdown = useQuery({
    queryKey: ["analytics", "sentiment-breakdown", range],
    queryFn: () => analyticsApi.getSentimentBreakdown({ range }),
  });

  const intentBreakdown = useQuery({
    queryKey: ["analytics", "intent-breakdown", range],
    queryFn: () => analyticsApi.getIntentBreakdown({ range }),
  });

  const responseTime = useQuery({
    queryKey: ["analytics", "response-time", range],
    queryFn: () => analyticsApi.getResponseTimeAnalytics({ range }),
  });

  const aiTimeSaved = useQuery({
    queryKey: ["analytics", "ai-time-saved", range],
    queryFn: () => analyticsApi.getAiTimeSavedBreakdown({ range }),
  });

  return {
    summary,
    weeklyActivity,
    categoryBreakdown,
    priorityBreakdown,
    sentimentBreakdown,
    intentBreakdown,
    responseTime,
    aiTimeSaved,
  };
}

/**
 * Fetches monthly trend data (used on the Dashboard, independent of
 * the Analytics page's range filter).
 * @param {number} [months=6]
 */
export function useMonthlyTrends(months = 6) {
  return useQuery({
    queryKey: ["monthly-trends", months],
    queryFn: () => analyticsApi.getMonthlyTrends({ months }),
  });
}

/**
 * Exports the analytics report as a downloadable file and triggers
 * the browser download automatically on success.
 */
export function useExportAnalyticsReport(range) {
  const { toast } = useToast();

  return useMutation({
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
}