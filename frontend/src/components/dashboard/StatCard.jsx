import * as React from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/**
 * Single metric card for the Dashboard's top stat row
 * (Total Emails, High Priority, Pending Replies, Meetings,
 * Tasks, AI Replies Generated, AI Time Saved).
 *
 * @param {object} props
 * @param {string} props.label
 * @param {string|number} props.value
 * @param {React.ComponentType} props.icon - lucide-react icon component
 * @param {number} [props.trendPercent] - positive = up, negative = down
 * @param {"positive"|"negative"} [props.trendDirection] - which direction counts as "good" for color
 * @param {string} [props.accentColor] - tailwind color token, e.g. "indigo"
 * @param {boolean} [props.isLoading]
 * @param {string} [props.suffix] - e.g. "min" for time-saved
 */
export default function StatCard({
  label,
  value,
  icon: Icon,
  trendPercent,
  trendDirection = "positive",
  accentColor = "indigo",
  isLoading = false,
  suffix,
}) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-5 space-y-3">
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-8 rounded-lg" />
          </div>
          <Skeleton className="h-7 w-16" />
          <Skeleton className="h-3 w-20" />
        </CardContent>
      </Card>
    );
  }

  const hasTrend = typeof trendPercent === "number";
  const isUp = hasTrend && trendPercent > 0;
  const isFlat = hasTrend && trendPercent === 0;
  const isGood = isFlat ? null : trendDirection === "positive" ? isUp : !isUp;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <Card className="overflow-hidden">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            {Icon && (
              <div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-lg",
                  `bg-${accentColor}-100 text-${accentColor}-600`
                )}
              >
                <Icon className="h-4.5 w-4.5" />
              </div>
            )}
          </div>

          <div className="mt-3 flex items-baseline gap-1">
            <span className="text-2xl font-semibold tracking-tight">{value}</span>
            {suffix && <span className="text-sm text-muted-foreground">{suffix}</span>}
          </div>

          {hasTrend && (
            <div className="mt-2 flex items-center gap-1 text-xs">
              {isFlat ? (
                <Minus className="h-3 w-3 text-muted-foreground" />
              ) : isUp ? (
                <ArrowUpRight className={cn("h-3 w-3", isGood ? "text-emerald-600" : "text-red-600")} />
              ) : (
                <ArrowDownRight className={cn("h-3 w-3", isGood ? "text-emerald-600" : "text-red-600")} />
              )}
              <span
                className={cn(
                  "font-medium",
                  isFlat ? "text-muted-foreground" : isGood ? "text-emerald-600" : "text-red-600"
                )}
              >
                {Math.abs(trendPercent)}%
              </span>
              <span className="text-muted-foreground">vs last period</span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}