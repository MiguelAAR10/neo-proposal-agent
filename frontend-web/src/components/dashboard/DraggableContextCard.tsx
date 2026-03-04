"use client";

import { Activity, TrendingUp, Shield, Lightbulb } from "lucide-react";
import { useAgentStore } from "@/stores/agentStore";
import type { DraggableContextCard as ContextCard } from "@/types/dashboard";

const CATEGORY_ICON: Record<string, React.ReactNode> = {
  macro: <TrendingUp className="h-3.5 w-3.5" />,
  risk: <Shield className="h-3.5 w-3.5" />,
  opportunity: <Lightbulb className="h-3.5 w-3.5" />,
  signal: <Activity className="h-3.5 w-3.5" />,
};

interface Props {
  card: ContextCard;
}

export function DraggableContextCard({ card }: Props) {
  const { contextChips, addContextChip, removeContextChip } = useAgentStore();
  const isActive = contextChips.some((c) => c.id === `ctx-${card.id}`);

  const handleClick = () => {
    if (isActive) {
      removeContextChip(`ctx-${card.id}`);
    } else {
      addContextChip({
        id: `ctx-${card.id}`,
        label: card.title,
        text: `${card.title}: ${card.summary}`,
      });
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`neo-context-chip-card${isActive ? " neo-context-chip-card--active" : ""}`}
      title={card.summary}
    >
      <span className={`inline-flex items-center gap-1.5 ${isActive ? "text-violet-400" : "text-zinc-400"}`}>
        {CATEGORY_ICON[card.category] ?? <Activity className="h-3.5 w-3.5" />}
        <span className="text-[11px] font-semibold text-zinc-50">{card.title}</span>
      </span>
      <span className="mt-1 block text-[11px] leading-relaxed text-zinc-400">
        {card.summary.length > 80 ? `${card.summary.slice(0, 80)}…` : card.summary}
      </span>
      <span className={`neo-tag mt-2 inline-flex ${isActive ? "neo-tag--active" : ""}`}>
        {isActive ? "Anadido" : "Clic para anadir"}
      </span>
    </button>
  );
}
