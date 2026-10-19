import * as React from "react";
import { Inbox as InboxIcon, Archive, Trash2, MailOpen, X } from "lucide-react";
import EmailListItem from "./EmailListItem";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";

/**
 * Scrollable email list with multi-select + bulk action bar.
 * Purely presentational — fetching/mutations happen in the parent
 * InboxPage via React Query + emailApi.bulkAction().
 *
 * @param {object} props
 * @param {object[]} props.emails
 * @param {boolean} props.isLoading
 * @param {(action: "archive"|"delete"|"mark_read"|"mark_unread", ids: string[]) => void} props.onBulkAction
 */
export default function EmailList({ emails = [], isLoading, onBulkAction }) {
  const [selectedIds, setSelectedIds] = React.useState(new Set());

  const handleSelectChange = (id, checked) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      checked ? next.add(id) : next.delete(id);
      return next;
    });
  };

  const allSelected = emails.length > 0 && selectedIds.size === emails.length;
  const someSelected = selectedIds.size > 0;

  const toggleSelectAll = (checked) => {
    setSelectedIds(checked ? new Set(emails.map((e) => e.id)) : new Set());
  };

  const runBulkAction = (action) => {
    onBulkAction(action, Array.from(selectedIds));
    setSelectedIds(new Set());
  };

  if (isLoading) {
    return (
      <div className="divide-y divide-border">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-start gap-3 px-3 py-3">
            <Skeleton className="mt-1 h-4 w-4" />
            <Skeleton className="h-9 w-9 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-2/3" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (emails.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
          <InboxIcon className="h-6 w-6 text-muted-foreground" />
        </div>
        <div>
          <p className="text-sm font-medium">No emails found</p>
          <p className="text-xs text-muted-foreground">Try adjusting your filters or sync your inbox.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Select-all row / bulk action bar */}
      <div className="flex items-center gap-3 border-b border-border bg-muted/40 px-3 py-2">
        <Checkbox
          checked={allSelected}
          onCheckedChange={toggleSelectAll}
          aria-label="Select all emails"
        />
        {someSelected ? (
          <div className="flex flex-1 items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground">
              {selectedIds.size} selected
            </span>
            <div className="ml-auto flex items-center gap-1">
              <Button variant="ghost" size="sm" onClick={() => runBulkAction("mark_read")}>
                <MailOpen className="h-3.5 w-3.5" />
                Mark read
              </Button>
              <Button variant="ghost" size="sm" onClick={() => runBulkAction("archive")}>
                <Archive className="h-3.5 w-3.5" />
                Archive
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => runBulkAction("delete")}
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Delete
              </Button>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setSelectedIds(new Set())}>
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">{emails.length} emails</span>
        )}
      </div>

      <div>
        {emails.map((email) => (
          <EmailListItem
            key={email.id}
            email={email}
            selected={selectedIds.has(email.id)}
            onSelectChange={handleSelectChange}
          />
        ))}
      </div>
    </div>
  );
}