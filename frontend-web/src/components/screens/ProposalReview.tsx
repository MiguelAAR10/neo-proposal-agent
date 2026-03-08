'use client'

import { Check, X, ArrowRight, AlertTriangle, Lightbulb, Layers, BarChart3, Calendar, Target, Sparkles } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'

interface ProposalReviewProps {
  onAccept: () => void
  onReject: () => void
}

interface ParsedSection {
  key: string
  title: string
  icon: React.ElementType
  color: string
  bullets: string[]
  tags?: string[]
}

// Parser robusto para extraer secciones del markdown
function parseProposal(text: string): ParsedSection[] {
  const sectionConfig = [
    { key: 'diagnostico', pattern: /###?\s*🔍\s*DIAGNÓSTICO/i, title: 'Diagnóstico', icon: AlertTriangle, color: '#ef4444' },
    { key: 'solucion', pattern: /###?\s*💡\s*SOLUCIÓN/i, title: 'Solución', icon: Lightbulb, color: '#4f8cff' },
    { key: 'arquitectura', pattern: /###?\s*🏗️\s*ARQUITECTURA/i, title: 'Stack', icon: Layers, color: '#8b5cf6' },
    { key: 'impacto', pattern: /###?\s*📊\s*IMPACTO/i, title: 'KPIs', icon: BarChart3, color: '#10b981' },
    { key: 'roadmap', pattern: /###?\s*🗓️\s*ROADMAP/i, title: 'Roadmap', icon: Calendar, color: '#f59e0b' },
    { key: 'siguiente', pattern: /###?\s*🎯\s*SIGUIENTE/i, title: 'Next', icon: Target, color: '#ec4899' },
  ]

  const sections: ParsedSection[] = []

  for (let i = 0; i < sectionConfig.length; i++) {
    const cfg = sectionConfig[i]
    const next = sectionConfig[i + 1]

    const match = text.match(cfg.pattern)
    if (!match) continue

    const start = match.index! + match[0].length
    let end = text.length

    if (next) {
      const nextMatch = text.slice(start).match(next.pattern)
      if (nextMatch) end = start + nextMatch.index!
    } else {
      const endMatch = text.slice(start).match(/^---/m)
      if (endMatch) end = start + endMatch.index!
    }

    const content = text.slice(start, end).trim()

    // Extraer bullets y tags
    const lines = content.split('\n').map(l => l.trim()).filter(Boolean)
    const bullets: string[] = []
    const tags: string[] = []

    for (const line of lines) {
      // Skip headers
      if (/^#{1,4}\s/.test(line)) continue

      // Extraer tags [Tecnología]
      const tagMatches = line.match(/\[([^\]]+)\]/g)
      if (tagMatches) {
        tags.push(...tagMatches.map(t => t.slice(1, -1)))
      }

      // Limpiar el bullet
      if (/^[-*•]\s/.test(line)) {
        let cleanLine = line.replace(/^[-*•]\s/, '')
        // Remover tags del texto
        cleanLine = cleanLine.replace(/\[([^\]]+)\]/g, '').trim()
        // Limpiar markdown bold
        cleanLine = cleanLine.replace(/\*\*([^*]+)\*\*/g, '$1')
        if (cleanLine) bullets.push(cleanLine)
      }
    }

    if (bullets.length > 0 || tags.length > 0) {
      sections.push({
        key: cfg.key,
        title: cfg.title,
        icon: cfg.icon,
        color: cfg.color,
        bullets: bullets.slice(0, 4), // Máximo 4 bullets por sección
        tags: [...new Set(tags)].slice(0, 6), // Únicos, máximo 6
      })
    }
  }

  return sections
}

export function ProposalReview({ onAccept, onReject }: ProposalReviewProps) {
  const { proposalRawText, selectedClient, selectedArea, selectedCaseIds, cases } = useAppStore()

  const proposalText = proposalRawText ?? ''
  const sections = parseProposal(proposalText)
  const hasSections = sections.length >= 2

  // Obtener tecnologías del caso seleccionado si no hay tags en arquitectura
  const selectedCase = cases.find(c => selectedCaseIds.includes(c.id))
  const stackSection = sections.find(s => s.key === 'arquitectura')
  const techTags = stackSection?.tags?.length ? stackSection.tags : (selectedCase?.tecnologias?.slice(0, 5) ?? [])

  return (
    <div className="neo-proposal-review" style={{ padding: 24 }}>
      {/* Header ejecutivo */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 20,
        paddingBottom: 16,
        borderBottom: '1px solid rgba(123,163,240,0.15)',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <Sparkles size={20} style={{ color: '#4f8cff' }} />
            <h2 style={{
              fontSize: 18,
              fontWeight: 700,
              color: '#f5f5ff',
              fontFamily: 'var(--font-serif)',
              margin: 0,
            }}>
              Propuesta de Valor
            </h2>
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>
            {selectedClient?.display_name ?? 'Cliente'} · {selectedArea ?? 'General'}
          </p>
        </div>

        {/* Tech Tags compactos */}
        {techTags.length > 0 && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end', maxWidth: 280 }}>
            {techTags.map(tag => (
              <span
                key={tag}
                style={{
                  fontSize: 10,
                  padding: '3px 8px',
                  background: 'rgba(139,92,246,0.15)',
                  border: '1px solid rgba(139,92,246,0.25)',
                  borderRadius: 4,
                  color: '#a78bfa',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Contenido principal - Grid compacto */}
      {hasSections ? (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 14,
          marginBottom: 20,
        }}>
          {sections.map((section) => {
            const Icon = section.icon
            return (
              <div
                key={section.key}
                style={{
                  background: 'rgba(5,5,140,0.20)',
                  borderRadius: 10,
                  border: '1px solid rgba(123,163,240,0.12)',
                  padding: '12px 14px',
                }}
              >
                {/* Section header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                  <div style={{
                    width: 24,
                    height: 24,
                    borderRadius: 5,
                    background: `${section.color}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <Icon size={12} style={{ color: section.color }} />
                  </div>
                  <h3 style={{
                    fontSize: 11,
                    fontWeight: 700,
                    color: section.color,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    margin: 0,
                  }}>
                    {section.title}
                  </h3>
                </div>

                {/* Bullets */}
                <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12, lineHeight: 1.6, color: 'var(--text-main)' }}>
                  {section.bullets.map((bullet, idx) => (
                    <li key={idx} style={{ marginBottom: 4 }}>{bullet}</li>
                  ))}
                </ul>
              </div>
            )
          })}
        </div>
      ) : (
        /* Fallback minimalista */
        <div style={{
          background: 'rgba(5,5,140,0.15)',
          borderRadius: 10,
          padding: 16,
          marginBottom: 20,
          fontSize: 13,
          lineHeight: 1.7,
          color: 'var(--text-main)',
          whiteSpace: 'pre-wrap',
        }}>
          {proposalText.slice(0, 800)}...
        </div>
      )}

      {/* Footer con acciones */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingTop: 16,
        borderTop: '1px solid rgba(123,163,240,0.10)',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '6px 12px',
          background: 'rgba(79,140,255,0.08)',
          borderRadius: 6,
        }}>
          <ArrowRight size={14} style={{ color: '#4f8cff' }} />
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Siguiente: Asignar equipo
          </span>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            type="button"
            onClick={onReject}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 16px',
              background: 'rgba(239,68,68,0.10)',
              border: '1px solid rgba(239,68,68,0.25)',
              borderRadius: 8,
              color: '#ef4444',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            <X size={14} />
            Refinar
          </button>
          <button
            type="button"
            onClick={onAccept}
            className="neo-pill neo-pill--primary"
            style={{ padding: '8px 20px' }}
          >
            <Check size={14} />
            Continuar
          </button>
        </div>
      </div>
    </div>
  )
}
