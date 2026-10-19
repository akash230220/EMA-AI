import * as React from "react";
import { Sparkles, Send, RotateCcw, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

const TONE_OPTIONS = [
  { value: "formal", label: "Formal" },
  { value: "friendly", label: "Friendly" },
  { value: "concise", label: "Concise" },
];

/**
 * Reply composer for the Email Detail page: lets the user generate
 * AI draft options (via emailApi.generateReply), pick/edit one, and
 * send (via emailApi.sendReply). Also usable standalone as the base
 * for the dedicated AI Reply Center page.
 *
 * @param {object} props
 * @param {{id: string, tone: string, body: string}[]} [props.drafts]
 * @param {boolean} [props.isGenerating]
 * @param {boolean} [props.isSending]
 * @param {(options: {tone: string, instructions: string}) => void} props.onGenerate
 * @param {(payload: {body: string, draftId?: string}) => void} props.onSend
 */
export default function ReplyComposer({
  drafts = [],
  isGenerating,
  isSending,
  onGenerate,
  onSend,
}) {
  const [tone, setTone] = React.useState("friendly");
  const [instructions, setInstructions] = React.useState("");
  const [activeDraftId, setActiveDraftId] = React.useState(null);
  const [bodyDraft, setBodyDraft] = React.useState("");

  // When new drafts arrive, select the first one and populate the editor
  React.useEffect(() => {
    if (drafts.length > 0) {
      setActiveDraftId(drafts[0].id);
      setBodyDraft(drafts[0].body);
    }
  }, [drafts]);

  const handleSelectDraft = (draft) => {
    setActiveDraftId(draft.id);
    setBodyDraft(draft.body);
  };

  const handleGenerate = () => {
    onGenerate({ tone, instructions: instructions.trim() });
  };

  const handleSend = () => {
    if (!bodyDraft.trim()) return;
    onSend({ body: bodyDraft, draftId: activeDraftId || undefined });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5 text-base">
          <Sparkles className="h-4 w-4 text-indigo-600" />
          AI Reply
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Generation controls */}
        <div className="flex flex-wrap items-end gap-2">
          <div className="flex-1 min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Tone</label>
            <Select value={tone} onValueChange={setTone}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TONE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button onClick={handleGenerate} disabled={isGenerating} className="shrink-0">
            {isGenerating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {isGenerating ? "Generating..." : drafts.length > 0 ? "Regenerate" : "Generate Reply"}
          </Button>
        </div>

        <Textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="Optional instructions for the AI (e.g. 'confirm the meeting but ask to push to 3pm')"
          className="min-h-[52px] text-sm"
        />

        {/* Draft tone picker (once multiple drafts exist) */}
        {drafts.length > 1 && (
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              Choose a draft
            </label>
            <Tabs value={activeDraftId || undefined} onValueChange={(id) => {
              const draft = drafts.find((d) => d.id === id);
              if (draft) handleSelectDraft(draft);
            }}>
              <TabsList>
                {drafts.map((draft) => (
                  <TabsTrigger key={draft.id} value={draft.id} className="capitalize">
                    {draft.tone}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
          </div>
        )}

        {/* Editable reply body */}
        {(drafts.length > 0 || bodyDraft) && (
          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <label className="text-xs font-medium text-muted-foreground">Reply</label>
              {activeDraftId && (
                <button
                  onClick={() => {
                    const draft = drafts.find((d) => d.id === activeDraftId);
                    if (draft) setBodyDraft(draft.body);
                  }}
                  className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground"
                >
                  <RotateCcw className="h-3 w-3" />
                  Reset to AI draft
                </button>
              )}
            </div>
            <Textarea
              value={bodyDraft}
              onChange={(e) => setBodyDraft(e.target.value)}
              className={cn("min-h-[160px] text-sm")}
              placeholder="Your reply..."
            />
          </div>
        )}

        <div className="flex justify-end">
          <Button onClick={handleSend} disabled={isSending || !bodyDraft.trim()}>
            {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            {isSending ? "Sending..." : "Send Reply"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}