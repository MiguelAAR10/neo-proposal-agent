"use client";

import { Copy, CheckCheck } from "lucide-react";
import { useState } from "react";

interface GeneratedResultViewProps {
  proposal: string | null;
  droppedCount: number;
  dragMessage: string | null;
}

function renderMarkdown(text: string): React.ReactNode[] {
  const paragraphs = text.split(/\n{2,}/);
  return paragraphs.map((block, i) => {
    const trimmed = block.trim();
    if (!trimmed) return null;

    if (/^#{1,3} /.test(trimmed)) {
      const content = trimmed.replace(/^#{1,3} /, "");
      return (
        <h3 key={i} style={{ fontSize: 13, fontWeight: 700, color: "#f4f9ff", marginBottom: 4, marginTop: i > 0 ? 12 : 0 }}>
          {inlineFormat(content)}
        </h3>
      );
    }

    const lines = trimmed.split("\n");
    if (lines.every((l) => /^[-*] /.test(l.trim()))) {
      return (
        <ul key={i} style={{ paddingLeft: 14, marginBottom: 8, marginTop: i > 0 ? 4 : 0 }}>
          {lines.map((l, j) => (
            <li key={j} style={{ fontSize: 12, color: "#c3d2f1", lineHeight: 1.5, marginBottom: 2 }}>
              {inlineFormat(l.replace(/^[-*] /, ""))}
            </li>
          ))}
        </ul>
      );
    }

    if (/^\d+\. /.test(lines[0]?.trim() ?? "")) {
      return (
        <ol key={i} style={{ paddingLeft: 16, marginBottom: 8, marginTop: i > 0 ? 4 : 0 }}>
          {lines.map((l, j) => (
            <li key={j} style={{ fontSize: 12, color: "#c3d2f1", lineHeight: 1.5, marginBottom: 2 }}>
              {inlineFormat(l.replace(/^\d+\. /, ""))}
            </li>
          ))}
        </ol>
      );
    }

    return (
      <p key={i} style={{ fontSize: 12, color: "#c3d2f1", lineHeight: 1.55, marginBottom: 8 }}>
        {inlineFormat(trimmed)}
      </p>
    );
  }).filter(Boolean);
}

function inlineFormat(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) {
      return <strong key={i} style={{ color: "#f4f9ff", fontWeight: 700 }}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

export function GeneratedResultView({ proposal, droppedCount, dragMessage }: GeneratedResultViewProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!proposal) return;
    await navigator.clipboard.writeText(proposal);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isEmpty = !proposal?.trim();

  return (
    <section className="neo-generated-result">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <p className="neo-drop-feedback">
          Fichas aplicadas: <strong style={{ color: "#7bf7ff" }}>{droppedCount}</strong>
          {dragMessage ? ` · ${dragMessage}` : ""}
        </p>
        {!isEmpty && (
          <button
            type="button"
            onClick={handleCopy}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 11,
              color: copied ? "#8ff8be" : "#a9ddff",
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: 8,
              padding: "3px 8px",
              cursor: "pointer",
            }}
          >
            {copied ? <CheckCheck className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? "Copiado" : "Copiar"}
          </button>
        )}
      </div>

      <div className="neo-proposal-output">
        {isEmpty ? (
          <p style={{ fontSize: 12, color: "#8ab0d0", fontStyle: "italic" }}>
            Aún no hay propuesta generada. Arrastra casos o contextos y haz clic en generar.
          </p>
        ) : (
          renderMarkdown(proposal!)
        )}
      </div>
    </section>
  );
}
