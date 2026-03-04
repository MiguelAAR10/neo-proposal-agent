"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, ExternalLink, BadgeCheck } from "lucide-react";
import type { DroppableCaseCard } from "@/types/dashboard";

interface Props {
  card: DroppableCaseCard;
  isDropped: boolean;
  onToggle?: (id: string) => void;
}

const MATCH_STYLE: Record<string, { bg: string; color: string }> = {
  exacto:       { bg: "rgba(110,255,170,0.12)", color: "#8ff8be" },
  relacionado:  { bg: "rgba(74,172,255,0.12)",  color: "#7bc8ff" },
  inspiracional:{ bg: "rgba(196,149,255,0.12)", color: "#d4a8ff" },
};

export function DraggableCaseCard({ card, isDropped, onToggle }: Props) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.id,
    data: { kind: "case", payload: card },
  });

  const style = { transform: CSS.Translate.toString(transform) };
  const matchStyle = MATCH_STYLE[card.matchType ?? ""] ?? { bg: "rgba(255,255,255,0.06)", color: "#a8b8d4" };
  const techs = Array.isArray(card.tecnologias) ? card.tecnologias.slice(0, 3) : [];
  const score = Math.round((card.scoreClientFit ?? card.scoreRaw ?? 0) * 100);
  const lowerProblem = card.problema.toLowerCase();
  const tone =
    lowerProblem.includes("fraude") || lowerProblem.includes("riesgo")
      ? "risk"
      : card.matchType === "exacto"
        ? "op"
        : "brand";

  return (
    <article
      ref={setNodeRef}
      data-tone={tone}
      style={style}
      className={`neo-case-card${isDropped ? " neo-case-card--selected" : ""}${isDragging ? " neo-case-card--dragging" : ""}`}
    >
      {/* Header */}
      <div className="neo-case-card__header">
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: 4, flexWrap: "wrap" }}>
            <span className="neo-dnd-chip" style={{ fontSize: 9, padding: "1px 7px" }}>{card.tipo}</span>
            <span className="neo-dnd-chip neo-dnd-chip--score" style={{ fontSize: 9, padding: "1px 7px" }}>
              {score}%
            </span>
            {card.matchType && (
              <span
                style={{
                  fontSize: 9, padding: "1px 7px", borderRadius: 999,
                  background: matchStyle.bg, color: matchStyle.color,
                  border: `1px solid ${matchStyle.color}55`,
                }}
              >
                {card.matchType}
              </span>
            )}
          </div>
          <h3 className="neo-case-card__title">{card.titulo}</h3>
        </div>
        {/* Drag handle — solo esta zona inicia el arrastre */}
        <div
          {...listeners}
          {...attributes}
          style={{ cursor: "grab", padding: "2px 0", flexShrink: 0 }}
          title="Arrastra al chat para añadir como contexto"
        >
          <GripVertical className="h-4 w-4 text-slate-400" />
        </div>
      </div>

      {/* Tags empresa / área */}
      <div className="neo-case-card__tags">
        {card.empresa && card.empresa !== "N/A" && (
          <span className="neo-dnd-chip" style={{ fontSize: 9 }}>{card.empresa}</span>
        )}
        {card.industria && card.industria !== "N/A" && (
          <span className="neo-dnd-chip" style={{ fontSize: 9, color: "#c3d2f1" }}>{card.industria}</span>
        )}
        {card.area && card.area !== "N/A" && (
          <span className="neo-dnd-chip" style={{ fontSize: 9, color: "#c3d2f1" }}>{card.area}</span>
        )}
      </div>

      {/* Cuerpo — Problema / Solución en dos columnas */}
      <div className="neo-case-card__body">
        <div className="neo-case-card__col">
          <p className="neo-case-card__col-label neo-case-card__col-label--problem">Problema del cliente</p>
          <p className="neo-case-card__col-text">{card.problema}</p>
        </div>
        <div className="neo-case-card__col">
          <p className="neo-case-card__col-label neo-case-card__col-label--solution">Solución</p>
          <p className="neo-case-card__col-text">{card.solucion}</p>
        </div>
      </div>

      {/* KPI impacto */}
      {card.kpiImpacto && (
        <div className="neo-case-card__kpi">
          ⚡ {card.kpiImpacto}
        </div>
      )}

      {/* Footer — tecnologías + URL + selección */}
      <div className="neo-case-card__footer">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, flex: 1 }}>
          {techs.map((t) => (
            <span key={t} className="neo-dnd-chip" style={{ fontSize: 9 }}>{t}</span>
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
              Ver diapositivas <ExternalLink className="h-3 w-3" />
            </a>
          ) : (
            <span style={{ fontSize: 10, color: "#4a5e7a", fontStyle: "italic" }}>Sin URL</span>
          )}
          <button
            type="button"
            onClick={() => onToggle?.(card.id)}
            className={`neo-case-select-btn${isDropped ? " neo-case-select-btn--active" : ""}`}
            title={isDropped ? "Quitar de propuesta" : "Seleccionar para propuesta"}
          >
            <BadgeCheck className="h-3.5 w-3.5" />
            {isDropped ? "Seleccionado" : "Seleccionar"}
          </button>
        </div>
      </div>
    </article>
  );
}
