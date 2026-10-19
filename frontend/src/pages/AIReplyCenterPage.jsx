import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Sparkles, Mail, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import PageHeader from "@/components/shared/PageHeader";
import EmptyState from "@/components/shared/EmptyState";
import ReplyComposer from "@/components/email-detail/ReplyComposer";
import { Skeleton } from "@/components/ui/skeleton";
import emailApi from "@/api/emailApi";
import { useToast } from "@/components/shared/ToastProvider";
import { cn } from "@/lib/utils";

/**
 * AI Reply Center — a dedicated triage view for all emails awaiting
 * a reply, letting the user work through them one by one without
 * navigating back and forth from the Inbox.
 */
export default function AIReplyCenterPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [selectedEmailId, setSelectedEmailId] = React.useState(null);
  const [replyDrafts, setReplyDrafts] = React.useState([]);

  const pendingQuery = useQuery({
    queryKey: ["emails", "pending-reply"],
    queryFn: () => emailApi.getEmails({ pendingReplyOnly: true, page: 1, pageSize: 50, sortBy: "priority", sortOrder: "desc" }),
  });

  React.useEffect(() => {
    if (!selectedEmailId && pendingQuery.data?.items?.length > 0) {
      setSelectedEmailId(pendingQuery.data.items[0].id);
    }
  }, [pendingQuery.data, selectedEmailId]);

  const selectedEmailQuery = useQuery({
    queryKey: ["email", selectedEmailId],
    queryFn: () => emailApi.getEmailById(selectedEmailId),
    enabled: Boolean(selectedEmailId),
  });

  const generateReplyMutation = useMutation({
    mutationFn: (options) => emailApi.generateReply(selectedEmailId, options),
    onSuccess: (data) => setReplyDrafts(data.drafts || []),
    onError: () => toast({ type: "error", message: "Couldn't generate a reply." }),
  });

  const sendReplyMutation = useMutation({
    mutationFn: (payload) => emailApi.sendReply(selectedEmailId, payload),
    onSuccess: () => {
      toast({ type: "success", message: "Reply sent! Moving to the next email." });
      setReplyDrafts([]);
      queryClient.invalidateQueries({ queryKey: ["emails", "pending-reply"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });

      const remaining = (pendingQuery.data?.items || []).filter((e) => e.id !== selectedEmailId);
      setSelectedEmailId(remaining[0]?.id || null);
    },
    onError: () => toast({ type: "error", message: "Failed to send reply." }),
  });

  const emails = pendingQuery.data?.items || [];

  if (!pendingQuery.isLoading && emails.length === 0) {
    return (
      <div className="space-y-4">
        <PageHeader title="AI Reply Center" description="Emails awaiting a response." />
        <EmptyState
          icon={Sparkles}
          title="You're all caught up!"
          description="No emails are currently awaiting a reply."
          action={{ label: "Back to Inbox", onClick: () => navigate("/inbox") }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="AI Reply Center"
        description={pendingQuery.data ? `${pendingQuery.data.total} emails awaiting a reply` : "Loading..."}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        {/* Queue */}
        <Card className="h-fit">
          <CardContent className="space-y-1 p-2">
            {pendingQuery.isLoading
              ? Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)
              : emails.map((email) => (
                  <button
                    key={email.id}
                    onClick={() => {
                      setSelectedEmailId(email.id);
                      setReplyDrafts([]);
                    }}
                    className={cn(
                      "flex w-full items-start gap-2 rounded-md p-2.5 text-left transition-colors",
                      selectedEmailId === email.id ? "bg-primary/10" : "hover:bg-accent"
                    )}
                  >
                    <Mail className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{email.senderName}</p>
                      <p className="truncate text-xs text-muted-foreground">{email.subject}</p>
                    </div>
                    {email.priority === "high" && (
                      <Badge variant="destructive" className="shrink-0 text-[10px]">High</Badge>
                    )}
                    <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                  </button>
                ))}
          </CardContent>
        </Card>

        {/* Detail + composer */}
        <div className="space-y-4">
          {selectedEmailQuery.data && (
            <Card>
              <CardContent className="p-4">
                <h2 className="text-base font-semibold">{selectedEmailQuery.data.subject}</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  From {selectedEmailQuery.data.senderName} &middot; {selectedEmailQuery.data.receivedAtLabel}
                </p>
                <p className="mt-3 text-sm leading-relaxed">
                  {selectedEmailQuery.data.aiSummary || selectedEmailQuery.data.snippet}
                </p>
              </CardContent>
            </Card>
          )}

          <ReplyComposer
            drafts={replyDrafts}
            isGenerating={generateReplyMutation.isPending}
            isSending={sendReplyMutation.isPending}
            onGenerate={(options) => generateReplyMutation.mutate(options)}
            onSend={(payload) => sendReplyMutation.mutate(payload)}
          />
        </div>
      </div>
    </div>
  );
}