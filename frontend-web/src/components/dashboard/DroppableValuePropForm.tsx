"use client";

import { WandSparkles } from "lucide-react";
import { ProposalDropZone } from "@/components/dashboard/ProposalDropZone";

interface DroppableValuePropFormProps {
  loading: boolean;
  canGenerate: boolean;
  onGenerate: () => void;
  children: React.ReactNode;
}

export function DroppableValuePropForm({
  loading,
  canGenerate,
  onGenerate,
  children,
}: DroppableValuePropFormProps) {
  return (
    <ProposalDropZone loading={loading}>
      <div className="neo-proposal-card">
        <div className="neo-proposal-card__header">
          <h2>Droppable Value Prop Form</h2>
          <button type="button" className="neo-pill neo-pill--primary" onClick={onGenerate} disabled={!canGenerate || loading}>
            <WandSparkles className="h-4 w-4" />
            Generar propuesta
          </button>
        </div>
        {children}
      </div>
    </ProposalDropZone>
  );
}

