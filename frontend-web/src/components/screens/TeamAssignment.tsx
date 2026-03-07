'use client'

import { useState } from 'react'
import { Send, Crown, Brain, Beaker, Megaphone, Server, Check } from 'lucide-react'
import { useAppStore, type Team } from '@/stores/appStore'

const TEAMS: Team[] = [
  {
    id: 'analytics-ml',
    name: 'Analytics & ML',
    description: 'Modelos predictivos, analitica avanzada, scoring, recomendacion automatizada.',
    icon: 'brain',
    specialties: ['Machine Learning', 'Data Analytics', 'Predictive Models'],
    is_best_match: true,
  },
  {
    id: 'ai-lab',
    name: 'AI Lab',
    description: 'LLMs, computer vision, NLP, agentes autonomos, generative AI.',
    icon: 'beaker',
    specialties: ['LLMs', 'Computer Vision', 'NLP'],
  },
  {
    id: 'growth-crm',
    name: 'Growth & CRM',
    description: 'Estrategia de crecimiento, CRM, marketing automation, customer journey.',
    icon: 'megaphone',
    specialties: ['Strategy', 'CRM', 'Marketing Automation'],
  },
  {
    id: 'operaciones',
    name: 'Operaciones',
    description: 'Infraestructura, DevOps, cloud, SRE, automatizacion de procesos.',
    icon: 'server',
    specialties: ['Infrastructure', 'DevOps', 'Cloud', 'SRE'],
  },
]

const ICON_MAP: Record<string, typeof Brain> = {
  brain: Brain,
  beaker: Beaker,
  megaphone: Megaphone,
  server: Server,
}

interface TeamAssignmentProps {
  onSend: () => void
}

export function TeamAssignment({ onSend }: TeamAssignmentProps) {
  const { selectedTeam, setSelectedTeam, proposalRawText, selectedClient, selectedArea, cases, selectedCaseIds } = useAppStore()
  const [localTeam, setLocalTeam] = useState<Team | null>(TEAMS.find((t) => t.is_best_match) ?? null)

  const selectedCase = cases.find((c) => selectedCaseIds.includes(c.id)) ?? cases[0]
  const bestMatch = TEAMS.find((t) => t.is_best_match)

  const handleSelectTeam = (team: Team) => {
    setLocalTeam(team)
    setSelectedTeam(team)
  }

  const handleSend = () => {
    if (!localTeam) return
    setSelectedTeam(localTeam)
    onSend()
  }

  return (
    <div className="neo-team-assignment">
      {/* Left: Proposal Summary Card */}
      <div className="neo-team-proposal-card">
        <div className="neo-team-proposal-card__header">
          <h3>Tarjeta de Propuesta</h3>
          <span className="neo-tag neo-tag--active">{selectedCase?.score ? Math.round(selectedCase.score) : 92}</span>
        </div>

        <div className="neo-team-proposal-card__tags">
          {selectedCase?.tecnologias?.slice(0, 3).map((t) => (
            <span key={t} className="neo-tag">{t}</span>
          ))}
          {selectedArea && <span className="neo-tag">{selectedArea}</span>}
        </div>

        <h4 className="neo-team-proposal-card__title">
          {selectedCase?.titulo ?? 'Propuesta'}
        </h4>

        <div className="neo-team-proposal-card__section">
          <span className="neo-team-proposal-card__label">Problema</span>
          <p>{selectedCase?.problema ?? ''}</p>
        </div>

        <div className="neo-team-proposal-card__section">
          <span className="neo-team-proposal-card__label">Solucion</span>
          <p>{selectedCase?.solucion ?? ''}</p>
        </div>

        {selectedCase?.kpi_impacto && (
          <div className="neo-team-proposal-card__kpi">
            {selectedCase.kpi_impacto}
          </div>
        )}
      </div>

      {/* Right: Team Assignment */}
      <div className="neo-team-selection">
        <h3 className="neo-team-selection__title">Asignar Equipo de Consultoria</h3>

        {/* Director card */}
        <div className="neo-director-card">
          <Crown size={16} style={{ color: '#c084fc' }} />
          <div>
            <p className="neo-director-card__name">Director de Consultoria</p>
            <p className="neo-director-card__desc">Aprueba la asignacion del equipo</p>
          </div>
        </div>

        {/* Team cards */}
        <div className="neo-team-grid">
          {TEAMS.map((team) => {
            const Icon = ICON_MAP[team.icon] ?? Brain
            const isSelected = localTeam?.id === team.id
            return (
              <button
                key={team.id}
                type="button"
                onClick={() => handleSelectTeam(team)}
                className={`neo-team-card${isSelected ? ' neo-team-card--selected' : ''}${team.is_best_match ? ' neo-team-card--best' : ''}`}
              >
                {team.is_best_match && (
                  <span className="neo-team-card__best-badge">Best Match</span>
                )}
                <div className="neo-team-card__icon">
                  <Icon size={20} />
                </div>
                <h4 className="neo-team-card__name">{team.name}</h4>
                <p className="neo-team-card__desc">{team.description}</p>
                {isSelected && (
                  <div className="neo-team-card__check">
                    <Check size={14} />
                  </div>
                )}
              </button>
            )
          })}
        </div>

        {/* Suggestion box */}
        {bestMatch && (
          <div className="neo-team-suggestion">
            <p>
              <strong>Sugerencia NEO:</strong> {bestMatch.name} es el mejor match basado en el stack tecnologico
              y las capacidades requeridas. El consultor puede cambiar la seleccion.
            </p>
          </div>
        )}

        {/* Send button */}
        <button
          type="button"
          onClick={handleSend}
          disabled={!localTeam}
          className="neo-pill neo-pill--primary neo-team-send-btn"
        >
          <Send size={15} />
          Enviar al Equipo
        </button>
      </div>
    </div>
  )
}
