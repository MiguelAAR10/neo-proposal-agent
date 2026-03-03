"use client";

import { useMemo, useState } from "react";
import { DndContext, DragEndEvent, DragOverlay } from "@dnd-kit/core";
import { AlertCircle } from "lucide-react";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { DraggableCaseCard } from "@/components/dashboard/DraggableCaseCard";
import { DraggableContextCard } from "@/components/dashboard/DraggableContextCard";
import { DroppableValuePropForm } from "@/components/dashboard/DroppableValuePropForm";
import { GeneratedResultView } from "@/components/dashboard/GeneratedResultView";
import { RadarIntelligencePanel } from "@/components/dashboard/RadarIntelligencePanel";
import { ValueAssistantChat } from "@/components/dashboard/ValueAssistantChat";
import { AREA_OPTIONS, useDashboardController } from "@/components/dashboard/useDashboardController";
import { getErrorMessage } from "@/lib/error";
import type { DraggableContextCard as ContextCard, DroppableCaseCard } from "@/types/dashboard";

type DragPayload =
  | { kind: "case"; payload: DroppableCaseCard }
  | { kind: "context"; payload: ContextCard };

export default function HomePage() {
  const dashboard = useDashboardController();
  const [activeDrag, setActiveDrag] = useState<DragPayload | null>(null);

  const companyOptions = useMemo(
    () => dashboard.catalog.map((entry) => ({ value: entry.name, label: entry.display_name })),
    [dashboard.catalog],
  );

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveDrag(null);
    if (!event.over || event.over.id !== "proposal-drop-zone") return;
    const dragData = event.active.data.current as DragPayload | undefined;
    if (!dragData) return;

    try {
      if (dragData.kind === "case") {
        await dashboard.onDropCase(dragData.payload);
      } else {
        await dashboard.onDropContext(dragData.payload);
      }
    } catch {
      // handled inside controller
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
            if (!dragData) return;
            setActiveDrag(dragData);
          }}
          onDragEnd={handleDragEnd}
        >
          <section className="neo-two-panel-grid">
            <aside className="neo-panel neo-panel--left">
              <div className="neo-panel-top">
                <h2 className="neo-panel-title">Controls, Inputs & Drag Zone</h2>
                <RadarIntelligencePanel cards={dashboard.contextCards} />
              </div>

              <div className="neo-controls-grid">
                <label className="neo-control-field">
                  <span>Industria</span>
                  <input
                    value={dashboard.controls.rubro}
                    onChange={(event) =>
                      dashboard.setControls((prev) => ({ ...prev, rubro: event.target.value }))
                    }
                    placeholder="Banca, Seguros, Retail..."
                  />
                </label>

                <label className="neo-control-field">
                  <span>Área</span>
                  <select
                    value={dashboard.controls.area}
                    onChange={(event) =>
                      dashboard.setControls((prev) => ({ ...prev, area: event.target.value }))
                    }
                  >
                    {AREA_OPTIONS.map((entry) => (
                      <option key={entry} value={entry}>
                        {entry}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="neo-control-field">
                  <span>Fuente</span>
                  <select
                    value={dashboard.controls.switch}
                    onChange={(event) =>
                      dashboard.setControls((prev) => ({
                        ...prev,
                        switch: event.target.value as "neo" | "ai" | "both",
                      }))
                    }
                  >
                    <option value="both">Ambos</option>
                    <option value="neo">Solo NEO</option>
                    <option value="ai">Solo AI</option>
                  </select>
                </label>
              </div>

              <label className="neo-control-field">
                <span>Problema de negocio</span>
                <textarea
                  rows={5}
                  value={dashboard.controls.problema}
                  onChange={(event) =>
                    dashboard.setControls((prev) => ({ ...prev, problema: event.target.value }))
                  }
                  placeholder="Describe dolor, impacto económico y urgencia comercial."
                />
              </label>

              <button
                type="button"
                onClick={() => dashboard.searchMutation.mutate()}
                disabled={dashboard.searchMutation.isPending || dashboard.controls.problema.trim().length < 20}
                className="neo-pill neo-pill--primary"
              >
                {dashboard.searchMutation.isPending ? "Buscando..." : "Buscar casos inteligentes"}
              </button>

              <h3 className="neo-panel-title mt-3">Fichas de Contexto Sectorial</h3>
              <div className="neo-context-list">
                {dashboard.contextCards.map((card) => (
                  <DraggableContextCard key={card.id} card={card} />
                ))}
              </div>

              <h3 className="neo-panel-title mt-3">Casos Sugeridos (arrastrables)</h3>
              <div className="neo-cases-list">
                {dashboard.visibleCases.map((card) => (
                  <DraggableCaseCard
                    key={card.id}
                    card={card}
                    isDropped={dashboard.selectedCaseIds.includes(card.id)}
                  />
                ))}
                {dashboard.visibleCases.length === 0 && (
                  <p className="neo-empty-state">
                    Ejecuta búsqueda para visualizar casos y arrastrarlos a la propuesta.
                  </p>
                )}
              </div>
            </aside>

            <section className="neo-panel neo-panel--right">
              <h2 className="neo-panel-title">Drop Zone & Intelligence Display</h2>
              <DroppableValuePropForm
                loading={dashboard.generateMutation.isPending}
                canGenerate={dashboard.selectedCaseIds.length > 0}
                onGenerate={() => dashboard.generateMutation.mutate()}
              >
                <GeneratedResultView
                  proposal={dashboard.proposal}
                  droppedCount={dashboard.selectedCaseIds.length}
                  dragMessage={dashboard.dragMessage}
                />
              </DroppableValuePropForm>

              <h3 className="neo-panel-title mt-3">ValueAssistantChat</h3>
              <ValueAssistantChat />
            </section>
          </section>

          <DragOverlay>
            {activeDrag?.kind === "case" ? (
              <div className="neo-overlay-card">
                <DraggableCaseCard card={activeDrag.payload} isDropped={false} />
              </div>
            ) : activeDrag?.kind === "context" ? (
              <div className="neo-overlay-card">
                <DraggableContextCard card={activeDrag.payload} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>

        {hasError && (
          <section className="neo-error-strip">
            <AlertCircle className="h-4 w-4" />
            <span>
              {getErrorMessage(
                dashboard.searchMutation.error ?? dashboard.generateMutation.error,
                "Se detectó un error en el flujo del dashboard.",
              )}
            </span>
          </section>
        )}
      </div>
    </main>
  );
}

