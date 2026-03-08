'use client'

import { useState } from 'react'
import Image from 'next/image'
import { ArrowLeft, Clock, Save } from 'lucide-react'
import { useAppStore, type InsightType } from '@/stores/appStore'
import { useSaveInsight } from '@/hooks/useApi'

function slugifyCompany(value: string): string {
  return value.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, '-')
}

const INSIGHT_TYPES: { value: InsightType; label: string; color: string }[] = [
  { value: 'pain_point', label: 'Pain Point', color: '#ef4444' },
  { value: 'objetivo', label: 'Objetivo', color: '#4f8cff' },
  { value: 'contexto', label: 'Contexto', color: '#8b5cf6' },
  { value: 'decision', label: 'Decision', color: '#c084fc' },
]

const AREA_TABS = ['Operaciones', 'Marketing', 'Corporativo']

interface ProfileInsightsProps {
  onBack: () => void
}

export function ProfileInsights({ onBack }: ProfileInsightsProps) {
  const {
    selectedClient, activeProfileArea, setActiveProfileArea, insights, clientProfile,
  } = useAppStore()

  const saveMutation = useSaveInsight()

  const [formType, setFormType] = useState<InsightType>('pain_point')
  const [formDescription, setFormDescription] = useState('')
  const [formSource, setFormSource] = useState('')

  const now = new Date()
  const autoDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} . ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`

  const handleSave = () => {
    if (!selectedClient || formDescription.trim().length < 10) return
    saveMutation.mutate({
      companyId: selectedClient.name,
      author: 'Consultor',
      text: formDescription,
      source: formSource || 'manual',
    })
    setFormDescription('')
    setFormSource('')
  }

  const filteredInsights = insights.filter((i) => i.area === activeProfileArea)
  const profileInsights = clientProfile?.insights?.filter((i) => i.area === activeProfileArea) ?? []
  const allInsights = [...filteredInsights, ...profileInsights]

  return (
    <div className="neo-profile-page">
      {/* Top bar */}
      <div className="neo-profile-page__topbar">
        <button type="button" onClick={onBack} className="neo-ghost-mini">
          <ArrowLeft size={14} /> Volver al Workspace
        </button>
        <h2 className="neo-profile-page__title">Perfil de Cliente</h2>
      </div>

      {/* Hero section */}
      <div className="neo-profile-hero">
        <div className="neo-profile-hero__avatar">
          {selectedClient && (
            <Image
              src={`/logos/companies/${slugifyCompany(selectedClient.name)}.png`}
              alt={selectedClient.display_name}
              width={56}
              height={56}
              unoptimized
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          )}
        </div>
        <div>
          <h3 className="neo-profile-hero__name">{selectedClient?.display_name ?? 'Sin cliente'}</h3>
          <p className="neo-profile-hero__sector">{selectedClient?.vertical ?? ''}</p>
        </div>

        {/* Area tabs */}
        <div className="neo-area-tabs">
          {AREA_TABS.map((area) => (
            <button
              key={area}
              type="button"
              className={`neo-area-tab${activeProfileArea === area ? ' neo-area-tab--active' : ''}`}
              onClick={() => setActiveProfileArea(area)}
            >
              {area}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="neo-profile-content">
        {/* Left: Insight Form */}
        <div className="neo-insight-form-panel">
          <h4 className="neo-insight-form-panel__title">Nuevo Insight</h4>

          {/* Auto date */}
          <div className="neo-insight-form__date">
            <Clock size={12} />
            <span>{autoDate}</span>
            <span className="neo-insight-form__auto-badge">Auto</span>
          </div>

          {/* Type chips */}
          <div className="neo-insight-type-chips">
            {INSIGHT_TYPES.map((t) => (
              <button
                key={t.value}
                type="button"
                className={`neo-insight-type-chip${formType === t.value ? ' neo-insight-type-chip--active' : ''}`}
                style={{
                  '--chip-color': t.color,
                } as React.CSSProperties}
                onClick={() => setFormType(t.value)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Description */}
          <textarea
            className="neo-form-input neo-form-textarea"
            rows={5}
            value={formDescription}
            onChange={(e) => setFormDescription(e.target.value)}
            placeholder="Describe el insight (min. 10 caracteres)..."
          />

          {/* Source */}
          <input
            className="neo-form-input"
            value={formSource}
            onChange={(e) => setFormSource(e.target.value)}
            placeholder="Fuente (reunion, llamada, documento...)"
          />

          {/* Actions */}
          <div className="neo-insight-form__actions">
            <button type="button" className="neo-ghost-mini" onClick={() => { setFormDescription(''); setFormSource('') }}>
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saveMutation.isPending || formDescription.trim().length < 10}
              className="neo-pill neo-pill--primary"
            >
              <Save size={14} />
              {saveMutation.isPending ? 'Guardando...' : 'Guardar Insight'}
            </button>
          </div>
        </div>

        {/* Right: Insight History */}
        <div className="neo-insight-history-panel">
          <h4 className="neo-insight-history-panel__title">
            Historial de Insights — {activeProfileArea}
            <span className="neo-insight-history-panel__count">{allInsights.length}</span>
          </h4>

          <div className="neo-insight-history-list">
            {allInsights.length > 0 ? (
              allInsights.map((insight, i) => {
                const typeConfig = INSIGHT_TYPES.find((t) => t.value === insight.type)
                return (
                  <div key={insight.id ?? i} className="neo-insight-history-item">
                    <div className="neo-insight-history-item__header">
                      <span
                        className="neo-insight-type-badge"
                        style={{ '--badge-color': typeConfig?.color ?? '#8b5cf6' } as React.CSSProperties}
                      >
                        {typeConfig?.label ?? insight.type}
                      </span>
                      <span className="neo-insight-history-item__time">
                        {insight.timestamp}
                      </span>
                    </div>
                    <p className="neo-insight-history-item__text">{insight.description}</p>
                    {insight.source && (
                      <span className="neo-insight-history-item__source">
                        Fuente: {insight.source}
                      </span>
                    )}
                  </div>
                )
              })
            ) : (
              <p style={{ fontSize: 13, color: 'var(--text-muted)', padding: 16 }}>
                Sin insights para {activeProfileArea}. Crea el primero.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
