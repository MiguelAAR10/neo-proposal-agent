'use client'

import { User, Plus, AlertTriangle, Target, FileText, Lightbulb, CheckSquare, Square } from 'lucide-react'
import { useAppStore, type Insight, type InsightType } from '@/stores/appStore'

const INSIGHT_TYPE_CONFIG: Record<InsightType, { label: string; color: string; icon: typeof AlertTriangle }> = {
  pain_point: { label: 'Pain Point', color: '#ef4444', icon: AlertTriangle },
  objetivo: { label: 'Objetivo', color: '#4f8cff', icon: Target },
  contexto: { label: 'Contexto', color: '#8b5cf6', icon: FileText },
  decision: { label: 'Decision', color: '#c084fc', icon: Lightbulb },
}

interface ClientProfileInlineProps {
  onNavigateToInsights: () => void
}

export function ClientProfileInline({ onNavigateToInsights }: ClientProfileInlineProps) {
  const { clientProfile, selectedClient, proposalContext, toggleInsightContext } = useAppStore()

  const profileInsights = clientProfile?.insights ?? []

  const groupedInsights = profileInsights.reduce<Record<InsightType, Insight[]>>((acc, insight) => {
    const type = insight.type ?? 'contexto'
    if (!acc[type]) acc[type] = []
    acc[type].push(insight)
    return acc
  }, {} as Record<InsightType, Insight[]>)

  return (
    <div className="neo-profile-inline">
      <div className="neo-profile-inline__header">
        <User size={14} />
        <h3 className="neo-profile-inline__title">Perfil del Cliente</h3>
        <button
          type="button"
          className="neo-ghost-mini"
          onClick={onNavigateToInsights}
        >
          <Plus size={12} /> Agregar Insight
        </button>
      </div>
      <div className="neo-profile-inline__body">
        {selectedClient ? (
          <>
            {(Object.entries(groupedInsights) as [InsightType, Insight[]][]).map(([type, items]) => {
              const config = INSIGHT_TYPE_CONFIG[type]
              if (!config || items.length === 0) return null
              const Icon = config.icon
              return (
                <div key={type} className="neo-profile-insight-group">
                  <div className="neo-profile-insight-group__header">
                    <Icon size={12} style={{ color: config.color }} />
                    <span style={{ color: config.color, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      {config.label} ({items.length})
                    </span>
                  </div>
                  {items.slice(0, 3).map((ins, i) => {
                    const insightId = ins.id ?? `${type}-${i}`
                    const isSelected = proposalContext.insightIds.includes(insightId)
                    return (
                      <div
                        key={i}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 6,
                          padding: '4px 0',
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => toggleInsightContext(insightId)}
                          title={isSelected ? 'Quitar del contexto' : 'Incluir en propuesta'}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: 0,
                            border: 'none',
                            background: 'transparent',
                            color: isSelected ? '#7ba3f0' : 'var(--text-muted)',
                            cursor: 'pointer',
                            opacity: isSelected ? 1 : 0.5,
                            flexShrink: 0,
                            marginTop: 1,
                          }}
                        >
                          {isSelected ? <CheckSquare size={12} /> : <Square size={12} />}
                        </button>
                        <p
                          className="neo-profile-insight-text"
                          style={{
                            margin: 0,
                            opacity: isSelected ? 1 : 0.7,
                          }}
                        >
                          {ins.description}
                        </p>
                      </div>
                    )
                  })}
                </div>
              )
            })}
            {profileInsights.length === 0 && (
              <p className="neo-profile-inline__empty">
                Sin insights. Haz click en &quot;Agregar Insight&quot; para empezar.
              </p>
            )}
            {proposalContext.insightIds.length > 0 && (
              <p style={{
                margin: '8px 0 0 0',
                padding: '6px 8px',
                background: 'rgba(123,163,240,0.10)',
                borderRadius: 6,
                fontSize: 11,
                color: '#7ba3f0',
                fontFamily: 'var(--font-mono)',
                textAlign: 'center',
              }}>
                {proposalContext.insightIds.length} insight{proposalContext.insightIds.length !== 1 ? 's' : ''} para propuesta
              </p>
            )}
          </>
        ) : (
          <p className="neo-profile-inline__empty">
            Selecciona un cliente para ver su perfil.
          </p>
        )}
      </div>
    </div>
  )
}
