import * as React from "react";
import {
  Mail,
  AlertTriangle,
  Clock,
  CalendarClock,
  CheckSquare,
  Sparkles,
  Timer,
} from "lucide-react";
import StatCard from "./StatCard";

/**
 * Renders the full row of Dashboard stat cards from a single
 * getDashboardSummary() response shape. Handles loading state
 * by passing isLoading through to each card.
 *
 * @param {object} props
 * @param {object} [props.summary] - result of analyticsApi.getDashboardSummary()
 * @param {boolean} [props.isLoading]
 */
export default function StatCardGrid({ summary, isLoading }) {
  const cards = [
    {
      label: "Total Emails",
      value: summary?.totalEmails ?? 0,
      icon: Mail,
      accentColor: "indigo",
    },
    {
      label: "High Priority",
      value: summary?.highPriorityEmails ?? 0,
      icon: AlertTriangle,
      accentColor: "red",
    },
    {
      label: "Pending Replies",
      value: summary?.pendingReplies ?? 0,
      icon: Clock,
      accentColor: "amber",
    },
    {
      label: "Meetings",
      value: summary?.meetings ?? 0,
      icon: CalendarClock,
      accentColor: "blue",
    },
    {
      label: "Tasks",
      value: summary?.tasks ?? 0,
      icon: CheckSquare,
      accentColor: "violet",
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
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
      {cards.map((card) => (
        <StatCard key={card.label} {...card} isLoading={isLoading} />
      ))}
    </div>
  );
}