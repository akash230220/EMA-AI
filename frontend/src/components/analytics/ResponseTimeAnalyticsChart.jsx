import * as React from "react";
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Combo chart (bar + line) showing response time trend over the
 * selected date range, plus a reference line for the period average.
 *
 * @param {object} props
 * @param {object} [props.data] - analyticsApi.getResponseTimeAnalytics() result
 * @param {boolean} [props.isLoading]
 */
export default function ResponseTimeAnalyticsChart({ data, isLoading }) {
  const trend = data?.trend ?? [];
  const average = data?.averageResponseTimeMinutes ?? 0;

  // Attach the average to every point so recharts can render a flat
  // reference line alongside the per-day bars.
  const chartData = React.useMemo(
    () => trend.map((point) => ({ ...point, average })),
    [trend, average]
  );

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Response Time Trend</CardTitle>
        {!isLoading && (
          <span className="text-sm text-muted-foreground">
            Period avg: <span className="font-medium text-foreground">{average}m</span>
          </span>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-72 w-full" />
        ) : (
          <ResponsiveContainer width="100%" height={288}>
            <ComposedChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#6B7280" }} />
              <YAxis
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 12, fill: "#6B7280" }}
                label={{ value: "minutes", angle: -90, position: "insideLeft", fontSize: 11, fill: "#6B7280" }}
              />
              <Tooltip
                formatter={(value, name) => [`${value} min`, name === "average" ? "Period average" : "Avg. response"]}
                contentStyle={{ borderRadius: 8, borderColor: "#E5E7EB", fontSize: 13 }}
              />
              <Legend wrapperStyle={{ fontSize: 13 }} />
              <Bar dataKey="avgMinutes" name="Daily avg." fill="#4F46E5" radius={[4, 4, 0, 0]} barSize={18} />
              <Line
                type="monotone"
                dataKey="average"
                name="Period average"
                stroke="#F59E0B"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}