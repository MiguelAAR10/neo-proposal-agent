"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, ExternalLink, BadgeCheck, Gauge, TriangleAlert, Sparkles } from "lucide-react";
import type { DroppableCaseCard } from "@/types/dashboard";

interface Props {
  card: DroppableCaseCard;
  isDropped: boolean;
  onToggle?: (id: string) => void;
}

const TAG_CLASS =
  "px-2 py-1 bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs font-mono uppercase tracking-wider";

export function DraggableCaseCard({ card, isDropped, onToggle }: Props) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.id,
    data: { kind: "case", payload: card },
  });

  const style = { transform: CSS.Translate.toString(transform) };
  const techs = Array.isArray(card.tecnologias) ? card.tecnologias.slice(0, 3) : [];
  const score = Math.round((card.scoreClientFit ?? card.scoreRaw ?? 0) * 100);

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={`neo-case-card${isDropped ? " neo-case-card--selected" : ""}${isDragging ? " neo-case-card--dragging" : ""}`}
    >
      <div className="neo-case-card__header">
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: 4, flexWrap: "wrap" }}>
            <span className={TAG_CLASS}>{card.tipo}</span>
            <span className={`${TAG_CLASS} ${isDropped ? "neo-tag--active" : ""}`}>
              <Gauge className="h-3 w-3 text-violet-400" />
              {score}%
            </span>
            {card.matchType && <span className={TAG_CLASS}>{card.matchType}</span>}
          </div>
          <h3 className="neo-case-card__title">{card.titulo}</h3>
        </div>
        <div
          {...listeners}
          {...attributes}
          style={{ cursor: "grab", padding: "2px 0", flexShrink: 0 }}
          title="Arrastra al chat para anadir como contexto"
        >
          <GripVertical className="h-4 w-4 text-zinc-400" />
        </div>
      </div>

      <div className="neo-case-card__tags">
        {card.empresa && card.empresa !== "N/A" && <span className={TAG_CLASS}>{card.empresa}</span>}
        {card.industria && card.industria !== "N/A" && <span className={TAG_CLASS}>{card.industria}</span>}
        {card.area && card.area !== "N/A" && <span className={TAG_CLASS}>{card.area}</span>}
      </div>

      <div className="neo-case-card__body">
        <div className="neo-case-card__col">
          <p className="neo-case-card__col-label neo-case-card__col-label--problem">
            <TriangleAlert className="h-3 w-3 text-zinc-400" />
            Problema del cliente
          </p>
          <p className="neo-case-card__col-text">{card.problema}</p>
        </div>
        <div className="neo-case-card__col">
          <p className="neo-case-card__col-label neo-case-card__col-label--solution">
            <Sparkles className="h-3 w-3 text-violet-400" />
            Solucion
          </p>
          <p className="neo-case-card__col-text">{card.solucion}</p>
        </div>
      </div>

      {card.kpiImpacto && (
        <div className="neo-case-card__kpi">
          <Gauge className="h-3.5 w-3.5 text-violet-400" />
          {card.kpiImpacto}
        </div>
      )}

      <div className="neo-case-card__footer">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, flex: 1 }}>
          {techs.map((t) => (
            <span key={t} className={TAG_CLASS}>
              {t}
            </span>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
          {card.urlSlide ? (
            <a
              href={card.urlSlide}
              target="_blank"
              rel="noopener noreferrer"
              className="neo-case-url-btn"
              onClick={(e) => e.stopPropagation()}
            >
              Ver diapositivas <ExternalLink className="h-3 w-3 text-zinc-400" />
            </a>
          ) : (
            <span className="text-[10px] text-zinc-400">Sin URL</span>
          )}
          <button
            type="button"
            onClick={() => onToggle?.(card.id)}
            className={`neo-case-select-btn${isDropped ? " neo-case-select-btn--active" : ""}`}
            title={isDropped ? "Quitar de propuesta" : "Seleccionar para propuesta"}
          >
            <BadgeCheck className={`h-3.5 w-3.5 ${isDropped ? "text-violet-400" : "text-zinc-400"}`} />
            {isDropped ? "Seleccionado" : "Seleccionar"}
          </button>
        </div>
      </div>
    </article>
  );
}
