import * as React from "react";
import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Inbox,
  Sparkles,
  MessageSquareText,
  CheckSquare,
  CalendarClock,
  BarChart3,
  Zap,
  Settings,
  ChevronsLeft,
  ChevronsRight,
  Mail,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/**
 * Primary navigation config. Centralized here so adding a new page
 * only requires one entry — Topbar's mobile nav can reuse this too.
 */
export const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/reply-center", label: "AI Reply Center", icon: Sparkles },
  { to: "/copilot", label: "Copilot Chat", icon: MessageSquareText },
  { to: "/tasks", label: "Tasks", icon: CheckSquare },
  { to: "/meetings", label: "Meetings", icon: CalendarClock },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/automation", label: "Automation Rules", icon: Zap },
  { to: "/settings", label: "Settings", icon: Settings },
];

/**
 * Collapsible desktop sidebar. Collapsed state persists to localStorage
 * so the layout doesn't "jump" on reload. Fully keyboard/tooltip
 * accessible when collapsed (icons only).
 */
export default function Sidebar({ collapsed, onToggleCollapsed }) {
  return (
    <TooltipProvider delayDuration={200}>
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 72 : 240 }}
        transition={{ duration: 0.2, ease: "easeInOut" }}
        className="hidden md:flex h-screen shrink-0 flex-col border-r border-border bg-card"
      >
        {/* Brand */}
        <div className={cn("flex items-center h-16 px-4 border-b border-border", collapsed && "justify-center px-0")}>
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600 text-white">
              <Mail className="h-4 w-4" />
            </div>
            {!collapsed && (
              <span className="truncate text-sm font-semibold tracking-tight">
                AI Email OS
              </span>
            )}
          </div>
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <SidebarLink key={to} to={to} label={label} Icon={Icon} collapsed={collapsed} />
          ))}
        </nav>

        {/* Collapse toggle */}
        <div className="border-t border-border p-2">
          <button
            onClick={onToggleCollapsed}
            className={cn(
              "flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors",
              collapsed && "justify-center"
            )}
          >
            {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
            {!collapsed && <span>Collapse</span>}
          </button>
        </div>
      </motion.aside>
    </TooltipProvider>
  );
}

function SidebarLink({ to, label, Icon, collapsed }) {
  const link = (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          collapsed && "justify-center px-0",
          isActive
            ? "bg-primary/10 text-primary"
            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        )
      }
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && <span className="truncate">{label}</span>}
    </NavLink>
  );

  if (!collapsed) return link;

  return (
    <Tooltip>
      <TooltipTrigger asChild>{link}</TooltipTrigger>
      <TooltipContent side="right">{label}</TooltipContent>
    </Tooltip>
  );
}