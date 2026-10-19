import * as React from "react";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const INTENT_COLORS = {
  meeting_request: "#4F46E5",
  task: "#7C3AED",
  fyi: "#9CA3AF",
  follow_up: "#F59E0B",
  urgent_action: "#EF4444",
  question: "#06B6D4",
};

/**
 * Donut chart of email distribution by AI-detected intent
 * (meeting_request, task, fyi, follow_up, urgent_action, question).
 *
 * @param {object} props
 * @param {{intent: string, count: number, percentage: number}[]} [props.data]
 * @param {boolean} [props.isLoading]
 */
export default function IntentBreakdownChart({ data = [], isLoading }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Intent Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : data.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
            No data available for this period
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={256}>
            <PieChart>
              <Pie
                data={data}
                dataKey="count"
                nameKey="intent"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={2}
              >
                {data.map((entry) => (
                  <Cell key={entry.intent} fill={INTENT_COLORS[entry.intent] || "#9CA3AF"} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name, item) => [`${value} (${item.payload.percentage}%)`, formatIntentLabel(name)]}
                contentStyle={{ borderRadius: 8, borderColor: "#E5E7EB", fontSize: 13 }}
              />
              <Legend
                wrapperStyle={{ fontSize: 12 }}
                formatter={(value) => formatIntentLabel(value)}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

function formatIntentLabel(value) {
  return String(value).replace(/_/g, " ");
}