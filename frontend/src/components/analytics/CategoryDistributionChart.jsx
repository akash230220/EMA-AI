import * as React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const CATEGORY_COLORS = [
  "#4F46E5", "#7C3AED", "#EC4899", "#F59E0B", "#10B981", "#06B6D4", "#8B5CF6",
];

/**
 * Horizontal bar chart of email volume by AI-assigned category.
 *
 * @param {object} props
 * @param {{category: string, count: number, percentage: number}[]} [props.data]
 * @param {boolean} [props.isLoading]
 */
export default function CategoryDistributionChart({ data = [], isLoading }) {
  const sorted = React.useMemo(() => [...data].sort((a, b) => b.count - a.count), [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Category Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-72 w-full" />
        ) : sorted.length === 0 ? (
          <div className="flex h-72 items-center justify-center text-sm text-muted-foreground">
            No data available for this period
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={288}>
            <BarChart data={sorted} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
              <XAxis type="number" tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#6B7280" }} />
              <YAxis
                type="category"
                dataKey="category"
                tickLine={false}
                axisLine={false}
                width={100}
                tick={{ fontSize: 12, fill: "#6B7280", textTransform: "capitalize" }}
              />
              <Tooltip
                formatter={(value, name, item) => [`${value} (${item.payload.percentage}%)`, "Emails"]}
                contentStyle={{ borderRadius: 8, borderColor: "#E5E7EB", fontSize: 13 }}
              />
              <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={20}>
                {sorted.map((entry, i) => (
                  <Cell key={entry.category} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}