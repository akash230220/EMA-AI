import * as React from "react";
import {
  AreaChart,
  Area,
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
 * Full-width email volume trend chart for the Analytics page —
 * same shape as the Dashboard's WeeklyActivityChart but scoped to
 * the selected date range (7d/30d/90d) rather than fixed to a week.
 *
 * @param {object} props
 * @param {{date: string, received: number, replied: number}[]} [props.data]
 * @param {boolean} [props.isLoading]
 */
export default function EmailVolumeChart({ data = [], isLoading }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Email Volume</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-80 w-full" />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="volReceivedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4F46E5" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#4F46E5" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="volRepliedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10B981" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#6B7280" }} />
              <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#6B7280" }} />
              <Tooltip contentStyle={{ borderRadius: 8, borderColor: "#E5E7EB", fontSize: 13 }} />
              <Legend wrapperStyle={{ fontSize: 13 }} />
              <Area type="monotone" dataKey="received" name="Received" stroke="#4F46E5" fill="url(#volReceivedGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="replied" name="Replied" stroke="#10B981" fill="url(#volRepliedGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}