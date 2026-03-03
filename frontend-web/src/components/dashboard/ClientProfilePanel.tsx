"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, User, MessageSquare, AlertTriangle, TrendingUp } from "lucide-react";
import { useAgentStore } from "@/stores/agentStore";
import type { ClientProfileInsight } from "@/types/dashboard";

const SENTIMENT_COLOR: Record<string, { dot: string; label: string }> = {
  positive: { dot: "#8ff8be", label: "Oportunidad" },
  neutral:  { dot: "#b3d5ff", label: "Info" },
  negative: { dot: "#ffb3b3", label: "Riesgo" },
};

const DUMMY_INSIGHTS: ClientProfileInsight[] = [
  {
    author: "Ana R.",
    text: "Prioridad Q2: reducir fricción en onboarding de PYMEs. Meta: bajar de 8 pasos a 3.",
    timestamp: "28 Feb 2026",
    sentiment: "positive",
  },
  {
    author: "Carlos M.",
    text: "Preocupación por cumplimiento SBS en modelos de scoring. Piden trazabilidad de decisiones.",
    timestamp: "15 Feb 2026",
    sentiment: "neutral",
  },
  {
    author: "Ana R.",
    text: "Presupuesto congelado en H1 para infraestructura core. Oportunidad en iniciativas ágiles de bajo capex.",
    timestamp: "20 Ene 2026",
    sentiment: "negative",
  },
];

export function ClientProfilePanel() {
  const [open, setOpen] = useState(true);
  const { empresa, area, perfilCliente, contextChips, addContextChip, removeContextChip } = useAgentStore();

  const currentEmpresa = empresa || "—";
  const currentArea = area || "—";

  const objetivos: string[] =
    Array.isArray((perfilCliente as Record<string, unknown> | null)?.objetivos)
      ? ((perfilCliente as Record<string, unknown>).objetivos as string[])
      : [];

  const painPoints: string[] =
    Array.isArray((perfilCliente as Record<string, unknown> | null)?.pain_points)
      ? ((perfilCliente as Record<string, unknown>).pain_points as string[])
      : [];

  const isChipActive = (id: string) => contextChips.some((c) => c.id === id);

  const toggleInsightChip = (ins: ClientProfileInsight, idx: number) => {
    const id = `insight-${idx}`;
    if (isChipActive(id)) {
      removeContextChip(id);
    } else {
      addContextChip({
        id,
        label: `${ins.author}: ${ins.text.slice(0, 30)}…`,
        text: `[Insight ${ins.timestamp} · ${ins.author}] ${ins.text}`,
      });
    }
  };

  const toggleObjectiveChip = (obj: string, idx: number) => {
    const id = `obj-${idx}`;
    if (isChipActive(id)) {
      removeContextChip(id);
    } else {
      addContextChip({ id, label: obj.slice(0, 30), text: `Objetivo cliente: ${obj}` });
    }
  };

  const togglePainChip = (pp: string, idx: number) => {
    const id = `pp-${idx}`;
    if (isChipActive(id)) {
      removeContextChip(id);
    } else {
      addContextChip({ id, label: pp.slice(0, 30), text: `Pain point: ${pp}` });
    }
  };

  return (
    <div className="neo-context-panel">
      <button
        type="button"
        className="neo-context-panel__header"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <User className="h-4 w-4 text-cyan-300" />
          <span style={{ fontSize: 12, fontWeight: 700, color: "#e4f2ff" }}>Contexto del Cliente</span>
          <span
            style={{
              fontSize: 9,
              padding: "1px 6px",
              borderRadius: 999,
              background: currentEmpresa !== "—" ? "rgba(110,255,170,0.12)" : "rgba(255,255,255,0.08)",
              color: currentEmpresa !== "—" ? "#8ff8be" : "#8ab0d0",
              border: "1px solid rgba(255,255,255,0.1)",
            }}
          >
            {currentEmpresa !== "—" ? currentEmpresa : "Sin sesión"}
          </span>
        </div>
        {open ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
      </button>

      {open && (
        <div className="neo-context-panel__body">
          <p style={{ fontSize: 10, color: "#7a93b8", marginBottom: 2 }}>
            {currentArea !== "—" ? `Área: ${currentArea}` : "Selecciona una empresa para activar su perfil"}
          </p>
          <p style={{ fontSize: 9, color: "#5a6e88", marginTop: -2 }}>
            Haz clic en cualquier item para añadirlo al chat
          </p>

          {objetivos.length > 0 && (
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 5 }}>
                <TrendingUp className="h-3 w-3 text-cyan-400" />
                <span style={{ fontSize: 9, color: "#7dd9f7", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                  Objetivos
                </span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {objetivos.map((obj, i) => (
                  <button
                    key={i}
                    type="button"
                    className={`neo-chip-btn${isChipActive(`obj-${i}`) ? " neo-chip-btn--active" : ""}`}
                    onClick={() => toggleObjectiveChip(obj, i)}
                  >
                    {obj.length > 32 ? obj.slice(0, 32) + "…" : obj}
                  </button>
                ))}
              </div>
            </div>
          )}

          {painPoints.length > 0 && (
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 5 }}>
                <AlertTriangle className="h-3 w-3 text-amber-400" />
                <span style={{ fontSize: 9, color: "#ffd89f", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                  Pain Points
                </span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {painPoints.map((pp, i) => (
                  <button
                    key={i}
                    type="button"
                    className={`neo-chip-btn${isChipActive(`pp-${i}`) ? " neo-chip-btn--active" : ""}`}
                    onClick={() => togglePainChip(pp, i)}
                  >
                    {pp.length > 32 ? pp.slice(0, 32) + "…" : pp}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 5 }}>
              <MessageSquare className="h-3 w-3 text-violet-400" />
              <span style={{ fontSize: 9, color: "#c9b8ff", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                Insights del equipo
              </span>
              <span style={{ fontSize: 8, color: "#5a6e88", marginLeft: 4 }}>datos demo</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              {DUMMY_INSIGHTS.map((ins, i) => {
                const s = SENTIMENT_COLOR[ins.sentiment] ?? SENTIMENT_COLOR.neutral;
                const active = isChipActive(`insight-${i}`);
                return (
                  <button
                    key={i}
                    type="button"
                    onClick={() => toggleInsightChip(ins, i)}
                    style={{
                      background: active ? "rgba(108,140,255,0.14)" : "rgba(255,255,255,0.04)",
                      border: `1px solid ${active ? "rgba(108,140,255,0.45)" : "rgba(255,255,255,0.1)"}`,
                      borderRadius: 9,
                      padding: "6px 8px",
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "background 140ms ease, border-color 140ms ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                      <span style={{ fontSize: 10, color: s.dot, fontWeight: 700, display: "flex", alignItems: "center", gap: 4 }}>
                        <span style={{ width: 6, height: 6, borderRadius: "50%", background: s.dot, display: "inline-block" }} />
                        {ins.author} · {s.label}
                      </span>
                      <span style={{ fontSize: 9, color: "#5a6e88" }}>{ins.timestamp}</span>
                    </div>
                    <p style={{ fontSize: 11, color: active ? "#c8daf5" : "#9ab0cc", lineHeight: 1.35 }}>{ins.text}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
