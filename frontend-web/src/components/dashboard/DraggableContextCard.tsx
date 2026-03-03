"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { Activity } from "lucide-react";
import type { DraggableContextCard as ContextCard } from "@/types/dashboard";

interface DraggableContextCardProps {
  card: ContextCard;
}

export function DraggableContextCard({ card }: DraggableContextCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.id,
    data: { kind: "context", payload: card },
  });

  return (
    <article
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={{ transform: CSS.Translate.toString(transform), opacity: isDragging ? 0.6 : 1 }}
      className="neo-context-card"
    >
      <header>
        <Activity className="h-4 w-4 text-cyan-300" />
        <span>{card.title}</span>
      </header>
      <p>{card.summary}</p>
      <span className={`neo-context-severity neo-context-severity--${card.severity}`}>{card.severity}</span>
    </article>
  );
}

