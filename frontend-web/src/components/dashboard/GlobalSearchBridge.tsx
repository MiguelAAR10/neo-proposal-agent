"use client";

import { Search } from "lucide-react";

interface GlobalSearchBridgeProps {
  value: string;
  onChange: (value: string) => void;
}

export function GlobalSearchBridge({ value, onChange }: GlobalSearchBridgeProps) {
  return (
    <section className="neo-search-bridge">
      <Search className="h-5 w-5 text-slate-300" />
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Busca por problema, tecnología, KPI o empresa para filtrar casos en tiempo real..."
        className="neo-search-bridge__input"
      />
    </section>
  );
}

