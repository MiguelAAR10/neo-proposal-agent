"use client";

import { useEffect, useState } from "react";

const PHRASES = [
  "> INICIALIZANDO MOTORES NEO...",
  "> CONECTANDO A BASE VECTORIAL...",
  "> ANALIZANDO CONTEXTO SECTORIAL...",
  "> SINTETIZANDO INTELIGENCIA ESTRATEGICA...",
] as const;

interface NeoLoaderProps {
  compact?: boolean;
  className?: string;
}

export function NeoLoader({ compact = false, className = "" }: NeoLoaderProps) {
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [cycle, setCycle] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setPhraseIndex((prev) => (prev + 1) % PHRASES.length);
      setCycle((prev) => prev + 1);
    }, 1500);

    return () => {
      window.clearInterval(interval);
    };
  }, []);

  const fillLine = cycle % 2 === 1;

  return (
    <div className={`neo-loader${compact ? " neo-loader--compact" : ""}${className ? ` ${className}` : ""}`}>
      <div className="inline-flex items-center gap-2 text-xs font-mono text-[#7ba3f0] tracking-widest uppercase">
        <span className="h-2 w-px bg-[#7ba3f0] animate-pulse" aria-hidden="true" />
        <span>{PHRASES[phraseIndex]}</span>
      </div>
      <div className="mt-2 h-px w-full overflow-hidden bg-[#1e2a6e]" aria-hidden="true">
        <div
          className={`h-px bg-[#7ba3f0] transition-[width] duration-[1400ms] ease-linear ${fillLine ? "w-full" : "w-0"}`}
        />
      </div>
    </div>
  );
}
