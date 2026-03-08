'use client'

import { X, Check, AlertTriangle, Cpu, BarChart3, CheckCircle2, Target, Zap, TrendingUp, ArrowRight } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'

interface ProposalReviewProps {
  onAccept: () => void
  onReject: () => void
}

function renderMarkdownSimple(text: string): React.ReactNode[] {
  return text.split(/\n{2,}/).map((block, i) => {
    const t = block.trim()
    if (!t) return null
    if (/^#{1,4} /.test(t)) {
      return (
        <p key={i} style={{ fontFamily: 'var(--font-serif)', color: 'var(--accent)', fontSize: 16, fontWeight: 700, margin: '12px 0 6px' }}>
          {t.replace(/^#{1,4} /, '')}
        </p>
      )
    }
    const lines = t.split('\n')
    if (lines.every((l) => /^[-*] /.test(l.trim()))) {
      return (
        <ul key={i} style={{ fontSize: 14, color: 'var(--text-main)', paddingLeft: 18, marginBottom: 10, listStyle: 'disc' }}>
          {lines.map((l, j) => <li key={j}>{l.replace(/^[-*] /, '').trim()}</li>)}
        </ul>
      )
    }
    return <p key={i} style={{ fontSize: 14, color: 'var(--text-main)', lineHeight: 1.7, marginBottom: 10 }}>{t}</p>
  }).filter(Boolean)
}

export function ProposalReview({ onAccept, onReject }: ProposalReviewProps) {
  const { proposalRawText, selectedClient, selectedArea, cases, selectedCaseIds, proposalContext } = useAppStore()

  const selectedCase = cases.find((c) => selectedCaseIds.includes(c.id)) ?? cases[0]
  const proposalText = proposalRawText ?? ''

  // Split proposal into sections (heuristic: use headers or divide into thirds)
  const sections = proposalText.split(/(?=^## )/m).filter(Boolean)
  const problemSection = sections[0] ?? proposalText.slice(0, Math.floor(proposalText.length / 3))
  const solutionSection = sections[1] ?? proposalText.slice(Math.floor(proposalText.length / 3), Math.floor(2 * proposalText.length / 3))
  const techSection = sections[2] ?? proposalText.slice(Math.floor(2 * proposalText.length / 3))

  // Puntos de valor identificados
  const valuePoints = [
    { icon: AlertTriangle, label: 'Problema identificado', present: problemSection.length > 50, color: '#ef4444' },
    { icon: Cpu, label: 'Solucion propuesta', present: solutionSection.length > 50, color: '#4f8cff' },
    { icon: BarChart3, label: 'Stack tecnologico', present: techSection.length > 30, color: '#8b5cf6' },
    { icon: TrendingUp, label: 'KPIs de impacto', present: !!selectedCase?.kpi_impacto, color: '#10b981' },
    { icon: Target, label: 'Casos de exito', present: selectedCaseIds.length > 0, color: '#f59e0b' },
    { icon: Zap, label: 'Contexto del cliente', present: proposalContext.chatMessageIndices.length > 0 || proposalContext.insightIds.length > 0, color: '#ec4899' },
  ]

  return (
    <div className="neo-proposal-review">
      <div className="neo-proposal-review__header">
        <h2 className="neo-proposal-review__title">Propuesta Generada</h2>
        <p className="neo-proposal-review__subtitle">
          {selectedClient?.display_name ?? ''} · {selectedArea ?? ''} · {selectedCase?.titulo ?? ''}
        </p>
      </div>

      {/* Ficha de Puntos de Valor */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 8,
        padding: '12px 16px',
        background: 'rgba(5,5,140,0.25)',
        borderRadius: 10,
        border: '1px solid rgba(123,163,240,0.20)',
        marginBottom: 16,
      }}>
        <div style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 4,
        }}>
          <CheckCircle2 size={16} style={{ color: '#10b981' }} />
          <span style={{
            fontSize: 12,
            fontWeight: 700,
            color: '#7ba3f0',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            fontFamily: 'var(--font-mono)',
          }}>
            Puntos de Valor Identificados
          </span>
        </div>
        {valuePoints.map((point) => {
          const Icon = point.icon
          return (
            <div
              key={point.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 10px',
                background: point.present ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.05)',
                borderRadius: 6,
                border: `1px solid ${point.present ? 'rgba(16,185,129,0.30)' : 'rgba(255,255,255,0.10)'}`,
              }}
            >
              <Icon size={12} style={{ color: point.present ? point.color : 'var(--text-muted)' }} />
              <span style={{
                fontSize: 11,
                color: point.present ? '#f5f5ff' : 'var(--text-muted)',
                fontFamily: 'var(--font-body)',
              }}>
                {point.label}
              </span>
              {point.present && (
                <CheckCircle2 size={10} style={{ color: '#10b981', marginLeft: 2 }} />
              )}
            </div>
          )
        })}
      </div>

      {/* 3 Proposal Cards */}
      <div className="neo-proposal-cards">
        {/* Problem Card */}
        <div className="neo-proposal-card neo-proposal-card--problem">
          <div className="neo-proposal-card__icon">
            <AlertTriangle size={20} />
          </div>
          <h3 className="neo-proposal-card__title">Problema Identificado</h3>
          <div className="neo-proposal-card__content">
            {renderMarkdownSimple(problemSection)}
          </div>
          {selectedCase?.kpi_impacto && (
            <div className="neo-proposal-card__tags">
              <span className="neo-metric-tag">{selectedCase.kpi_impacto}</span>
            </div>
          )}
        </div>

        {/* Solution Card */}
        <div className="neo-proposal-card neo-proposal-card--solution">
          <div className="neo-proposal-card__icon" style={{ color: '#4f8cff' }}>
            <Cpu size={20} />
          </div>
          <h3 className="neo-proposal-card__title">Solucion Propuesta</h3>
          <div className="neo-proposal-card__content">
            {renderMarkdownSimple(solutionSection)}
          </div>
          {selectedCase?.tecnologias && selectedCase.tecnologias.length > 0 && (
            <div className="neo-proposal-card__tags">
              {selectedCase.tecnologias.slice(0, 4).map((tech) => (
                <span key={tech} className="neo-tech-tag">{tech}</span>
              ))}
            </div>
          )}
        </div>

        {/* Tech Stack Card */}
        <div className="neo-proposal-card neo-proposal-card--tech">
          <div className="neo-proposal-card__icon" style={{ color: '#8b5cf6' }}>
            <BarChart3 size={20} />
          </div>
          <h3 className="neo-proposal-card__title">Stack Tecnologico</h3>
          <div className="neo-proposal-card__content">
            {renderMarkdownSimple(techSection)}
          </div>
        </div>
      </div>

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
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-body)' }}>
            Proximo: Asignar equipo de implementacion
          </span>
        </div>
        <button type="button" onClick={onReject} className="neo-proposal-reject-btn">
          <X size={16} />
          Rechazar y Refinar
        </button>
        <button type="button" onClick={onAccept} className="neo-pill neo-pill--primary">
          <Check size={16} />
          Aceptar Propuesta
        </button>
      </div>
    </div>
  )
}
