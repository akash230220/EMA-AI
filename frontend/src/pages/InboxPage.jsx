import * as React from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import EmailList from "@/components/inbox/EmailList";
import InboxFilters from "@/components/inbox/InboxFilters";
import InboxTabs from "@/components/inbox/InboxTabs";
import PaginationBar from "@/components/inbox/PaginationBar";
import PageHeader from "@/components/shared/PageHeader";
import emailApi from "@/api/emailApi";
import { useToast } from "@/components/shared/ToastProvider";

const TAB_PRESETS = {
  all: {},
  unread: { unreadOnly: true },
  high_priority: { priority: "high" },
  meetings: { intent: "meeting_request" },
  tasks: { intent: "task" },
  archived: { archived: true },
};

/**
 * Inbox — the main email list page. Owns filter/pagination state,
 * fetches via emailApi.getEmails(), and wires bulk actions.
 */
export default function InboxPage() {
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = React.useState("all");
  const [filters, setFilters] = React.useState({
    page: 1,
    pageSize: 20,
    search: searchParams.get("search") || undefined,
  });

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setFilters((prev) => ({
      search: prev.search,
      page: 1,
      pageSize: prev.pageSize,
      ...TAB_PRESETS[tab],
    }));
  };

  const emailsQuery = useQuery({
    queryKey: ["emails", filters],
    queryFn: () => emailApi.getEmails(filters),
    keepPreviousData: true,
  });

  const bulkActionMutation = useMutation({
    mutationFn: ({ action, ids }) => emailApi.bulkAction(ids, action),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      toast({ type: "success", message: `${variables.ids.length} email(s) updated.` });
    },
    onError: () => {
      toast({ type: "error", message: "Couldn't complete that action. Please try again." });
    },
  });

  const handleBulkAction = (action, ids) => {
    if (ids.length === 0) return;
    bulkActionMutation.mutate({ action, ids });
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Inbox"
        description={
          emailsQuery.data ? `${emailsQuery.data.total} emails` : "Loading your inbox..."
        }
      />

      <InboxTabs value={activeTab} onChange={handleTabChange} />
      <InboxFilters filters={filters} onFiltersChange={setFilters} />

      <Card className="overflow-hidden p-0">
        <EmailList
          emails={emailsQuery.data?.items}
          isLoading={emailsQuery.isLoading}
          onBulkAction={handleBulkAction}
        />
        {emailsQuery.data && emailsQuery.data.total > 0 && (
          <PaginationBar
            page={filters.page}
            pageSize={filters.pageSize}
            total={emailsQuery.data.total}
            onPageChange={(page) => setFilters((prev) => ({ ...prev, page }))}
          />
        )}
      </Card>
    </div>
  );
}