"use client";

import type { DraggableContextCard } from "@/types/dashboard";

interface RadarIntelligencePanelProps {
  cards: DraggableContextCard[];
}

export function RadarIntelligencePanel({ cards }: RadarIntelligencePanelProps) {
  const highAlerts = cards.filter((item) => item.severity === "high").length;
  return (
    <aside className="neo-radar-panel">
      <h3>Radar Intelligence</h3>
      <p>
        {highAlerts} alertas críticas detectadas.
      </p>
      <div className="neo-radar-tags">
        {cards.slice(0, 3).map((item) => (
          <span key={item.id}>{item.title}</span>
        ))}
      </div>
    </aside>
  );
}

