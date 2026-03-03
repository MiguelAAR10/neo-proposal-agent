"use client";

import { useDroppable } from "@dnd-kit/core";
import { Inbox, Loader2 } from "lucide-react";

interface ProposalDropZoneProps {
  children: React.ReactNode;
  loading: boolean;
}

export function ProposalDropZone({ children, loading }: ProposalDropZoneProps) {
  const { setNodeRef, isOver } = useDroppable({ id: "proposal-drop-zone" });

  return (
    <section ref={setNodeRef} className={`neo-drop-zone ${isOver ? "neo-drop-zone--over" : ""}`}>
      <div className="neo-drop-zone__hint">
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Inbox className="h-4 w-4" />}
        Arrastra una ficha aquí para inyectar insight automáticamente
      </div>
      {children}
    </section>
  );
}

