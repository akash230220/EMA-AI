import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import copilotApi from "@/api/copilotApi";
import { useToast } from "@/components/shared/ToastProvider";

/** Fetches the user's Copilot conversation history. */
export function useCopilotConversations(params = {}) {
  return useQuery({
    queryKey: ["copilot-conversations", params],
    queryFn: () => copilotApi.getConversations(params),
  });
}

/** Fetches full message history for one conversation. */
export function useCopilotConversation(conversationId) {
  return useQuery({
    queryKey: ["copilot-conversation", conversationId],
    queryFn: () => copilotApi.getConversationById(conversationId),
    enabled: Boolean(conversationId),
  });
}

/** Renames a conversation. */
export function useRenameConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, title }) => copilotApi.renameConversation(id, title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["copilot-conversations"] }),
  });
}

/** Deletes a conversation. */
export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => copilotApi.deleteConversation(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["copilot-conversations"] }),
  });
}

/** Submits thumbs up/down feedback on an assistant message. */
export function useSubmitCopilotFeedback() {
  return useMutation({
    mutationFn: ({ messageId, rating, comment }) => copilotApi.submitFeedback(messageId, rating, comment),
  });
}

/**
 * Encapsulates the full streaming chat lifecycle: sending a message,
 * reading the SSE response, appending tokens to the in-progress
 * assistant message, and exposing an abort/stop control.
 *
 * This is the logic previously inlined in CopilotChatPage.jsx,
 * extracted here so it can be reused (e.g. a future embedded
 * Copilot widget) without duplicating the SSE parsing.
 *
 * @param {string|null} conversationId
 * @param {(newConversationId: string) => void} [onConversationCreated]
 */
export function useCopilotChatStream(conversationId, onConversationCreated) {
  const [isStreaming, setIsStreaming] = React.useState(false);
  const abortControllerRef = React.useRef(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const sendMessage = React.useCallback(
    async (text, { onToken, onToolCall, onSources, onDone } = {}) => {
      setIsStreaming(true);
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const response = await copilotApi.streamMessage(
          { conversationId, message: text },
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
          buffer = lines.pop();

          for (const line of lines) {
            if (!line.startsWith("data:")) continue;
            const jsonStr = line.replace(/^data:\s*/, "");
            if (jsonStr === "[DONE]") continue;

            try {
              const event = JSON.parse(jsonStr);
              if (event.type === "conversation_id" && !conversationId) {
                onConversationCreated?.(event.conversationId);
              }
              if (event.type === "token") onToken?.(event.content);
              if (event.type === "tool_call") onToolCall?.(event.toolCall);
              if (event.type === "sources") onSources?.(event.sources);
            } catch {
              // Skip malformed SSE chunks rather than crashing the stream
            }
          }
        }
        onDone?.();
      } catch (err) {
        if (err.name !== "AbortError") {
          toast({ type: "error", message: "Copilot stopped responding. Please try again." });
        }
      } finally {
        setIsStreaming(false);
        queryClient.invalidateQueries({ queryKey: ["copilot-conversations"] });
      }
    },
    [conversationId, onConversationCreated, toast, queryClient]
  );

  const stopStreaming = React.useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { sendMessage, stopStreaming, isStreaming };
}