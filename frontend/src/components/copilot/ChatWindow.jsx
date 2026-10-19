import * as React from "react";
import { Sparkles } from "lucide-react";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Main scrollable chat surface. Purely presentational — the parent
 * CopilotChatPage owns message state, the streaming fetch call
 * (copilotApi.streamMessage), and feedback mutations.
 *
 * @param {object} props
 * @param {object[]} props.messages
 * @param {boolean} [props.isLoadingHistory]
 * @param {boolean} props.isStreaming
 * @param {(message: string) => void} props.onSendMessage
 * @param {() => void} [props.onStopStreaming]
 * @param {(messageId: string, rating: "up"|"down") => void} [props.onFeedback]
 */
export default function ChatWindow({
  messages = [],
  isLoadingHistory,
  isStreaming,
  onSendMessage,
  onStopStreaming,
  onFeedback,
}) {
  const scrollRef = React.useRef(null);

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, messages[messages.length - 1]?.content]);

  const isEmpty = !isLoadingHistory && messages.length === 0;
  const lastMessage = messages[messages.length - 1];

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
        {isLoadingHistory ? (
          <div className="space-y-4">
            <Skeleton className="h-16 w-2/3" />
            <Skeleton className="ml-auto h-10 w-1/2" />
            <Skeleton className="h-20 w-3/4" />
          </div>
        ) : isEmpty ? (
          <EmptyState />
        ) : (
          <div className="space-y-5">
            {messages.map((message) => (
              <ChatBubble
                key={message.id}
                message={message}
                onFeedback={onFeedback}
                isStreaming={isStreaming && message.id === lastMessage?.id && message.role === "assistant"}
              />
            ))}
          </div>
        )}
      </div>

      <ChatInput
        onSend={onSendMessage}
        onStop={onStopStreaming}
        isStreaming={isStreaming}
        showSuggestions={isEmpty}
      />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 py-16 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-100 to-violet-100">
        <Sparkles className="h-6 w-6 text-indigo-600" />
      </div>
      <div>
        <p className="text-sm font-semibold">Ask your AI Copilot anything</p>
        <p className="mt-1 max-w-xs text-xs text-muted-foreground">
          Search emails, get summaries, draft replies, or ask about your tasks and meetings — all grounded in your inbox history.
        </p>
      </div>
    </div>
  );
}