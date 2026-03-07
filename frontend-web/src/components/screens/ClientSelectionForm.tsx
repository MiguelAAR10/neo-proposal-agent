'use client'

import { useState, useEffect, useMemo } from 'react'
import Image from 'next/image'
import { Search, Building, AlertCircle, Lightbulb, Target, FileText, ChevronDown } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'
import { usePrioritizedClients, useClientProfile, useSearchCases, AREA_OPTIONS } from '@/hooks/useApi'
import { NeoLoader } from '@/components/ui/NeoLoader'
import type { Client } from '@/stores/appStore'

function slugifyCompany(value: string): string {
  return value.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, '-')
}

interface ClientSelectionFormProps {
  onBack: () => void
}

export function ClientSelectionForm({ onBack }: ClientSelectionFormProps) {
  const {
    selectedClient, setSelectedClient,
    selectedArea, setSelectedArea,
    dataSource, setDataSource,
    problemDescription, setProblemDescription,
  } = useAppStore()

  const { data: catalog = [] } = usePrioritizedClients()
  const searchMutation = useSearchCases()
  const [isClientDropdownOpen, setIsClientDropdownOpen] = useState(false)

  const companyId = selectedClient?.name ?? null
  const { data: profileData } = useClientProfile(companyId, selectedArea ?? undefined)

  const handleSelectClient = (client: Client) => {
    setSelectedClient(client)
    setIsClientDropdownOpen(false)
  }

  const handleSearch = () => {
    if (!selectedClient || !selectedArea || problemDescription.trim().length < 10) return
    const switchMap = { historico: 'neo', ai: 'ai', ambas: 'both' } as const
    searchMutation.mutate({
      empresa: selectedClient.name,
      rubro: selectedClient.vertical,
      area: selectedArea,
      problema: problemDescription,
      switch: switchMap[dataSource],
      use_client_profile: true,
    })
  }

  const profilePayload = profileData?.profile_payload as Record<string, unknown> | undefined
  const insights = useMemo(() => {
    if (!profilePayload) return []
    const raw = profilePayload.human_insights ?? profilePayload.insights ?? []
    return Array.isArray(raw) ? raw.slice(0, 5) : []
  }, [profilePayload])

  return (
    <div className="neo-client-selection">
      {/* Left: Form */}
      <div className="neo-client-form">
        <h2 className="neo-client-form__title">Configura tu Busqueda</h2>

        {/* Client dropdown */}
        <div className="neo-form-field">
          <label className="neo-form-field__label">Cliente Priorizado</label>
          <div style={{ position: 'relative' }}>
            <button
              type="button"
              onClick={() => setIsClientDropdownOpen(!isClientDropdownOpen)}
              className="neo-form-select"
              aria-expanded={isClientDropdownOpen}
            >
              {selectedClient ? (
                <span className="neo-form-select__content">
                  <span className="neo-form-select__logo">
                    <Image
                      src={`/logos/companies/${slugifyCompany(selectedClient.name)}.png`}
                      alt={selectedClient.display_name}
                      width={24}
                      height={24}
                      className="neo-form-select__logo-img"
                      unoptimized
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                    />
                  </span>
                  {selectedClient.display_name}
                </span>
              ) : (
                <span style={{ color: 'var(--text-muted)' }}>Selecciona un cliente</span>
              )}
              <ChevronDown size={16} style={{ marginLeft: 'auto', color: 'var(--text-muted)' }} />
            </button>
            {isClientDropdownOpen && (
              <div className="neo-form-dropdown">
                {catalog.map((client) => (
                  <button
                    key={client.name}
                    type="button"
                    className={`neo-form-dropdown__item${selectedClient?.name === client.name ? ' neo-form-dropdown__item--active' : ''}`}
                    onClick={() => handleSelectClient(client)}
                  >
                    <Image
                      src={`/logos/companies/${slugifyCompany(client.name)}.png`}
                      alt={client.display_name}
                      width={24}
                      height={24}
                      className="neo-form-select__logo-img"
                      unoptimized
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                    />
                    <span>{client.display_name}</span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>{client.vertical}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Area */}
        <div className="neo-form-field">
          <label className="neo-form-field__label">Area de Impacto</label>
          <select
            className="neo-form-input"
            value={selectedArea ?? ''}
            onChange={(e) => setSelectedArea(e.target.value || null)}
          >
            <option value="">Selecciona un area</option>
            {AREA_OPTIONS.map((area) => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
        </div>

        {/* Data source */}
        <div className="neo-form-field">
          <label className="neo-form-field__label">Fuente de Datos</label>
          <div className="neo-source-chips">
            {([
              { value: 'historico', label: 'Historico NEO' },
              { value: 'ai', label: 'AI NEO' },
              { value: 'ambas', label: 'Ambas' },
            ] as const).map((opt) => (
              <button
                key={opt.value}
                type="button"
                className={`neo-source-chip${dataSource === opt.value ? ' neo-source-chip--active' : ''}`}
                onClick={() => setDataSource(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Problem */}
        <div className="neo-form-field">
          <label className="neo-form-field__label">Problema o Solucion</label>
          <textarea
            className="neo-form-input neo-form-textarea"
            rows={4}
            value={problemDescription}
            onChange={(e) => setProblemDescription(e.target.value)}
            placeholder="Describe el problema de negocio, impacto y contexto para obtener mejores resultados..."
          />
        </div>

        {/* Search button */}
        <button
          type="button"
          onClick={handleSearch}
          disabled={searchMutation.isPending || !selectedClient || !selectedArea || problemDescription.trim().length < 10}
          className="neo-pill neo-pill--primary neo-form-search-btn"
        >
          {searchMutation.isPending ? (
            <>Buscando<span className="neo-loading-dots"><span>.</span><span>.</span><span>.</span></span></>
          ) : (
            <><Search size={15} /> Buscar Casos de Uso</>
          )}
        </button>
        {searchMutation.isPending && <NeoLoader compact />}
      </div>

      {/* Right: Client Preview */}
      <div className="neo-client-preview">
        {selectedClient ? (
          <>
            <div className="neo-client-preview__hero">
              <div className="neo-client-preview__avatar">
                <Image
                  src={`/logos/companies/${slugifyCompany(selectedClient.name)}.png`}
                  alt={selectedClient.display_name}
                  width={48}
                  height={48}
                  className="neo-form-select__logo-img"
                  unoptimized
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                />
              </div>
              <div>
                <h3 className="neo-client-preview__name">{selectedClient.display_name}</h3>
                <p className="neo-client-preview__sector">{selectedClient.vertical}{selectedArea ? ` · ${selectedArea}` : ''}</p>
              </div>
            </div>

            {/* KPIs */}
            <div className="neo-client-kpis">
              {[
                { label: 'Revenue', value: profilePayload?.revenue ? String(profilePayload.revenue) : 'N/A' },
                { label: 'Satisfaccion', value: profilePayload?.satisfaction ? String(profilePayload.satisfaction) : 'N/A' },
                { label: 'Empleados TI', value: profilePayload?.empleados_ti ? String(profilePayload.empleados_ti) : 'N/A' },
                { label: 'Proyectos', value: profilePayload?.proyectos ? String(profilePayload.proyectos) : 'N/A' },
              ].map((kpi) => (
                <div key={kpi.label} className="neo-client-kpi">
                  <span className="neo-client-kpi__value">{kpi.value}</span>
                  <span className="neo-client-kpi__label">{kpi.label}</span>
                </div>
              ))}
            </div>

            {/* Alerts */}
            <div className="neo-client-section">
              <h4 className="neo-client-section__title">
                <AlertCircle size={13} /> Alertas del Radar
              </h4>
              <div className="neo-client-alerts">
                {profilePayload?.alerts ? (
                  (profilePayload.alerts as Array<{severity: string; title: string}>).slice(0, 3).map((alert, i) => (
                    <span key={i} className={`neo-alert-dot neo-alert-dot--${alert.severity}`}>
                      {alert.title}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Ejecuta radar para ver alertas</span>
                )}
              </div>
            </div>

            {/* Latest Insights */}
            <div className="neo-client-section">
              <h4 className="neo-client-section__title">
                <Lightbulb size={13} /> Ultimos Insights
              </h4>
              <div className="neo-client-insights-list">
                {insights.length > 0 ? (
                  insights.map((insight: Record<string, unknown>, i: number) => {
                    const type = String((insight as Record<string, unknown>).category ?? (insight as Record<string, unknown>).type ?? 'Contexto')
                    return (
                      <div key={i} className="neo-mini-insight">
                        <span className={`neo-insight-type-tag neo-insight-type-tag--${type.toLowerCase().replace(/\s/g, '_')}`}>
                          {type}
                        </span>
                        <span className="neo-mini-insight__text">
                          {String((insight as Record<string, unknown>).value ?? (insight as Record<string, unknown>).description ?? '')}
                        </span>
                      </div>
                    )
                  })
                ) : (
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Sin insights disponibles</span>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="neo-client-preview__empty">
            <Building size={40} strokeWidth={1} />
            <p>Selecciona un cliente para ver su perfil</p>
          </div>
        )}
      </div>
    </div>
  )
}
