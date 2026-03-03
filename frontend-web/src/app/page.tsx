"use client";

import { useMemo, useState } from "react";
import { DndContext, DragEndEvent, DragOverlay } from "@dnd-kit/core";
import { AlertCircle } from "lucide-react";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { DraggableCaseCard } from "@/components/dashboard/DraggableCaseCard";
import { DraggableContextCard } from "@/components/dashboard/DraggableContextCard";
import { ClientProfilePanel } from "@/components/dashboard/ClientProfilePanel";
import { RadarIntelligencePanel } from "@/components/dashboard/RadarIntelligencePanel";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { AREA_OPTIONS, useDashboardController } from "@/components/dashboard/useDashboardController";
import { useAgentStore } from "@/stores/agentStore";
import { getErrorMessage } from "@/lib/error";
import type { DroppableCaseCard } from "@/types/dashboard";

type DragPayload = { kind: "case"; payload: DroppableCaseCard };

export default function HomePage() {
  const dashboard = useDashboardController();
  const { addContextChip } = useAgentStore();
  const [activeDrag, setActiveDrag] = useState<DragPayload | null>(null);

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

  return (
    <main className="neo-two-panel-page">
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
            <aside className="neo-left-col neo-panel">

              {/* Contexto del cliente */}
              <ClientProfilePanel />

              {/* Fichas de contexto sectorial */}
              <div>
                <h3 className="neo-panel-title">Contexto Sectorial</h3>
                <div className="neo-context-list">
                  {dashboard.contextCards.map((card) => (
                    <DraggableContextCard key={card.id} card={card} />
                  ))}
                </div>
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
                  {dashboard.searchMutation.isPending ? "Buscando casos…" : "Buscar casos inteligentes"}
                </button>
              </div>

              {/* Casos encontrados */}
              {dashboard.visibleCases.length > 0 && (
                <div>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                    <h3 className="neo-panel-title" style={{ marginBottom: 0 }}>
                      Casos sugeridos
                    </h3>
                    <span style={{ fontSize: 10, color: "#7a93b8" }}>
                      {dashboard.selectedCaseIds.length} seleccionado{dashboard.selectedCaseIds.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div className="neo-cases-list">
                    {dashboard.visibleCases.map((card) => (
                      <DraggableCaseCard
                        key={card.id}
                        card={card}
                        isDropped={dashboard.selectedCaseIds.includes(card.id)}
                        onToggle={dashboard.onToggleCase}
                      />
                    ))}
                  </div>
                </div>
              )}

              {dashboard.visibleCases.length === 0 && !dashboard.searchMutation.isPending && (
                <p className="neo-empty-state">
                  Ejecuta una búsqueda para ver casos y seleccionar los más relevantes.
                </p>
              )}

            </aside>

            {/* ── PANEL DERECHO: CHAT CENTRO DE MANDO ── */}
            <section className="neo-right-col">
              <ChatPanel
                onGenerate={() => dashboard.generateMutation.mutate()}
                isGenerating={dashboard.generateMutation.isPending}
              />
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
    </main>
  );
}
