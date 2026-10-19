import * as React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const PRIORITY_COLORS = {
  high: "#EF4444",
  medium: "#F59E0B",
  low: "#10B981",
};

/**
 * Bar chart of average response time (minutes) broken down by
 * email priority level.
 *
 * @param {object} props
 * @param {{averageResponseTimeMinutes: number, byPriority: {priority: string, avgMinutes: number}[]}} [props.data]
 * @param {boolean} [props.isLoading]
 */
export default function ResponseTimeChart({ data, isLoading }) {
  const byPriority = data?.byPriority ?? [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Response Time by Priority</CardTitle>
        {!isLoading && typeof data?.averageResponseTimeMinutes === "number" && (
          <span className="text-sm text-muted-foreground">
            Avg: <span className="font-medium text-foreground">{data.averageResponseTimeMinutes}m</span>
          </span>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <ResponsiveContainer width="100%" height={256}>
            <BarChart data={byPriority} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis
                dataKey="priority"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 12, fill: "#6B7280", textTransform: "capitalize" }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 12, fill: "#6B7280" }}
                label={{ value: "minutes", angle: -90, position: "insideLeft", fontSize: 11, fill: "#6B7280" }}
              />
              <Tooltip
                formatter={(value) => [`${value} min`, "Avg. response"]}
                contentStyle={{ borderRadius: 8, borderColor: "#E5E7EB", fontSize: 13 }}
              />
              <Bar dataKey="avgMinutes" radius={[6, 6, 0, 0]}>
                {byPriority.map((entry) => (
                  <Cell
                    key={entry.priority}
                    fill={PRIORITY_COLORS[entry.priority?.toLowerCase()] || "#9CA3AF"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}