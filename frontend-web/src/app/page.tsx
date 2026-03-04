"use client";

import { useCallback, useMemo, useState } from "react";
import { DndContext, DragEndEvent, DragOverlay } from "@dnd-kit/core";
import { AlertCircle, History, X } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { DraggableCaseCard } from "@/components/dashboard/DraggableCaseCard";
import { DraggableContextCard } from "@/components/dashboard/DraggableContextCard";
import { ClientProfilePanel } from "@/components/dashboard/ClientProfilePanel";
import { RadarIntelligencePanel } from "@/components/dashboard/RadarIntelligencePanel";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { NeoLoader } from "@/components/ui/NeoLoader";
import { AREA_OPTIONS, useDashboardController } from "@/components/dashboard/useDashboardController";
import { getErrorMessage } from "@/lib/error";
import type { DroppableCaseCard } from "@/types/dashboard";

type DragPayload = { kind: "case"; payload: DroppableCaseCard };

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
  const [activeDrag, setActiveDrag] = useState<DragPayload | null>(null);
  const [isProfileDrawerOpen, setIsProfileDrawerOpen] = useState(false);
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

    // Al arrastrar caso al chat → seleccionar + añadir chip de contexto
    if (event.over.id === "chat-drop-zone") {
      dashboard.onDropCase(dragData.payload);
    }
  };

  const hasError = Boolean(dashboard.searchMutation.error || dashboard.generateMutation.error);
  const handleGenerateProposal = useCallback(() => {
    if (dashboard.generateMutation.isPending) return;
    dashboard.generateMutation.mutate();
  }, [dashboard.generateMutation]);

  return (
    <main className="neo-two-panel-page animated-grid-bg h-screen w-full flex overflow-hidden bg-[#0A0A0A]">
      <DashboardHeader
        companyLabel={`${dashboard.empresa || dashboard.controls.empresa} · ${dashboard.area || dashboard.controls.area}`}
        companyValue={dashboard.controls.empresa}
        companyOptions={companyOptions}
        onCompanyChange={dashboard.onCompanyChange}
        onReset={dashboard.reset}
      />

      <div className="neo-two-panel-container">
        <DndContext
          onDragStart={(event) => {
            const dragData = event.active.data.current as DragPayload | undefined;
            if (dragData?.kind === "case") setActiveDrag(dragData);
          }}
          onDragEnd={handleDragEnd}
        >
          <div className="neo-app-body">

            {/* ── PANEL IZQUIERDO ── */}
            <motion.aside
              className="neo-left-col neo-panel"
              initial={shouldAnimate ? { opacity: 0, y: 10 } : false}
              animate={shouldAnimate ? { opacity: 1, y: 0 } : undefined}
              transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
            >

              {/* Contexto del cliente */}
              <ClientProfilePanel />

              {/* Fichas de contexto sectorial */}
              <div>
                <h3 className="neo-panel-title">Contexto Sectorial</h3>
                <motion.div
                  className="neo-context-list"
                  initial={shouldAnimate ? "hidden" : false}
                  animate={shouldAnimate ? "show" : undefined}
                  variants={{
                    hidden: { opacity: 0 },
                    show: { opacity: 1, transition: { staggerChildren: 0.06, delayChildren: 0.05 } },
                  }}
                >
                  {dashboard.contextCards.map((card) => (
                    <motion.div
                      key={card.id}
                      variants={{
                        hidden: { opacity: 0, y: 8 },
                        show: { opacity: 1, y: 0, transition: { duration: 0.24, ease: [0.22, 1, 0.36, 1] } },
                      }}
                    >
                      <DraggableContextCard card={card} />
                    </motion.div>
                  ))}
                </motion.div>
              </div>

              {/* Radar mini */}
              <RadarIntelligencePanel cards={dashboard.contextCards} />

              {/* Inputs de búsqueda */}
              <div>
                <h3 className="neo-panel-title">Búsqueda de Casos</h3>
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
                        dashboard.setControls((prev) => ({ ...prev, switch: e.target.value as "neo" | "ai" | "both" }))
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
                    <div className="neo-profile-toggle-copy">
                      <span className="neo-profile-toggle-label">Considerar Perfil Histórico del Cliente</span>
                      <span className="neo-profile-toggle-help">
                        Usa señales previas del cliente al proponer estrategia.
                      </span>
                    </div>
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
                  </div>
                  <button type="button" className="neo-ghost-mini" onClick={() => setIsProfileDrawerOpen(true)}>
                    <History size={14} />
                    Ver evolución
                  </button>
                </div>

                <label className="neo-control-field" style={{ marginTop: 8 }}>
                  <span>Problema de negocio</span>
                  <textarea
                    rows={4}
                    value={dashboard.controls.problema}
                    onChange={(e) => dashboard.setControls((prev) => ({ ...prev, problema: e.target.value }))}
                    placeholder="Describe el dolor, impacto económico y urgencia comercial."
                  />
                </label>

                <button
                  type="button"
                  onClick={() => dashboard.searchMutation.mutate()}
                  disabled={dashboard.searchMutation.isPending || dashboard.controls.problema.trim().length < 20}
                  className="neo-pill neo-pill--primary"
                  style={{ width: "100%", marginTop: 10 }}
                >
                  {dashboard.searchMutation.isPending ? "Procesando busqueda..." : "Buscar casos inteligentes"}
                </button>

                {dashboard.searchMutation.isPending && (
                  <NeoLoader className="mt-2" />
                )}
              </div>

              {/* Casos encontrados */}
              {dashboard.visibleCases.length > 0 && (
                <div>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                    <h3 className="neo-panel-title" style={{ marginBottom: 0 }}>
                      Casos sugeridos
                    </h3>
                    <span style={{ fontSize: 10, color: "#a1a1aa", fontFamily: "var(--font-mono), monospace" }}>
                      {dashboard.selectedCaseIds.length} seleccionado{dashboard.selectedCaseIds.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div className="neo-cases-list">
                    <motion.div
                      key={`${dashboard.threadId ?? "idle"}-${dashboard.visibleCases.length}`}
                      initial={shouldAnimate ? "hidden" : false}
                      animate={shouldAnimate ? "show" : undefined}
                      variants={{
                        hidden: { opacity: 0 },
                        show: { opacity: 1, transition: { staggerChildren: 0.045 } },
                      }}
                      style={{ display: "grid", gap: 7 }}
                    >
                      {dashboard.visibleCases.map((card) => (
                        <motion.div
                          key={card.id}
                          variants={{
                            hidden: { opacity: 0, y: 10 },
                            show: { opacity: 1, y: 0, transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] } },
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
                </div>
              )}

              {dashboard.visibleCases.length === 0 && !dashboard.searchMutation.isPending && (
                <p className="neo-empty-state">
                  Ejecuta una búsqueda para ver casos y seleccionar los más relevantes.
                </p>
              )}

            </motion.aside>

            {/* ── PANEL DERECHO: CHAT CENTRO DE MANDO ── */}
            <section className="neo-right-col">
              <div className="neo-chat-shell p-4 h-full flex flex-col">
                <div className="neo-chat-frame flex-1 overflow-y-auto rounded-xl border border-zinc-800 bg-[#121212]/80 backdrop-blur-md">
                  <ChatPanel
                    onGenerate={handleGenerateProposal}
                    isGenerating={dashboard.generateMutation.isPending}
                  />
                </div>
              </div>
            </section>

          </div>

          {/* DragOverlay */}
          <DragOverlay>
            {activeDrag?.kind === "case" && (
              <div style={{ width: 380, opacity: 0.88 }}>
                <DraggableCaseCard card={activeDrag.payload} isDropped={false} />
              </div>
            )}
          </DragOverlay>
        </DndContext>

        {hasError && (
          <div className="neo-error-strip" style={{ margin: "0 18px 10px" }}>
            <AlertCircle className="h-4 w-4" />
            <span>
              {getErrorMessage(
                dashboard.searchMutation.error ?? dashboard.generateMutation.error,
                "Se detectó un error en el flujo.",
              )}
            </span>
          </div>
        )}
      </div>

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
