"use client";

interface GeneratedResultViewProps {
  proposal: string | null;
  droppedCount: number;
  dragMessage: string | null;
}

export function GeneratedResultView({ proposal, droppedCount, dragMessage }: GeneratedResultViewProps) {
  return (
    <section className="neo-generated-result">
      <p className="neo-generated-meta">
        Fichas aplicadas: {droppedCount}
        {dragMessage ? ` · ${dragMessage}` : ""}
      </p>
      <pre>
        {(proposal ?? "").trim() || "Aún no hay propuesta generada. Arrastra casos o contextos y haz clic en generar."}
      </pre>
    </section>
  );
}
