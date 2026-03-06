"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, User, MessageSquare, AlertTriangle, TrendingUp } from "lucide-react";
import { useAgentStore } from "@/stores/agentStore";
import type { ClientProfileInsight } from "@/types/dashboard";

const DUMMY_INSIGHTS: ClientProfileInsight[] = [
  {
    author: "Ana R.",
    text: "Prioridad Q2: reducir friccion en onboarding de PYMEs. Meta: bajar de 8 pasos a 3.",
    timestamp: "28 Feb 2026",
    sentiment: "positive",
  },
  {
    author: "Carlos M.",
    text: "Preocupacion por cumplimiento SBS en modelos de scoring. Piden trazabilidad de decisiones.",
    timestamp: "15 Feb 2026",
    sentiment: "neutral",
  },
  {
    author: "Ana R.",
    text: "Presupuesto congelado en H1 para infraestructura core. Oportunidad en iniciativas agiles de bajo capex.",
    timestamp: "20 Ene 2026",
    sentiment: "negative",
  },
];

const TAG_CLASS =
  "px-2 py-1 bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs font-mono uppercase tracking-wider";

export function ClientProfilePanel() {
  const [open, setOpen] = useState(true);
  const { empresa, area, perfilCliente, contextChips, addContextChip, removeContextChip } = useAgentStore();

  const currentEmpresa = empresa || "-";
  const currentArea = area || "-";

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
        label: `${ins.author}: ${ins.text.slice(0, 30)}...`,
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
        <div className="flex items-center gap-2">
          <User className="h-4 w-4 text-zinc-400" />
          <span className="text-xs font-semibold text-zinc-50">Perfil del Cliente</span>
          <span className={`${TAG_CLASS} ${currentEmpresa !== "-" ? "neo-tag--active" : ""}`}>
            {currentEmpresa !== "-" ? currentEmpresa : "Sin sesion"}
          </span>
        </div>
        {open ? <ChevronUp className="h-4 w-4 text-zinc-400" /> : <ChevronDown className="h-4 w-4 text-zinc-400" />}
      </button>

      {open && (
        <div className="neo-context-panel__body">
          <p className="text-[11px] font-mono font-bold text-zinc-400">
            {currentArea !== "-" ? `Area: ${currentArea}` : "Selecciona una empresa para activar su perfil"}
          </p>
          <p className="text-[11px] text-zinc-400">Haz clic en cualquier item para anadirlo al chat</p>

          {objetivos.length > 0 && (
            <div>
              <div className="mb-1 flex items-center gap-1.5">
                <TrendingUp className="h-3 w-3 text-zinc-400" />
                <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-zinc-50">Objetivos</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {objetivos.map((obj, i) => (
                  <button
                    key={i}
                    type="button"
                    className={`${TAG_CLASS} ${isChipActive(`obj-${i}`) ? "neo-tag--active" : ""}`}
                    onClick={() => toggleObjectiveChip(obj, i)}
                  >
                    {obj.length > 32 ? `${obj.slice(0, 32)}...` : obj}
                  </button>
                ))}
              </div>
            </div>
          )}

          {painPoints.length > 0 && (
            <div>
              <div className="mb-1 flex items-center gap-1.5">
                <AlertTriangle className="h-3 w-3 text-zinc-400" />
                <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-zinc-50">Pain Points</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {painPoints.map((pp, i) => (
                  <button
                    key={i}
                    type="button"
                    className={`${TAG_CLASS} ${isChipActive(`pp-${i}`) ? "neo-tag--active" : ""}`}
                    onClick={() => togglePainChip(pp, i)}
                  >
                    {pp.length > 32 ? `${pp.slice(0, 32)}...` : pp}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <div className="mb-1 flex items-center gap-1.5">
              <MessageSquare className="h-3 w-3 text-zinc-400" />
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-zinc-50">Insights del equipo</span>
            </div>
            <div className="flex flex-col gap-2">
              {DUMMY_INSIGHTS.map((ins, i) => {
                const active = isChipActive(`insight-${i}`);
                return (
                  <button
                    key={i}
                    type="button"
                    onClick={() => toggleInsightChip(ins, i)}
                    className={`w-full rounded-md border p-3 text-left ${active ? "border-violet-400" : "border-zinc-800"} bg-[#121212]`}
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <span className={`inline-flex items-center gap-1 text-[11px] font-mono font-bold ${active ? "text-violet-400" : "text-zinc-400"}`}>
                        <span className={`inline-block h-1.5 w-1.5 rounded-sm ${active ? "bg-violet-400" : "bg-zinc-500"}`} />
                        {ins.author}
                      </span>
                      <span className="text-[11px] font-mono text-zinc-400">{ins.timestamp}</span>
                    </div>
                    <p className="text-[11px] leading-relaxed text-zinc-300">{ins.text}</p>
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
