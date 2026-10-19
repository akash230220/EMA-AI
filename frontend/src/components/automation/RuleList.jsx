import * as React from "react";
import { Zap, Plus } from "lucide-react";
import { DndContext, PointerSensor, useSensor, useSensors, closestCenter } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy, arrayMove } from "@dnd-kit/sortable";
import RuleCard from "./RuleCard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Draggable, reorderable list of automation rules. Purely
 * presentational — parent AutomationRulesPage owns fetching/mutations
 * via React Query + automationApi.
 *
 * @param {object} props
 * @param {object[]} props.rules
 * @param {boolean} [props.isLoading]
 * @param {() => void} props.onCreateRule
 * @param {(id: string, enabled: boolean) => void} props.onToggleEnabled
 * @param {(id: string) => void} props.onEdit
 * @param {(id: string) => void} props.onDelete
 * @param {(id: string) => void} props.onViewLogs
 * @param {(orderedRules: {ruleId: string, priority: number}[]) => void} props.onReorder
 */
export default function RuleList({
  rules = [],
  isLoading,
  onCreateRule,
  onToggleEnabled,
  onEdit,
  onDelete,
  onViewLogs,
  onReorder,
}) {
  const [localRules, setLocalRules] = React.useState(rules);

  React.useEffect(() => {
    setLocalRules(rules);
  }, [rules]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = localRules.findIndex((r) => r.id === active.id);
    const newIndex = localRules.findIndex((r) => r.id === over.id);
    const reordered = arrayMove(localRules, oldIndex, newIndex);

    setLocalRules(reordered);
    onReorder(reordered.map((r, i) => ({ ruleId: r.id, priority: i })));
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (localRules.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border py-16 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
          <Zap className="h-6 w-6 text-muted-foreground" />
        </div>
        <div>
          <p className="text-sm font-medium">No automation rules yet</p>
          <p className="text-xs text-muted-foreground">
            Automatically archive, label, or forward emails based on AI-detected conditions.
          </p>
        </div>
        <Button onClick={onCreateRule} size="sm">
          <Plus className="h-4 w-4" />
          Create your first rule
        </Button>
      </div>
    );
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={localRules.map((r) => r.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-2">
          {localRules.map((rule) => (
            <RuleCard
              key={rule.id}
              rule={rule}
              onToggleEnabled={onToggleEnabled}
              onEdit={onEdit}
              onDelete={onDelete}
              onViewLogs={onViewLogs}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}