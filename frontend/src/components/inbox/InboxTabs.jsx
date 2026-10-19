import * as React from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const TABS = [
  { value: "all", label: "All" },
  { value: "unread", label: "Unread" },
  { value: "high_priority", label: "High Priority" },
  { value: "meetings", label: "Meetings" },
  { value: "tasks", label: "Tasks" },
  { value: "archived", label: "Archived" },
];

/**
 * Quick-filter tab strip above the email list, mapped to
 * common preset filter combinations (rather than the full
 * filter drawer in InboxFilters).
 *
 * @param {object} props
 * @param {string} props.value - active tab value
 * @param {(value: string) => void} props.onChange
 */
export default function InboxTabs({ value, onChange }) {
  return (
    <Tabs value={value} onValueChange={onChange}>
      <TabsList>
        {TABS.map((tab) => (
          <TabsTrigger key={tab.value} value={tab.value}>
            {tab.label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}