import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import analyticsApi from "@/api/analyticsApi";
import emailApi from "@/api/emailApi";
import meetingApi from "@/api/meetingApi";
import StatCardGrid from "@/components/dashboard/StatCardGrid";
import WeeklyActivityChart from "@/components/dashboard/WeeklyActivityChart";
import MonthlyTrendChart from "@/components/dashboard/MonthlyTrendChart";
import PriorityBreakdownChart from "@/components/dashboard/PriorityBreakdownChart";
import ResponseTimeChart from "@/components/dashboard/ResponseTimeChart";
import RecentEmailsWidget from "@/components/dashboard/RecentEmailsWidget";
import UpcomingMeetingsWidget from "@/components/dashboard/UpcomingMeetingsWidget";
import PageHeader from "@/components/shared/PageHeader";

/**
 * Dashboard — the app's home page. Aggregates summary stats,
 * activity/trend charts, and quick-glance widgets for recent
 * emails and upcoming meetings.
 */
export default function DashboardPage() {
  const summaryQuery = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => analyticsApi.getDashboardSummary(),
  });

  const weeklyActivityQuery = useQuery({
    queryKey: ["weekly-activity"],
    queryFn: () => analyticsApi.getWeeklyActivity({ weeks: 1 }),
  });

  const monthlyTrendsQuery = useQuery({
    queryKey: ["monthly-trends"],
    queryFn: () => analyticsApi.getMonthlyTrends({ months: 6 }),
  });

  const priorityBreakdownQuery = useQuery({
    queryKey: ["priority-breakdown", "30d"],
    queryFn: () => analyticsApi.getPriorityBreakdown({ range: "30d" }),
  });

  const responseTimeQuery = useQuery({
    queryKey: ["response-time", "30d"],
    queryFn: () => analyticsApi.getResponseTimeAnalytics({ range: "30d" }),
  });

  const recentEmailsQuery = useQuery({
    queryKey: ["emails", "recent"],
    queryFn: () => emailApi.getEmails({ page: 1, pageSize: 5, sortBy: "date", sortOrder: "desc" }),
  });

  const upcomingMeetingsQuery = useQuery({
    queryKey: ["meetings", "upcoming"],
    queryFn: () => meetingApi.getUpcomingMeetings({ days: 7 }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Your inbox at a glance, powered by AI."
      />

      <StatCardGrid summary={summaryQuery.data} isLoading={summaryQuery.isLoading} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <WeeklyActivityChart data={weeklyActivityQuery.data} isLoading={weeklyActivityQuery.isLoading} />
        <MonthlyTrendChart data={monthlyTrendsQuery.data} isLoading={monthlyTrendsQuery.isLoading} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <PriorityBreakdownChart data={priorityBreakdownQuery.data} isLoading={priorityBreakdownQuery.isLoading} />
        <ResponseTimeChart data={responseTimeQuery.data} isLoading={responseTimeQuery.isLoading} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <RecentEmailsWidget emails={recentEmailsQuery.data?.items} isLoading={recentEmailsQuery.isLoading} />
        <UpcomingMeetingsWidget meetings={upcomingMeetingsQuery.data} isLoading={upcomingMeetingsQuery.isLoading} />
      </div>
    </div>
  );
}