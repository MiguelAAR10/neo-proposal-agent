'use client'

import { X, Check, AlertTriangle, Lightbulb, Layers, BarChart3, Calendar, Target, CheckCircle2, ArrowRight } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'

interface ProposalReviewProps {
  onAccept: () => void
  onReject: () => void
}

interface ProposalSection {
  key: string
  emoji: string
  title: string
  icon: React.ElementType
  color: string
  content: string
}

// Parser para extraer secciones del markdown generado
function parseProposalSections(text: string): ProposalSection[] {
  const sectionDefs = [
    { key: 'diagnostico', emoji: '🔍', title: 'Diagnóstico', icon: AlertTriangle, color: '#ef4444', pattern: /###?\s*🔍\s*DIAGNÓSTICO/i },
    { key: 'solucion', emoji: '💡', title: 'Solución Propuesta', icon: Lightbulb, color: '#4f8cff', pattern: /###?\s*💡\s*SOLUCIÓN/i },
    { key: 'arquitectura', emoji: '🏗️', title: 'Arquitectura & Stack', icon: Layers, color: '#8b5cf6', pattern: /###?\s*🏗️\s*ARQUITECTURA/i },
    { key: 'impacto', emoji: '📊', title: 'Impacto & KPIs', icon: BarChart3, color: '#10b981', pattern: /###?\s*📊\s*IMPACTO/i },
    { key: 'roadmap', emoji: '🗓️', title: 'Roadmap', icon: Calendar, color: '#f59e0b', pattern: /###?\s*🗓️\s*ROADMAP/i },
    { key: 'siguiente', emoji: '🎯', title: 'Siguiente Paso', icon: Target, color: '#ec4899', pattern: /###?\s*🎯\s*SIGUIENTE/i },
  ]

  const sections: ProposalSection[] = []

  for (let i = 0; i < sectionDefs.length; i++) {
    const def = sectionDefs[i]
    const nextDef = sectionDefs[i + 1]

    const startMatch = text.match(def.pattern)
    if (!startMatch) continue

    const startIdx = startMatch.index! + startMatch[0].length
    let endIdx = text.length

    if (nextDef) {
      const nextMatch = text.slice(startIdx).match(nextDef.pattern)
      if (nextMatch) {
        endIdx = startIdx + nextMatch.index!
      }
    } else {
      // Para la última sección, buscar fin del contenido
      const endMatch = text.slice(startIdx).match(/^---/m)
      if (endMatch) {
        endIdx = startIdx + endMatch.index!
      }
    }

    const content = text.slice(startIdx, endIdx).trim()
    if (content) {
      sections.push({
        key: def.key,
        emoji: def.emoji,
        title: def.title,
        icon: def.icon,
        color: def.color,
        content,
      })
    }
  }

  return sections
}

// Extraer tags tecnológicos del contenido [Tag]
function extractTechTags(content: string): string[] {
  const matches = content.match(/\[([^\]]+)\]/g)
  if (!matches) return []
  return [...new Set(matches.map(m => m.slice(1, -1)))]
}

// Renderizar markdown simple a React nodes
function renderContent(content: string): React.ReactNode[] {
  // Remover tags [Tecnología] del contenido principal (se muestran aparte)
  const cleanContent = content.replace(/\[([^\]]+)\]/g, '')

  return cleanContent.split(/\n/).map((line, i) => {
    const trimmed = line.trim()
    if (!trimmed) return null

    // Headers
    if (/^#{1,4}\s/.test(trimmed)) {
      return null // Ya tenemos el header en la card
    }

    // Bullets
    if (/^[-*•]\s/.test(trimmed)) {
      const text = trimmed.replace(/^[-*•]\s/, '')
      // Resaltar negritas
      const parts = text.split(/\*\*([^*]+)\*\*/)
      return (
        <li key={i} style={{ fontSize: 13, lineHeight: 1.6, marginBottom: 4 }}>
          {parts.map((part, j) =>
            j % 2 === 1 ? <strong key={j} style={{ color: '#f5f5ff' }}>{part}</strong> : part
          )}
        </li>
      )
    }

    // Texto normal con negritas
    const parts = trimmed.split(/\*\*([^*]+)\*\*/)
    return (
      <p key={i} style={{ fontSize: 13, lineHeight: 1.6, marginBottom: 6, color: 'var(--text-main)' }}>
        {parts.map((part, j) =>
          j % 2 === 1 ? <strong key={j} style={{ color: '#f5f5ff' }}>{part}</strong> : part
        )}
      </p>
    )
  }).filter(Boolean)
}

export function ProposalReview({ onAccept, onReject }: ProposalReviewProps) {
  const { proposalRawText, selectedClient, selectedArea, proposalContext, selectedCaseIds } = useAppStore()

  const proposalText = proposalRawText ?? ''
  const sections = parseProposalSections(proposalText)

  // Fallback si no se parsearon secciones
  const hasSections = sections.length >= 3

  // Puntos de valor identificados
  const valuePoints = [
    { label: 'Diagnóstico', present: sections.some(s => s.key === 'diagnostico'), color: '#ef4444' },
    { label: 'Solución', present: sections.some(s => s.key === 'solucion'), color: '#4f8cff' },
    { label: 'Stack Tech', present: sections.some(s => s.key === 'arquitectura'), color: '#8b5cf6' },
    { label: 'KPIs', present: sections.some(s => s.key === 'impacto'), color: '#10b981' },
    { label: 'Roadmap', present: sections.some(s => s.key === 'roadmap'), color: '#f59e0b' },
    { label: 'Casos', present: selectedCaseIds.length > 0, color: '#ec4899' },
    { label: 'Contexto', present: proposalContext.chatMessageIndices.length > 0 || proposalContext.insightIds.length > 0, color: '#06b6d4' },
  ]

  return (
    <div className="neo-proposal-review">
      {/* Header */}
      <div className="neo-proposal-review__header">
        <h2 className="neo-proposal-review__title">Propuesta de Valor</h2>
        <p className="neo-proposal-review__subtitle">
          {selectedClient?.display_name ?? 'Cliente'} · {selectedArea ?? 'General'}
        </p>
      </div>

      {/* Ficha de Puntos de Valor - Compacta */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '8px 12px',
        background: 'rgba(5,5,140,0.20)',
        borderRadius: 8,
        border: '1px solid rgba(123,163,240,0.15)',
        marginBottom: 12,
        flexWrap: 'wrap',
      }}>
        <CheckCircle2 size={14} style={{ color: '#10b981' }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: '#7ba3f0', letterSpacing: '0.04em' }}>
          INCLUIDO:
        </span>
        {valuePoints.filter(p => p.present).map((point) => (
          <span
            key={point.label}
            style={{
              fontSize: 10,
              padding: '2px 8px',
              background: 'rgba(16,185,129,0.15)',
              borderRadius: 4,
              color: point.color,
              fontWeight: 500,
            }}
          >
            {point.label}
          </span>
        ))}
      </div>

      {/* Cards Grid - 6 secciones en 2 filas */}
      {hasSections ? (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12,
          marginBottom: 16,
        }}>
          {sections.map((section) => {
            const Icon = section.icon
            const techTags = section.key === 'arquitectura' ? extractTechTags(section.content) : []

            return (
              <div
                key={section.key}
                className="neo-proposal-card"
                style={{
                  background: 'rgba(5,5,140,0.25)',
                  borderRadius: 10,
                  border: '1px solid rgba(123,163,240,0.18)',
                  padding: 14,
                  display: 'flex',
                  flexDirection: 'column',
                  minHeight: 140,
                }}
              >
                {/* Card Header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                  <div style={{
                    width: 28,
                    height: 28,
                    borderRadius: 6,
                    background: `${section.color}20`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <Icon size={14} style={{ color: section.color }} />
                  </div>
                  <h3 style={{
                    fontSize: 12,
                    fontWeight: 700,
                    color: '#f5f5ff',
                    fontFamily: 'var(--font-serif)',
                    margin: 0,
                  }}>
                    {section.title}
                  </h3>
                </div>

                {/* Card Content */}
                <div style={{ flex: 1, overflow: 'auto' }}>
                  <ul style={{ margin: 0, paddingLeft: 14, color: 'var(--text-main)' }}>
                    {renderContent(section.content)}
                  </ul>
                </div>

                {/* Tech Tags (solo para arquitectura) */}
                {techTags.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 10 }}>
                    {techTags.slice(0, 6).map((tag) => (
                      <span
                        key={tag}
                        className="neo-tech-tag"
                        style={{
                          fontSize: 9,
                          padding: '2px 6px',
                          background: 'rgba(139,92,246,0.20)',
                          border: '1px solid rgba(139,92,246,0.30)',
                          borderRadius: 4,
                          color: '#a78bfa',
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        /* Fallback: mostrar markdown raw si no se parsearon secciones */
        <div className="neo-proposal-card" style={{ padding: 16, marginBottom: 16 }}>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.6 }}>{proposalText}</pre>
        </div>
      )}

      {/* Action buttons */}
      <div className="neo-proposal-review__actions">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          marginRight: 'auto',
          padding: '6px 12px',
          background: 'rgba(123,163,240,0.08)',
          borderRadius: 6,
        }}>
          <ArrowRight size={14} style={{ color: '#7ba3f0' }} />
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Próximo: Asignar equipo
          </span>
        </div>
        <button type="button" onClick={onReject} className="neo-proposal-reject-btn">
          <X size={16} />
          Refinar
        </button>
        <button type="button" onClick={onAccept} className="neo-pill neo-pill--primary">
          <Check size={16} />
          Aceptar
        </button>
      </div>
    </div>
  )
}
