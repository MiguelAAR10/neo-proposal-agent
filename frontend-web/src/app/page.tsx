"use client";

import { useCallback, useMemo, useState } from "react";
import { DndContext, DragEndEvent, DragOverlay } from "@dnd-kit/core";
import { AlertCircle, History, WandSparkles, X } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { DraggableCaseCard } from "@/components/dashboard/DraggableCaseCard";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { NeoLoader } from "@/components/ui/NeoLoader";
import { AREA_OPTIONS, useDashboardController } from "@/components/dashboard/useDashboardController";
import { useAgentStore } from "@/stores/agentStore";
import { getErrorMessage } from "@/lib/error";
import type { DraggableContextCard, DroppableCaseCard } from "@/types/dashboard";

type DragPayload = { kind: "case"; payload: DroppableCaseCard };

// Category → icon map for sector strip
const CATEGORY_ICON: Record<string, string> = {
  risk: "⚠️",
  signal: "📡",
  macro: "🌐",
  opportunity: "💡",
};

const PROFILE_EVOLUTION_MOCK = [
  {
    period: "Hace 1 mes",
    title: "Foco en churn de banca pyme",
    detail: "Se priorizó retención sobre crecimiento y se pidió reducir fricción en onboarding.",
  },
  {
    period: "Hace 2 semanas",
    title: "Riesgo regulatorio en modelos IA",
    detail: "Aparecen requisitos de trazabilidad y control para decisiones asistidas por IA.",
  },
  {
    period: "Hoy",
    title: "Interés en automatización con ROI",
    detail: "La conversación migra a quick wins operativos con impacto financiero en menos de 12 meses.",
  },
] as const;

export default function HomePage() {
  const dashboard = useDashboardController();
  const { addContextChip, removeContextChip } = useAgentStore();
  const [activeDrag, setActiveDrag] = useState<DragPayload | null>(null);
  const [isProfileDrawerOpen, setIsProfileDrawerOpen] = useState(false);
  const [activeContextIds, setActiveContextIds] = useState<Set<string>>(new Set());
  const prefersReducedMotion = useReducedMotion();
  const shouldAnimate = !prefersReducedMotion;

  const companyOptions = useMemo(
    () => dashboard.catalog.map((entry) => ({ value: entry.name, label: entry.display_name })),
    [dashboard.catalog],
  );

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveDrag(null);
    if (!event.over) return;
    const dragData = event.active.data.current as DragPayload | undefined;
    if (!dragData || dragData.kind !== "case") return;
    if (event.over.id === "chat-drop-zone") {
      dashboard.onDropCase(dragData.payload);
    }
  };

  const toggleSectorCard = (card: DraggableContextCard) => {
    if (activeContextIds.has(card.id)) {
      removeContextChip(card.id);
      setActiveContextIds((prev) => {
        const s = new Set(prev);
        s.delete(card.id);
        return s;
      });
    } else {
      addContextChip({
        id: card.id,
        label: card.title,
        text: `${card.title}: ${card.summary}`,
      });
      setActiveContextIds((prev) => new Set([...prev, card.id]));
    }
  };

  const hasError = Boolean(dashboard.searchMutation.error || dashboard.generateMutation.error);

  const handleGenerateProposal = useCallback(() => {
    if (dashboard.generateMutation.isPending) return;
    dashboard.generateMutation.mutate();
  }, [dashboard.generateMutation]);

  return (
    <main className="neo-two-panel-page">
      {/* ── Level 1: Top Header ── */}
      <DashboardHeader
        companyLabel={`${dashboard.empresa || dashboard.controls.empresa} · ${dashboard.area || dashboard.controls.area}`}
        companyValue={dashboard.controls.empresa}
        companyOptions={companyOptions}
        onCompanyChange={dashboard.onCompanyChange}
        onReset={dashboard.reset}
      />

      <div className="neo-two-panel-container">
        {/* ── Level 2: Sector Context Strip ── */}
        <div className="neo-sector-strip">
          <span
            style={{
              fontSize: 12,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "var(--accent)",
              whiteSpace: "nowrap",
              fontFamily: "var(--font-serif), Georgia, serif",
              flexShrink: 0,
            }}
          >
            Contexto
          </span>
          {dashboard.contextCards.map((card) => (
            <button
              key={card.id}
              type="button"
              onClick={() => toggleSectorCard(card)}
              className={`neo-sector-micro-card${activeContextIds.has(card.id) ? " neo-sector-micro-card--active" : ""}`}
              title={card.summary}
            >
              <span className="neo-sector-micro-card__icon">
                {CATEGORY_ICON[card.category] ?? "📌"}
              </span>
              <span className="neo-sector-micro-card__label">{card.title}</span>
              {card.severity === "high" && (
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "#f87171",
                    flexShrink: 0,
                  }}
                />
              )}
            </button>
          ))}
        </div>

        <DndContext
          onDragStart={(event) => {
            const dragData = event.active.data.current as DragPayload | undefined;
            if (dragData?.kind === "case") setActiveDrag(dragData);
          }}
          onDragEnd={handleDragEnd}
        >
          <div className="neo-app-body">

            {/* ── SLIM SIDEBAR: filters only ── */}
            <motion.aside
              className="neo-left-col"
              initial={shouldAnimate ? { opacity: 0, x: -8 } : false}
              animate={shouldAnimate ? { opacity: 1, x: 0 } : undefined}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            >
              {/* Filter section */}
              <div className="neo-sidebar-section">
                <h3 className="neo-panel-title">Filtros de Búsqueda</h3>
                <div className="neo-controls-grid">
                  <label className="neo-control-field">
                    <span>Industria</span>
                    <input
                      value={dashboard.controls.rubro}
                      onChange={(e) => dashboard.setControls((prev) => ({ ...prev, rubro: e.target.value }))}
                      placeholder="Banca, Seguros, Retail..."
                    />
                  </label>
                  <label className="neo-control-field">
                    <span>Área funcional</span>
                    <select
                      value={dashboard.controls.area}
                      onChange={(e) => dashboard.setControls((prev) => ({ ...prev, area: e.target.value }))}
                    >
                      {AREA_OPTIONS.map((entry) => (
                        <option key={entry} value={entry}>{entry}</option>
                      ))}
                    </select>
                  </label>
                  <label className="neo-control-field">
                    <span>Fuente de casos</span>
                    <select
                      value={dashboard.controls.switch}
                      onChange={(e) =>
                        dashboard.setControls((prev) => ({
                          ...prev,
                          switch: e.target.value as "neo" | "ai" | "both",
                        }))
                      }
                    >
                      <option value="both">Ambos (NEO + AI)</option>
                      <option value="neo">Solo NEO</option>
                      <option value="ai">Solo AI Global</option>
                    </select>
                  </label>
                </div>

                <div className="neo-profile-controls">
                  <div className="neo-profile-toggle-row">
                    <button
                      type="button"
                      role="switch"
                      aria-checked={dashboard.useClientProfile}
                      aria-label="Considerar perfil histórico del cliente"
                      onClick={() => dashboard.setUseClientProfile(!dashboard.useClientProfile)}
                      className={`neo-profile-switch${dashboard.useClientProfile ? " neo-profile-switch--on" : ""}`}
                    >
                      <span className="neo-profile-switch__thumb" />
                    </button>
                    <div className="neo-profile-toggle-copy">
                      <span className="neo-profile-toggle-label">Perfil histórico</span>
                      <span className="neo-profile-toggle-help">Usa señales previas.</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="neo-ghost-mini"
                    onClick={() => setIsProfileDrawerOpen(true)}
                  >
                    <History size={13} />
                    Evolución
                  </button>
                </div>
              </div>
            </motion.aside>

            {/* ── WORK AREA ── */}
            <section className="neo-right-col">

              {/* Problem block: the primary focus */}
              <div className="neo-problem-block">
                <label style={{ display: "block" }}>
                  <span className="neo-problem-block__label">Problema de Negocio</span>
                  <textarea
                    className="neo-problem-block__textarea"
                    rows={3}
                    value={dashboard.controls.problema}
                    onChange={(e) => dashboard.setControls((prev) => ({ ...prev, problema: e.target.value }))}
                    placeholder="Describe el dolor comercial, impacto económico y urgencia. A mayor contexto, mejor la propuesta de valor generada."
                  />
                </label>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
                  <button
                    type="button"
                    onClick={() => dashboard.searchMutation.mutate()}
                    disabled={
                      dashboard.searchMutation.isPending || dashboard.controls.problema.trim().length < 20
                    }
                    className="neo-pill neo-pill--primary"
                    style={{ flex: "0 0 auto" }}
                  >
                    {dashboard.searchMutation.isPending ? "Buscando..." : "Buscar casos inteligentes"}
                  </button>
                  {dashboard.searchMutation.isPending && (
                    <NeoLoader compact className="flex-1" />
                  )}
                </div>
              </div>

              {/* Work split: cases + chat */}
              <div className="neo-work-split">

                {/* Cases column — shown when cases are found */}
                {dashboard.visibleCases.length > 0 && (
                  <div className="neo-cases-col">
                    <div className="neo-cases-col__header">
                      <span
                        style={{
                          fontSize: 13,
                          fontWeight: 700,
                          textTransform: "uppercase" as const,
                          letterSpacing: "0.08em",
                          color: "var(--accent)",
                          fontFamily: "var(--font-serif), Georgia, serif",
                        }}
                      >
                        Casos sugeridos · {dashboard.visibleCases.length}
                      </span>
                      <span
                        style={{
                          fontSize: 12,
                          color: "var(--text-muted)",
                          fontFamily: "var(--font-mono), monospace",
                        }}
                      >
                        {dashboard.selectedCaseIds.length} sel.
                      </span>
                    </div>

                    <div className="neo-cases-col__scroll">
                      <motion.div
                        key={`${dashboard.threadId ?? "idle"}-${dashboard.visibleCases.length}`}
                        initial={shouldAnimate ? "hidden" : false}
                        animate={shouldAnimate ? "show" : undefined}
                        variants={{
                          hidden: { opacity: 0 },
                          show: {
                            opacity: 1,
                            transition: { staggerChildren: 0.04 },
                          },
                        }}
                        style={{ display: "grid", gap: 7 }}
                      >
                        {dashboard.visibleCases.map((card) => (
                          <motion.div
                            key={card.id}
                            variants={{
                              hidden: { opacity: 0, y: 8 },
                              show: {
                                opacity: 1,
                                y: 0,
                                transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] },
                              },
                            }}
                          >
                            <DraggableCaseCard
                              card={card}
                              isDropped={dashboard.selectedCaseIds.includes(card.id)}
                              onToggle={dashboard.onToggleCase}
                            />
                          </motion.div>
                        ))}
                      </motion.div>
                    </div>

                    {/* Generate button at bottom of cases column */}
                    {dashboard.selectedCaseIds.length > 0 && (
                      <div className="neo-generate-bar">
                        <span
                          style={{
                            fontSize: 13,
                            color: "var(--text-muted)",
                            fontFamily: "var(--font-body), sans-serif",
                            fontWeight: 500,
                          }}
                        >
                          {dashboard.selectedCaseIds.length} caso{dashboard.selectedCaseIds.length !== 1 ? "s" : ""} seleccionado{dashboard.selectedCaseIds.length !== 1 ? "s" : ""}
                        </span>
                        <button
                          type="button"
                          onClick={handleGenerateProposal}
                          disabled={Boolean(dashboard.generateMutation.isPending)}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: 6,
                            padding: "8px 16px",
                            border: "none",
                            background: "linear-gradient(135deg, #05058c, #7ba3f0)",
                            color: "#ffffff",
                            borderRadius: 10,
                            fontSize: 14,
                            fontWeight: 700,
                            fontFamily: "var(--font-body), sans-serif",
                            cursor: "pointer",
                            opacity: dashboard.generateMutation.isPending ? 0.6 : 1,
                            boxShadow: "0 0 15px rgba(123,163,240,0.3)",
                            transition: "all 250ms ease",
                          }}
                        >
                          <WandSparkles size={13} />
                          {dashboard.generateMutation.isPending ? "Generando..." : "Generar Propuesta"}
                        </button>
                      </div>
                    )}
                    {dashboard.generateMutation.isPending && (
                      <NeoLoader compact className="border-t-0 rounded-none" />
                    )}
                  </div>
                )}

                {/* Chat column */}
                <div className="neo-chat-col">
                  <ChatPanel isGenerating={dashboard.generateMutation.isPending} />
                </div>
              </div>
            </section>

          </div>

          {/* DragOverlay */}
          <DragOverlay>
            {activeDrag?.kind === "case" && (
              <div style={{ width: 320, opacity: 0.88 }}>
                <DraggableCaseCard card={activeDrag.payload} isDropped={false} />
              </div>
            )}
          </DragOverlay>
        </DndContext>

        {hasError && (
          <div className="neo-error-strip" style={{ margin: "0 16px 10px" }}>
            <AlertCircle className="h-4 w-4 shrink-0" style={{ color: "#f87171" }} />
            <span>
              {getErrorMessage(
                dashboard.searchMutation.error ?? dashboard.generateMutation.error,
                "Se detectó un error en el flujo.",
              )}
            </span>
          </div>
        )}
      </div>

      {/* Profile evolution drawer */}
      <div
        className={`neo-profile-drawer-backdrop${isProfileDrawerOpen ? " is-open" : ""}`}
        onClick={() => setIsProfileDrawerOpen(false)}
      />
      <aside
        className={`neo-profile-drawer${isProfileDrawerOpen ? " is-open" : ""}`}
        aria-hidden={!isProfileDrawerOpen}
        aria-label="Evolución del perfil del cliente"
      >
        <div className="neo-profile-drawer__header">
          <div>
            <p className="neo-profile-drawer__kicker">Perfil del cliente</p>
            <h3 className="neo-profile-drawer__title">Evolución estratégica</h3>
          </div>
          <button
            type="button"
            className="neo-ghost-mini neo-ghost-mini--icon"
            onClick={() => setIsProfileDrawerOpen(false)}
          >
            <X size={14} />
          </button>
        </div>
        <div className="neo-profile-timeline">
          {PROFILE_EVOLUTION_MOCK.map((entry) => (
            <article key={entry.period} className="neo-profile-timeline__item">
              <span className="neo-profile-timeline__period">{entry.period}</span>
              <p className="neo-profile-timeline__title">{entry.title}</p>
              <p className="neo-profile-timeline__detail">{entry.detail}</p>
            </article>
          ))}
        </div>
      </aside>
    </main>
  );
}
