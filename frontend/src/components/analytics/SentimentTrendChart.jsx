import * as React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const SENTIMENT_COLORS = {
  positive: "#10B981",
  neutral: "#9CA3AF",
  negative: "#EF4444",
};

/**
 * Line chart tracking sentiment distribution over time (percentage
 * of emails per sentiment, per day/week within the selected range).
 *
 * @param {object} props
 * @param {{date: string, positive: number, neutral: number, negative: number}[]} [props.data]
 * @param {boolean} [props.isLoading]
 */
export default function SentimentTrendChart({ data = [], isLoading }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Sentiment Trend</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-72 w-full" />
        ) : (
          <ResponsiveContainer width="100%" height={288}>
            <LineChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#6B7280" }} />
              <YAxis
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 12, fill: "#6B7280" }}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                formatter={(value) => [`${value}%`, undefined]}
                contentStyle={{ borderRadius: 8, borderColor: "#E5E7EB", fontSize: 13 }}
              />
              <Legend wrapperStyle={{ fontSize: 13, textTransform: "capitalize" }} />
              <Line type="monotone" dataKey="positive" stroke={SENTIMENT_COLORS.positive} strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="neutral" stroke={SENTIMENT_COLORS.neutral} strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="negative" stroke={SENTIMENT_COLORS.negative} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}