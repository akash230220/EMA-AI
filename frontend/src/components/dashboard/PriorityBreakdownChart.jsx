import * as React from "react";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const PRIORITY_COLORS = {
  high: "#EF4444",
  medium: "#F59E0B",
  low: "#10B981",
};

/**
 * Donut chart showing email distribution by AI-assigned priority.
 *
 * @param {object} props
 * @param {{priority: string, count: number, percentage: number}[]} [props.data]
 * @param {boolean} [props.isLoading]
 */
export default function PriorityBreakdownChart({ data = [], isLoading }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Priority Breakdown</CardTitle>
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
                nameKey="priority"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
              >
                {data.map((entry) => (
                  <Cell
                    key={entry.priority}
                    fill={PRIORITY_COLORS[entry.priority?.toLowerCase()] || "#9CA3AF"}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name, item) => [
                  `${value} (${item.payload.percentage}%)`,
                  name,
                ]}
                contentStyle={{ borderRadius: 8, borderColor: "#E5E7EB", fontSize: 13 }}
              />
              <Legend
                wrapperStyle={{ fontSize: 13, textTransform: "capitalize" }}
                formatter={(value) => value}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}