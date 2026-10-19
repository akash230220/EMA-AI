import * as React from "react";
import { motion } from "framer-motion";
import { Paperclip, Download, ChevronDown, ChevronUp } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/**
 * Renders a full email thread as a stack of collapsible message
 * cards (Gmail-style: most recent expanded, older ones collapsed).
 *
 * @param {object} props
 * @param {object[]} props.messages - thread messages, oldest first
 * @param {boolean} [props.isLoading]
 */
export default function ThreadView({ messages = [], isLoading }) {
  const [expandedIds, setExpandedIds] = React.useState(() => {
    // Expand only the last message by default
    if (messages.length === 0) return new Set();
    return new Set([messages[messages.length - 1]?.id]);
  });

  React.useEffect(() => {
    if (messages.length > 0) {
      setExpandedIds(new Set([messages[messages.length - 1].id]));
    }
  }, [messages.length]);

  const toggleExpanded = (id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center gap-3">
              <Skeleton className="h-9 w-9 rounded-full" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-3 w-1/4" />
              </div>
            </div>
            <Skeleton className="h-24 w-full" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {messages.map((message) => (
        <ThreadMessage
          key={message.id}
          message={message}
          expanded={expandedIds.has(message.id)}
          onToggle={() => toggleExpanded(message.id)}
        />
      ))}
    </div>
  );
}

function ThreadMessage({ message, expanded, onToggle }) {
  return (
    <motion.div
      layout
      className="overflow-hidden rounded-lg border border-border bg-card"
    >
      <button
        onClick={onToggle}
        className="flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-accent/50"
      >
        <Avatar className="h-9 w-9 shrink-0">
          <AvatarFallback className="text-xs">
            {message.senderName?.[0]?.toUpperCase() || "?"}
          </AvatarFallback>
        </Avatar>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <span className="text-sm font-semibold">{message.senderName}</span>
              <span className="ml-1.5 truncate text-xs text-muted-foreground">
                &lt;{message.senderEmail}&gt;
              </span>
            </div>
            <span className="shrink-0 text-xs text-muted-foreground">{message.sentAtLabel}</span>
          </div>
          {!expanded && (
            <p className="mt-0.5 truncate text-xs text-muted-foreground">{message.snippet}</p>
          )}
          {expanded && message.recipientsLabel && (
            <p className="mt-0.5 truncate text-xs text-muted-foreground">
              To: {message.recipientsLabel}
            </p>
          )}
        </div>

        {expanded ? (
          <ChevronUp className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronDown className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-border px-4 py-4">
          <div
            className={cn(
              "prose prose-sm max-w-none text-foreground",
              "prose-p:my-2 prose-a:text-primary"
            )}
            // Body is sanitized server-side before being stored/returned.
            dangerouslySetInnerHTML={{ __html: message.bodyHtml || message.bodyText }}
          />

          {message.attachments?.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2 border-t border-border pt-3">
              {message.attachments.map((att) => (
                <a
                  key={att.id}
                  href={att.downloadUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 rounded-md border border-border px-2.5 py-1.5 text-xs hover:bg-accent"
                >
                  <Paperclip className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="max-w-[140px] truncate">{att.filename}</span>
                  <Download className="h-3.5 w-3.5 text-muted-foreground" />
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}