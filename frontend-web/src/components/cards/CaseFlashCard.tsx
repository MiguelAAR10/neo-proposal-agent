'use client'

import { useMemo, useState } from 'react'
import { ExternalLink, CheckCircle2, Circle, CornerDownRight, CornerDownLeft } from 'lucide-react'
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

function compactText(value: string | undefined, fallback: string, max = 88): string {
  const text = (value || '').trim()
  if (!text) return fallback
  if (text.length <= max) return text
  return `${text.slice(0, max - 1)}…`
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

  const scorePct = Math.round((caseData.score_client_fit ?? caseData.score ?? 0) * 100)
  const topTech = (caseData.tecnologias || []).slice(0, 2)

  const handleToggleSelect = () => {
    if (isSelected) unselectCase(caseData.id)
    else selectCase(caseData.id)
  }

  return (
    <div className="case-flip-wrap h-[292px] md:h-[304px]">
      <div className={`case-flip-inner ${flipped ? 'is-flipped' : ''}`}>
        <article className={`case-flip-face case-aurora case-card-lift neo-glass-card border bg-gradient-to-br ${tone} p-4 relative overflow-hidden`}>
          <div className="absolute -right-6 -top-8 h-24 w-24 rounded-full blur-2xl" style={logoStyle} />

          <header className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                <span className="text-[11px] px-2 py-0.5 rounded-full border border-white/20 bg-white/10 text-slate-100 uppercase tracking-wider">{caseData.tipo}</span>
                <span className="text-[11px] px-2 py-0.5 rounded-full border border-white/20 bg-white/10 text-slate-100">{(caseData.match_type || 'relacionado').toUpperCase()}</span>
                <span className="text-[11px] px-2 py-0.5 rounded-full border border-white/20 bg-white/10 text-slate-100">{scorePct}%</span>
              </div>
              <h4 className="text-sm font-semibold text-white leading-snug line-clamp-2">{caseData.titulo}</h4>
            </div>
            <div className="h-9 w-9 rounded-xl border border-white/20 flex items-center justify-center text-[11px] font-semibold text-white bg-white/10" style={logoStyle}>
              {initials(caseData.empresa || '')}
            </div>
          </header>

          <div className="mt-3 grid grid-cols-1 gap-2">
            <section className="rounded-2xl border border-white/15 bg-white/8 p-3 min-h-[122px]">
              <p className="text-[11px] uppercase tracking-wide text-slate-300 mb-1">Valor clave</p>
              <p className="text-[11px] text-slate-100 leading-4 select-text">{compactText(caseData.problema, 'Problema no disponible')}</p>
              <p className="text-[11px] text-slate-300 mt-1.5 leading-4 select-text">{compactText(caseData.solucion, 'Solución no disponible')}</p>
              <p className="text-[11px] text-slate-300 mt-2 select-text">
                <span className="text-slate-200">Impacto:</span> {compactText(caseData.kpi_impacto, 'Pendiente de cuantificación', 72)}
              </p>
            </section>
          </div>

          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="text-[11px] px-2 py-0.5 rounded-full border border-white/20 bg-white/8 text-slate-200">{caseData.area || 'General'}</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full border border-white/20 bg-white/8 text-slate-200">{caseData.industria || 'Multisector'}</span>
            {topTech.length > 0 ? (
              topTech.map((tech) => (
                <span key={`${caseData.id}-${tech}`} className="text-[11px] px-2 py-0.5 rounded-full border border-white/20 bg-white/8 text-slate-200">
                  {tech}
                </span>
              ))
            ) : (
              <span className="text-[11px] px-2 py-0.5 rounded-full border border-white/20 bg-white/8 text-slate-300">
                Tecnología por definir
              </span>
            )}
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
            {caseData.url_slide ? (
              <a
                href={caseData.url_slide}
                target="_blank"
                rel="noopener noreferrer"
                className="neo-pill inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold text-white border border-white/25 bg-white/12 hover:bg-white/18 w-fit"
              >
                Ver diapositivas <ExternalLink className="w-3.5 h-3.5" />
              </a>
            ) : (
              <span className="text-[11px] text-amber-200">Sin diapositivas</span>
            )}
          </div>

          <button
            type="button"
            onClick={() => setFlipped(true)}
            className="corner-peel-btn"
            aria-label="Ver detalle completo"
            title="Ver detalle completo"
          >
            <CornerDownRight className="w-3.5 h-3.5" />
          </button>
        </article>

        <article className={`case-flip-face case-back case-aurora case-card-lift neo-glass-card border bg-gradient-to-br ${tone} p-4 relative overflow-hidden`}>
          <div className="absolute -left-6 -bottom-8 h-24 w-24 rounded-full blur-2xl" style={logoStyle} />

          <h4 className="text-sm font-semibold text-white line-clamp-2">{caseData.titulo}</h4>
          <div className="mt-2 rounded-2xl border border-white/15 bg-white/8 p-3 space-y-1.5 text-[11px] text-slate-100 max-h-[175px] overflow-y-auto">
            <p className="select-text"><span className="text-slate-300">Caso para:</span> {caseData.empresa || 'Cliente no mapeado'}</p>
            <p className="select-text"><span className="text-slate-300">Impacto esperado:</span> {caseData.kpi_impacto || 'Pendiente de cuantificación'}</p>
            <p className="select-text"><span className="text-slate-300">Por qué aplica:</span> {caseData.match_reason || 'Similitud con el problema objetivo'}</p>
            <p className="select-text"><span className="text-slate-300">Tecnologías:</span> {(caseData.tecnologias || []).slice(0, 5).join(' · ') || 'N/A'}</p>
            <p className="select-text"><span className="text-slate-300">Contexto:</span> {caseData.industria || 'N/A'} · {caseData.area || 'N/A'}</p>
          </div>

          <div className="mt-3 flex items-center justify-between gap-2">
            {caseData.url_slide ? (
              <a
                href={caseData.url_slide}
                target="_blank"
                rel="noopener noreferrer"
                className="neo-pill inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold text-white border border-white/25 bg-white/12 hover:bg-white/18"
              >
                Abrir evidencia <ExternalLink className="w-3.5 h-3.5" />
              </a>
            ) : (
              <span className="text-[11px] text-amber-200">Sin URL verificable</span>
            )}
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
          </div>

          <button
            type="button"
            onClick={() => setFlipped(false)}
            className="corner-peel-btn"
            aria-label="Regresar al frente"
            title="Regresar al frente"
          >
            <CornerDownLeft className="w-3.5 h-3.5" />
          </button>
        </article>
      </div>
    </div>
  )
}
