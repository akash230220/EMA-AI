import * as React from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Label } from "@/components/ui/label";

const CATEGORY_OPTIONS = ["work", "finance", "personal", "newsletters", "promotions", "social"];
const PRIORITY_OPTIONS = ["high", "medium", "low"];
const INTENT_OPTIONS = ["meeting_request", "task", "fyi", "follow_up", "urgent_action", "question"];
const SENTIMENT_OPTIONS = ["positive", "neutral", "negative"];

/**
 * Filter bar for the Inbox page: search input + a filter drawer
 * covering category/priority/intent/sentiment/unread/pending-reply.
 * Fully controlled — parent (InboxPage) owns filter state and
 * passes it to emailApi.getEmails(params) via React Query.
 *
 * @param {object} props
 * @param {object} props.filters
 * @param {(filters: object) => void} props.onFiltersChange
 */
export default function InboxFilters({ filters, onFiltersChange }) {
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [searchDraft, setSearchDraft] = React.useState(filters.search || "");

  const activeFilterCount = [
    filters.category,
    filters.priority,
    filters.intent,
    filters.sentiment,
    filters.unreadOnly,
    filters.pendingReplyOnly,
  ].filter(Boolean).length;

  const updateFilter = (key, value) => {
    onFiltersChange({ ...filters, [key]: value, page: 1 });
  };

  const clearFilter = (key) => {
    const next = { ...filters };
    delete next[key];
    onFiltersChange({ ...next, page: 1 });
  };

  const clearAllFilters = () => {
    onFiltersChange({ search: filters.search, page: 1 });
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    updateFilter("search", searchDraft.trim() || undefined);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchDraft}
            onChange={(e) => setSearchDraft(e.target.value)}
            placeholder="Search subject, sender, or content..."
            className="pl-8"
          />
        </form>

        <Button variant="outline" onClick={() => setDrawerOpen(true)} className="relative">
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <Badge className="ml-1 h-5 w-5 justify-center rounded-full p-0 text-[10px]">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
      </div>

      {/* Active filter chips */}
      {activeFilterCount > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {filters.category && (
            <FilterChip label={`Category: ${filters.category}`} onClear={() => clearFilter("category")} />
          )}
          {filters.priority && (
            <FilterChip label={`Priority: ${filters.priority}`} onClear={() => clearFilter("priority")} />
          )}
          {filters.intent && (
            <FilterChip label={`Intent: ${filters.intent.replace(/_/g, " ")}`} onClear={() => clearFilter("intent")} />
          )}
          {filters.sentiment && (
            <FilterChip label={`Sentiment: ${filters.sentiment}`} onClear={() => clearFilter("sentiment")} />
          )}
          {filters.unreadOnly && (
            <FilterChip label="Unread only" onClear={() => clearFilter("unreadOnly")} />
          )}
          {filters.pendingReplyOnly && (
            <FilterChip label="Pending reply" onClear={() => clearFilter("pendingReplyOnly")} />
          )}
          <button
            onClick={clearAllFilters}
            className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
          >
            Clear all
          </button>
        </div>
      )}

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent side="right" className="w-80">
          <SheetHeader>
            <SheetTitle>Filter Emails</SheetTitle>
          </SheetHeader>

          <div className="mt-6 space-y-5">
            <FilterSelect
              label="Category"
              value={filters.category}
              options={CATEGORY_OPTIONS}
              onChange={(v) => updateFilter("category", v)}
            />
            <FilterSelect
              label="Priority"
              value={filters.priority}
              options={PRIORITY_OPTIONS}
              onChange={(v) => updateFilter("priority", v)}
            />
            <FilterSelect
              label="Intent"
              value={filters.intent}
              options={INTENT_OPTIONS}
              onChange={(v) => updateFilter("intent", v)}
              formatLabel={(v) => v.replace(/_/g, " ")}
            />
            <FilterSelect
              label="Sentiment"
              value={filters.sentiment}
              options={SENTIMENT_OPTIONS}
              onChange={(v) => updateFilter("sentiment", v)}
            />

            <div className="flex items-center justify-between">
              <Label htmlFor="unread-only" className="text-sm font-normal">
                Unread only
              </Label>
              <input
                id="unread-only"
                type="checkbox"
                checked={Boolean(filters.unreadOnly)}
                onChange={(e) => updateFilter("unreadOnly", e.target.checked || undefined)}
                className="h-4 w-4 rounded border-input"
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="pending-reply-only" className="text-sm font-normal">
                Pending reply only
              </Label>
              <input
                id="pending-reply-only"
                type="checkbox"
                checked={Boolean(filters.pendingReplyOnly)}
                onChange={(e) => updateFilter("pendingReplyOnly", e.target.checked || undefined)}
                className="h-4 w-4 rounded border-input"
              />
            </div>

            <Button variant="outline" className="w-full" onClick={clearAllFilters}>
              Reset filters
            </Button>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

function FilterChip({ label, onClear }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-accent px-2.5 py-1 text-xs capitalize">
      {label}
      <button onClick={onClear} aria-label={`Remove ${label} filter`}>
        <X className="h-3 w-3" />
      </button>
    </span>
  );
}

function FilterSelect({ label, value, options, onChange, formatLabel }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-sm">{label}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue placeholder={`Any ${label.toLowerCase()}`} />
        </SelectTrigger>
        <SelectContent>
          {options.map((opt) => (
            <SelectItem key={opt} value={opt} className="capitalize">
              {formatLabel ? formatLabel(opt) : opt}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}