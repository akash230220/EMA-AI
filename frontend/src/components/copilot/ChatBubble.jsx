import * as React from "react";
import { motion } from "framer-motion";
import { Bot, User, ThumbsUp, ThumbsDown, Search, Check } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import SourceCitations from "./SourceCitations";

/**
 * A single chat message bubble — user or assistant. Assistant
 * messages can show tool-call chips ("Searched your emails for...")
 * and source citations pulled from the RAG pipeline, plus
 * thumbs up/down feedback.
 *
 * @param {object} props
 * @param {object} props.message - { id, role, content, toolCalls?, sources?, feedback? }
 * @param {(messageId: string, rating: "up"|"down") => void} [props.onFeedback]
 * @param {boolean} [props.isStreaming] - true while this message is still being written
 */
export default function ChatBubble({ message, onFeedback, isStreaming }) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn("flex gap-3", isUser && "flex-row-reverse")}
    >
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className={cn(isUser ? "bg-primary text-primary-foreground" : "bg-indigo-100 text-indigo-700")}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      <div className={cn("flex max-w-[75%] flex-col gap-1.5", isUser && "items-end")}>
        {/* Tool call chips */}
        {!isUser && message.toolCalls?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.toolCalls.map((tool, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground"
              >
                <Search className="h-3 w-3" />
                {tool.label || tool.name}
              </span>
            ))}
          </div>
        )}

        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "rounded-tr-sm bg-primary text-primary-foreground"
              : "rounded-tl-sm bg-muted text-foreground"
          )}
        >
          <span className="whitespace-pre-wrap">{message.content}</span>
          {isStreaming && (
            <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-current align-middle" />
          )}
        </div>

        {/* Source citations */}
        {!isUser && message.sources?.length > 0 && (
          <SourceCitations sources={message.sources} />
        )}

        {/* Feedback controls */}
        {!isUser && !isStreaming && onFeedback && (
          <div className="flex items-center gap-0.5">
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={() => onFeedback(message.id, "up")}
              aria-label="Good response"
            >
              {message.feedback === "up" ? (
                <Check className="h-3 w-3 text-emerald-600" />
              ) : (
                <ThumbsUp className="h-3 w-3 text-muted-foreground" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={() => onFeedback(message.id, "down")}
              aria-label="Bad response"
            >
              <ThumbsDown
                className={cn("h-3 w-3", message.feedback === "down" ? "text-red-600" : "text-muted-foreground")}
              />
            </Button>
          </div>
        )}
      </div>
    </motion.div>
  );
}