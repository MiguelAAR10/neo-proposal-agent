"use client";

import { CSS } from "@dnd-kit/utilities";
import { useDraggable } from "@dnd-kit/core";
import { GripVertical, ExternalLink, BadgeCheck } from "lucide-react";
import type { DroppableCaseCard } from "@/types/dashboard";

interface DraggableCaseCardProps {
  card: DroppableCaseCard;
  isDropped: boolean;
}

export function DraggableCaseCard({ card, isDropped }: DraggableCaseCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.id,
    data: { kind: "case", payload: card },
  });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.65 : 1,
  };

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={`neo-dnd-card ${isDragging ? "neo-dnd-card--dragging" : ""} ${
        isDropped ? "neo-dnd-card--dropped" : ""
      }`}
      {...listeners}
      {...attributes}
    >
      <header className="neo-dnd-card__header">
        <div className="flex items-center gap-2">
          <span className="neo-dnd-chip">{card.tipo}</span>
          <span className="neo-dnd-chip neo-dnd-chip--score">
            {Math.round((card.scoreClientFit ?? card.scoreRaw ?? 0) * 100)}%
          </span>
        </div>
        <GripVertical className="h-4 w-4 text-slate-300" />
      </header>
      <h3 className="neo-dnd-card__title">{card.titulo}</h3>
      <p className="neo-dnd-card__desc">{card.problema}</p>
      <footer className="neo-dnd-card__footer">
        <span>{card.empresa}</span>
        <span>{card.area}</span>
        {card.urlSlide ? (
          <a href={card.urlSlide} target="_blank" rel="noopener noreferrer" className="neo-dnd-link">
            Evidencia <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : (
          <span className="neo-dnd-muted">Sin URL</span>
        )}
        {isDropped && (
          <span className="neo-dnd-success">
            <BadgeCheck className="h-3.5 w-3.5" />
            En propuesta
          </span>
        )}
      </footer>
    </article>
  );
}
