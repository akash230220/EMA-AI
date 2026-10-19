import * as React from "react";
import ConversationSidebar from "@/components/copilot/ConversationSidebar";
import ChatWindow from "@/components/copilot/ChatWindow";
import copilotApi from "@/api/copilotApi";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/components/shared/ToastProvider";

/**
 * Copilot Chat — full-page conversational AI interface with a
 * conversation history sidebar and streaming responses (SSE) via
 * copilotApi.streamMessage().
 */
export default function CopilotChatPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [activeConversationId, setActiveConversationId] = React.useState(null);
  const [messages, setMessages] = React.useState([]);
  const [isStreaming, setIsStreaming] = React.useState(false);
  const abortControllerRef = React.useRef(null);

  const conversationsQuery = useQuery({
    queryKey: ["copilot-conversations"],
    queryFn: () => copilotApi.getConversations(),
  });

  const conversationQuery = useQuery({
    queryKey: ["copilot-conversation", activeConversationId],
    queryFn: () => copilotApi.getConversationById(activeConversationId),
    enabled: Boolean(activeConversationId),
  });

  React.useEffect(() => {
    if (conversationQuery.data) {
      setMessages(conversationQuery.data.messages || []);
    }
  }, [conversationQuery.data]);

  const renameMutation = useMutation({
    mutationFn: ({ id, title }) => copilotApi.renameConversation(id, title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["copilot-conversations"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => copilotApi.deleteConversation(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["copilot-conversations"] });
      if (id === activeConversationId) {
        setActiveConversationId(null);
        setMessages([]);
      }
    },
  });

  const feedbackMutation = useMutation({
    mutationFn: ({ messageId, rating }) => copilotApi.submitFeedback(messageId, rating),
  });

  const handleNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
  };

  const handleSendMessage = async (text) => {
    const userMessage = { id: crypto.randomUUID(), role: "user", content: text };
    const assistantMessageId = crypto.randomUUID();
    const assistantPlaceholder = { id: assistantMessageId, role: "assistant", content: "", toolCalls: [], sources: [] };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await copilotApi.streamMessage(
        { conversationId: activeConversationId, message: text },
        controller.signal
      );

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // keep incomplete chunk for next read

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          const jsonStr = line.replace(/^data:\s*/, "");
          if (jsonStr === "[DONE]") continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.type === "conversation_id" && !activeConversationId) {
              setActiveConversationId(event.conversationId);
            }
            if (event.type === "token") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessageId ? { ...m, content: m.content + event.content } : m
                )
              );
            }
            if (event.type === "tool_call") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessageId
                    ? { ...m, toolCalls: [...(m.toolCalls || []), event.toolCall] }
                    : m
                )
              );
            }
            if (event.type === "sources") {
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantMessageId ? { ...m, sources: event.sources } : m))
              );
            }
          } catch {
            // Skip malformed SSE chunks rather than crashing the stream
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        toast({ type: "error", message: "Copilot stopped responding. Please try again." });
      }
    } finally {
      setIsStreaming(false);
      queryClient.invalidateQueries({ queryKey: ["copilot-conversations"] });
    }
  };

  const handleStopStreaming = () => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  };

  const handleFeedback = (messageId, rating) => {
    setMessages((prev) => prev.map((m) => (m.id === messageId ? { ...m, feedback: rating } : m)));
    feedbackMutation.mutate({ messageId, rating });
  };

  return (
    <div className="-m-4 flex h-[calc(100vh-4rem)] overflow-hidden md:-m-6">
      <ConversationSidebar
        conversations={conversationsQuery.data?.items}
        activeConversationId={activeConversationId}
        isLoading={conversationsQuery.isLoading}
        onNewConversation={handleNewConversation}
        onSelectConversation={setActiveConversationId}
        onRenameConversation={(id, title) => renameMutation.mutate({ id, title })}
        onDeleteConversation={(id) => deleteMutation.mutate(id)}
      />
      <div className="flex-1">
        <ChatWindow
          messages={messages}
          isLoadingHistory={conversationQuery.isLoading}
          isStreaming={isStreaming}
          onSendMessage={handleSendMessage}
          onStopStreaming={handleStopStreaming}
          onFeedback={handleFeedback}
        />
      </div>
    </div>
  );
}