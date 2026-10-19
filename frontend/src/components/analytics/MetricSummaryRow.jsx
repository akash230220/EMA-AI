import * as React from "react";
import { Mail, Clock, Sparkles, Timer } from "lucide-react";
import StatCard from "@/components/dashboard/StatCard";

/**
 * Compact metric row at the top of the Analytics page — reuses the
 * same StatCard used on the Dashboard, but scoped to the selected
 * date range and focused on trend-relevant numbers rather than the
 * full dashboard set.
 *
 * @param {object} props
 * @param {object} [props.summary] - analyticsApi.getDashboardSummary({ range })
 * @param {boolean} [props.isLoading]
 */
export default function MetricSummaryRow({ summary, isLoading }) {
  const cards = [
    { label: "Total Emails", value: summary?.totalEmails ?? 0, icon: Mail, accentColor: "indigo" },
    {
      label: "Avg. Response Time",
      value: summary?.avgResponseTimeMinutes ?? 0,
      suffix: "min",
      icon: Clock,
      accentColor: "amber",
    },
    {
      label: "AI Replies Generated",
      value: summary?.aiRepliesGenerated ?? 0,
      icon: Sparkles,
      accentColor: "emerald",
    },
    {
      label: "AI Time Saved",
      value: summary?.aiTimeSavedMinutes ?? 0,
      suffix: "min",
      icon: Timer,
      accentColor: "teal",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {cards.map((card) => (
        <StatCard key={card.label} {...card} isLoading={isLoading} />
      ))}
    </div>
  );
}