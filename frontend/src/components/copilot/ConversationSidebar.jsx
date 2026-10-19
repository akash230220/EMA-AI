import * as React from "react";
import { Plus, MessageSquare, Trash2, Pencil, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/**
 * Left rail listing the user's past Copilot conversations, with
 * new-chat, rename, and delete actions. Mirrors ChatGPT-style
 * conversation history UX.
 *
 * @param {object} props
 * @param {{id: string, title: string, lastMessageAt: string}[]} props.conversations
 * @param {string|null} props.activeConversationId
 * @param {boolean} [props.isLoading]
 * @param {() => void} props.onNewConversation
 * @param {(id: string) => void} props.onSelectConversation
 * @param {(id: string, title: string) => void} props.onRenameConversation
 * @param {(id: string) => void} props.onDeleteConversation
 */
export default function ConversationSidebar({
  conversations = [],
  activeConversationId,
  isLoading,
  onNewConversation,
  onSelectConversation,
  onRenameConversation,
  onDeleteConversation,
}) {
  const [editingId, setEditingId] = React.useState(null);
  const [editValue, setEditValue] = React.useState("");

  const startEditing = (conv) => {
    setEditingId(conv.id);
    setEditValue(conv.title);
  };

  const commitEdit = () => {
    if (editValue.trim()) {
      onRenameConversation(editingId, editValue.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="flex h-full w-64 shrink-0 flex-col border-r border-border">
      <div className="p-3">
        <Button variant="outline" className="w-full justify-start gap-2" onClick={onNewConversation}>
          <Plus className="h-4 w-4" />
          New chat
        </Button>
      </div>

      <div className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-9 w-full rounded-md" />)
        ) : conversations.length === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-muted-foreground">No conversations yet</p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={cn(
                "group flex items-center gap-2 rounded-md px-2 py-2 text-sm cursor-pointer transition-colors",
                conv.id === activeConversationId
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
              onClick={() => editingId !== conv.id && onSelectConversation(conv.id)}
            >
              <MessageSquare className="h-3.5 w-3.5 shrink-0" />

              {editingId === conv.id ? (
                <div className="flex flex-1 items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <Input
                    autoFocus
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") commitEdit();
                      if (e.key === "Escape") setEditingId(null);
                    }}
                    className="h-6 px-1.5 text-xs"
                  />
                  <button onClick={commitEdit} className="shrink-0">
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                  </button>
                  <button onClick={() => setEditingId(null)} className="shrink-0">
                    <X className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                </div>
              ) : (
                <>
                  <span className="flex-1 truncate">{conv.title || "New conversation"}</span>
                  <div className="hidden shrink-0 items-center gap-0.5 group-hover:flex">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startEditing(conv);
                      }}
                      aria-label="Rename conversation"
                    >
                      <Pencil className="h-3 w-3 hover:text-foreground" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(conv.id);
                      }}
                      aria-label="Delete conversation"
                    >
                      <Trash2 className="h-3 w-3 hover:text-destructive" />
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}