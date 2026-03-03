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

const SEVERITY_COLOR: Record<string, string> = {
  high: "#ffb3b3",
  medium: "#ffd89f",
  low: "#b4ffd2",
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

  const severityColor = SEVERITY_COLOR[card.severity] ?? "#b3d5ff";

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`neo-chip-btn${isActive ? " neo-chip-btn--active" : ""}`}
      style={{ width: "100%", borderRadius: 10, padding: "7px 10px", textAlign: "left" }}
      title={card.summary}
    >
      <span style={{ display: "flex", alignItems: "center", gap: 5, color: isActive ? "#b3d5ff" : severityColor }}>
        {CATEGORY_ICON[card.category] ?? <Activity className="h-3.5 w-3.5" />}
        <span style={{ fontWeight: 700, fontSize: 11 }}>{card.title}</span>
      </span>
      <span style={{ fontSize: 10, color: "#9ab0cc", marginTop: 2, display: "block", lineHeight: 1.3 }}>
        {card.summary.length > 60 ? card.summary.slice(0, 60) + "…" : card.summary}
      </span>
      <span
        style={{
          marginTop: 4,
          display: "inline-block",
          fontSize: 9,
          padding: "1px 6px",
          borderRadius: 999,
          background: isActive ? "rgba(108,140,255,0.25)" : "rgba(255,255,255,0.07)",
          color: isActive ? "#b3d5ff" : "#8ab0d0",
          border: `1px solid ${isActive ? "rgba(108,140,255,0.5)" : "rgba(255,255,255,0.1)"}`,
        }}
      >
        {isActive ? "✓ Añadido al chat" : "Clic para añadir"}
      </span>
    </button>
  );
}
