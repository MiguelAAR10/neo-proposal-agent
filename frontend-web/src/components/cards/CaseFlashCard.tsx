'use client'

import { useMemo, useState } from 'react'
import { ExternalLink, CheckCircle2, Circle, Sparkles } from 'lucide-react'
import { useAgentStore, type Case } from '@/stores/agentStore'

interface CaseFlashCardProps {
  caseData: Case
}

function hashToHue(input: string): number {
  let hash = 0
  for (let i = 0; i < input.length; i += 1) {
    hash = input.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash) % 360
}

function initials(name: string): string {
  const raw = (name || 'N/A').trim()
  if (!raw) return 'NA'
  const parts = raw.split(/\s+/).slice(0, 2)
  return parts.map((p) => p[0]?.toUpperCase() || '').join('') || 'NA'
}

export function CaseFlashCard({ caseData }: CaseFlashCardProps) {
  const { selectedCaseIds, selectCase, unselectCase } = useAgentStore()
  const isSelected = selectedCaseIds.includes(caseData.id)
  const [flipped, setFlipped] = useState(false)

  const tone = useMemo(() => {
    const kind = (caseData.match_type || '').toLowerCase()
    if (kind === 'exacto') return 'from-emerald-400/18 to-cyan-400/16 border-emerald-200/35'
    if (kind === 'relacionado') return 'from-sky-400/18 to-indigo-400/16 border-sky-200/30'
    return 'from-amber-300/18 to-orange-300/12 border-amber-200/30'
  }, [caseData.match_type])

  const logoHue = useMemo(() => hashToHue(caseData.empresa || caseData.titulo), [caseData.empresa, caseData.titulo])
  const logoStyle = useMemo(
    () => ({
      background: `radial-gradient(circle at 30% 30%, hsla(${logoHue}, 90%, 72%, 0.45), hsla(${(logoHue + 46) % 360}, 85%, 58%, 0.22))`,
    }),
    [logoHue],
  )

  const handleToggleSelect = () => {
    if (isSelected) unselectCase(caseData.id)
    else selectCase(caseData.id)
  }

  return (
    <div className="case-flip-wrap h-[210px]">
      <div className={`case-flip-inner ${flipped ? 'is-flipped' : ''}`}>
        <article
          className={`case-flip-face neo-glass-card border bg-gradient-to-br ${tone} p-4 relative overflow-hidden`}
          onMouseEnter={() => setFlipped(true)}
          onMouseLeave={() => setFlipped(false)}
        >
          <div className="absolute -right-6 -top-8 h-24 w-24 rounded-full blur-2xl" style={logoStyle} />
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] px-2 py-0.5 rounded-full border border-white/20 bg-white/10 text-slate-100 uppercase tracking-wider">{caseData.tipo}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full border border-white/20 bg-white/10 text-slate-100">{(caseData.match_type || 'relacionado').toUpperCase()}</span>
              </div>
              <h4 className="text-sm font-semibold text-white leading-snug line-clamp-2">{caseData.titulo}</h4>
              <p className="text-[11px] text-slate-200 mt-1 line-clamp-1">{caseData.match_reason || 'Referencia útil para la propuesta'}</p>
            </div>
            <div className="h-9 w-9 rounded-xl border border-white/20 flex items-center justify-center text-[11px] font-semibold text-white bg-white/10" style={logoStyle}>
              {initials(caseData.empresa || '')}
            </div>
          </div>

          <div className="mt-3 space-y-2">
            <p className="text-[11px] text-slate-100 line-clamp-2">{caseData.problema}</p>
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] text-slate-200">Score {Math.round((caseData.score_client_fit ?? caseData.score ?? 0) * 100)}%</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  setFlipped(true)
                }}
                className="text-[11px] text-slate-100 underline underline-offset-2"
              >
                Ver más
              </button>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={handleToggleSelect}
              className={`neo-pill inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold border ${
                isSelected ? 'text-emerald-100 border-emerald-200/50 bg-emerald-300/20' : 'text-slate-100 border-white/20 bg-white/10'
              }`}
            >
              {isSelected ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Circle className="w-3.5 h-3.5" />}
              {isSelected ? 'Seleccionado' : 'Seleccionar'}
            </button>
            <button
              type="button"
              onClick={() => setFlipped((v) => !v)}
              className="neo-pill inline-flex items-center gap-1 px-3 py-1.5 text-[11px] text-slate-100 border border-white/20 bg-white/10"
            >
              <Sparkles className="w-3.5 h-3.5" /> Flash
            </button>
          </div>
        </article>

        <article
          className={`case-flip-face case-back neo-glass-card border bg-gradient-to-br ${tone} p-4 relative overflow-hidden`}
          onMouseLeave={() => setFlipped(false)}
        >
          <div className="absolute -left-6 -bottom-8 h-24 w-24 rounded-full blur-2xl" style={logoStyle} />
          <h4 className="text-sm font-semibold text-white line-clamp-2">{caseData.titulo}</h4>
          <div className="mt-2 space-y-1.5 text-[11px] text-slate-100">
            <p className="line-clamp-2"><span className="text-slate-300">Solución:</span> {caseData.solucion}</p>
            <p className="line-clamp-1"><span className="text-slate-300">Impacto:</span> {caseData.kpi_impacto || 'Impacto estimado por caso relacionado'}</p>
            <p className="line-clamp-1"><span className="text-slate-300">Stack:</span> {(caseData.tecnologias || []).slice(0, 3).join(' · ') || 'N/A'}</p>
          </div>

          <div className="mt-3 flex items-center justify-between gap-2">
            {caseData.url_slide ? (
              <a
                href={caseData.url_slide}
                target="_blank"
                rel="noopener noreferrer"
                className="neo-pill inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold text-white border border-white/25 bg-white/12"
              >
                Evidencia <ExternalLink className="w-3.5 h-3.5" />
              </a>
            ) : (
              <span className="text-[11px] text-amber-200">Sin URL</span>
            )}
            <button
              type="button"
              onClick={() => setFlipped(false)}
              className="neo-pill px-3 py-1.5 text-[11px] border border-white/20 bg-white/10 text-slate-100"
            >
              Volver
            </button>
          </div>
        </article>
      </div>
    </div>
  )
}
