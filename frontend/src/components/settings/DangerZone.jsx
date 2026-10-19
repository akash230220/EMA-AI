import * as React from "react";
import { AlertTriangle, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

const CONFIRM_PHRASE = "DELETE MY ACCOUNT";

/**
 * Destructive account actions: clear AI processing data (re-runs
 * from scratch) and permanent account deletion, both gated behind
 * explicit confirmation.
 *
 * @param {object} props
 * @param {() => void} props.onClearAiData
 * @param {() => void} props.onDeleteAccount
 * @param {boolean} [props.isClearing]
 * @param {boolean} [props.isDeleting]
 */
export default function DangerZone({ onClearAiData, onDeleteAccount, isClearing, isDeleting }) {
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [confirmText, setConfirmText] = React.useState("");

  const canConfirmDelete = confirmText === CONFIRM_PHRASE;

  const handleDelete = () => {
    if (!canConfirmDelete) return;
    onDeleteAccount();
    setDeleteDialogOpen(false);
  };

  return (
    <Card className="border-destructive/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5 text-destructive">
          <AlertTriangle className="h-4 w-4" />
          Danger Zone
        </CardTitle>
        <CardDescription>These actions are irreversible. Proceed with caution.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between rounded-md border border-border p-3">
          <div>
            <p className="text-sm font-medium">Clear AI processing data</p>
            <p className="text-xs text-muted-foreground">
              Removes all AI summaries, categorizations, and embeddings. Emails are re-processed
              on next sync.
            </p>
          </div>
          <Button variant="outline" onClick={onClearAiData} disabled={isClearing}>
            {isClearing ? "Clearing..." : "Clear data"}
          </Button>
        </div>

        <div className="flex items-center justify-between rounded-md border border-destructive/30 bg-destructive/5 p-3">
          <div>
            <p className="text-sm font-medium">Delete account</p>
            <p className="text-xs text-muted-foreground">
              Permanently deletes your account, emails, tasks, meetings, and all associated data.
            </p>
          </div>
          <Button variant="destructive" onClick={() => setDeleteDialogOpen(true)}>
            <Trash2 className="h-4 w-4" />
            Delete account
          </Button>
        </div>
      </CardContent>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-destructive">Delete your account?</DialogTitle>
            <DialogDescription>
              This action cannot be undone. All your emails, AI insights, tasks, meetings, and
              automation rules will be permanently deleted.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-1.5">
            <Label htmlFor="confirm-delete">
              Type <span className="font-mono font-semibold">{CONFIRM_PHRASE}</span> to confirm
            </Label>
            <Input
              id="confirm-delete"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder={CONFIRM_PHRASE}
              autoComplete="off"
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={!canConfirmDelete || isDeleting} onClick={handleDelete}>
              {isDeleting ? "Deleting..." : "Permanently delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}