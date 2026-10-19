import * as React from "react";
import { Send, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const SUGGESTED_PROMPTS = [
  "Summarize my unread high-priority emails",
  "What meetings do I have this week?",
  "Find emails about the Q3 budget",
  "Draft a reply to the last email from my manager",
];

/**
 * Chat input box with auto-resize, Enter-to-send (Shift+Enter for
 * newline), and quick suggested-prompt chips shown when the
 * conversation is empty.
 *
 * @param {object} props
 * @param {(message: string) => void} props.onSend
 * @param {() => void} [props.onStop] - cancels an in-flight stream
 * @param {boolean} props.isStreaming
 * @param {boolean} [props.showSuggestions]
 */
export default function ChatInput({ onSend, onStop, isStreaming, showSuggestions }) {
  const [value, setValue] = React.useState("");
  const textareaRef = React.useRef(null);

  const handleChange = (e) => {
    setValue(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  };

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border bg-background p-3">
      {showSuggestions && (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {SUGGESTED_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => onSend(prompt)}
              className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2 rounded-xl border border-input bg-card p-2 shadow-sm focus-within:ring-1 focus-within:ring-ring">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask Copilot about your emails, tasks, or meetings..."
          rows={1}
          className="max-h-40 min-h-[36px] resize-none border-0 shadow-none focus-visible:ring-0"
        />

        {isStreaming ? (
          <Button size="icon" variant="destructive" onClick={onStop} className="shrink-0" aria-label="Stop generating">
            <Square className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            size="icon"
            onClick={handleSubmit}
            disabled={!value.trim()}
            className="shrink-0"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}