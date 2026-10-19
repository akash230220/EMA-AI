import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Mail } from "lucide-react";

/**
 * Row of small "source" chips shown under an assistant message,
 * linking back to the specific emails the RAG pipeline retrieved
 * from ChromaDB to ground its answer.
 *
 * @param {object} props
 * @param {{email_id: string, snippet: string, score: number}[]} props.sources
 */
export default function SourceCitations({ sources }) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-wrap gap-1.5">
      {sources.map((source, i) => (
        <button
          key={`${source.email_id}-${i}`}
          onClick={() => navigate(`/inbox/${source.email_id}`)}
          className="flex max-w-[220px] items-center gap-1.5 rounded-md border border-border bg-background px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          title={source.snippet}
        >
          <Mail className="h-3 w-3 shrink-0" />
          <span className="truncate">{source.snippet}</span>
        </button>
      ))}
    </div>
  );
}