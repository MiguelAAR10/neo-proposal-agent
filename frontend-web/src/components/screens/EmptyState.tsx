'use client'

import { Sparkles, Users, Lightbulb, FileText, Users2 } from 'lucide-react'
import { GhostSidebar } from '@/components/layout/GhostSidebar'

interface EmptyStateProps {
  onStart: () => void
}

export function EmptyState({ onStart }: EmptyStateProps) {
  const stats = [
    { label: 'Clientes Priorizados', value: '12', icon: Users },
    { label: 'Insights Activos', value: '47', icon: Lightbulb },
    { label: 'Propuestas en Curso', value: '8', icon: FileText },
    { label: 'Equipos', value: '4', icon: Users2 },
  ]

  return (
    <div className="neo-empty-screen">
      <GhostSidebar />

      <div className="neo-empty-screen__content">
        {/* Ambient orbs */}
        <div className="neo-ambient-orb neo-ambient-orb--purple" />
        <div className="neo-ambient-orb neo-ambient-orb--blue" />

        {/* Welcome card */}
        <div className="neo-welcome-card">
          <div className="neo-welcome-card__icon">
            <Sparkles size={28} />
          </div>
          <h2 className="neo-welcome-card__title">
            Bienvenido a Neo Intelligence
          </h2>
          <p className="neo-welcome-card__desc">
            Conecta insights de mercado con soluciones tecnologicas de alto impacto.
            Descubre necesidades del cliente, genera propuestas con IA y asigna equipos de consultoria.
          </p>
          <button
            type="button"
            onClick={onStart}
            className="neo-pill neo-pill--primary neo-welcome-card__cta"
          >
            <Sparkles size={15} />
            Iniciar Descubrimiento
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="neo-stats-bar">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="neo-stat-item">
              <Icon size={14} className="neo-stat-item__icon" />
              <span className="neo-stat-item__value">{stat.value}</span>
              <span className="neo-stat-item__label">{stat.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
