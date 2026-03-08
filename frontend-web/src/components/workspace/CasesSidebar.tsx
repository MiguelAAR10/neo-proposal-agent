'use client'

import { useMemo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { WandSparkles, Presentation, CheckCircle } from 'lucide-react'
import { useAppStore, type UseCase } from '@/stores/appStore'
import { useGenerateProposal } from '@/hooks/useApi'

export function CasesSidebar() {
  const {
    cases,
    selectedCaseIds,
    selectCase,
    unselectCase,
    proposalSentSuccess,
  } = useAppStore()

  const generateMutation = useGenerateProposal()
  const prefersReducedMotion = useReducedMotion()
  const shouldAnimate = !prefersReducedMotion

  const handleToggle = (id: string) => {
    if (selectedCaseIds.includes(id)) unselectCase(id)
    else selectCase(id)
  }

  return (
    <div className="neo-v4-cases-sidebar">
      <div className="neo-v4-cases-sidebar__header">
        <span className="neo-v4-cases-sidebar__title">
          Casos Sugeridos
        </span>
        <span className="neo-v4-cases-sidebar__count">{cases.length}</span>
      </div>

      <div className="neo-v4-cases-sidebar__scroll">
        <motion.div
          initial={shouldAnimate ? 'hidden' : false}
          animate={shouldAnimate ? 'show' : undefined}
          variants={{
            hidden: { opacity: 0 },
            show: { opacity: 1, transition: { staggerChildren: 0.05 } },
          }}
          style={{ display: 'grid', gap: 8 }}
        >
          {cases.map((c) => (
            <motion.div
              key={c.id}
              variants={{
                hidden: { opacity: 0, y: 8 },
                show: { opacity: 1, y: 0, transition: { duration: 0.22 } },
              }}
            >
              <SidebarCaseCard
                useCase={c}
                isSelected={selectedCaseIds.includes(c.id)}
                onToggle={() => handleToggle(c.id)}
              />
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Generate proposal button */}
      <div className="neo-v4-cases-sidebar__footer">
        {selectedCaseIds.length > 0 && (
          <span className="neo-v4-cases-sidebar__sel-count">
            {selectedCaseIds.length} seleccionado{selectedCaseIds.length !== 1 ? 's' : ''}
          </span>
        )}
        <button
          type="button"
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending || proposalSentSuccess}
          className={`neo-pill ${proposalSentSuccess ? 'neo-pill--success' : 'neo-pill--primary'} neo-v4-cases-sidebar__gen-btn`}
          style={proposalSentSuccess ? {
            background: 'linear-gradient(135deg, #059669, #10b981)',
            borderColor: '#10b981',
          } : undefined}
        >
          {proposalSentSuccess ? (
            <>
              <CheckCircle size={14} />
              Propuesta Generada
            </>
          ) : (
            <>
              <WandSparkles size={14} />
              {generateMutation.isPending ? 'Generando...' : 'Generar Propuesta'}
            </>
          )}
        </button>
      </div>
    </div>
  )
}

// ── Case Card ─────────────────────────────────────────────────────────────

function SidebarCaseCard({
  useCase,
  isSelected,
  onToggle,
}: {
  useCase: UseCase
  isSelected: boolean
  onToggle: () => void
}) {
  const tags = useMemo(() => {
    const t: string[] = []
    if (useCase.tipo) t.push(useCase.tipo)
    if (useCase.empresa) t.push(useCase.empresa)
    if (useCase.area) t.push(useCase.area)
    return t.slice(0, 3)
  }, [useCase])

  return (
    <article
      className={`neo-case-card${isSelected ? ' neo-case-card--selected' : ''}`}
      onClick={onToggle}
      style={{ cursor: 'pointer' }}
    >
      <div className="neo-case-card__header">
        <h4 className="neo-case-card__title">{useCase.titulo}</h4>
        <span className="neo-tag neo-tag--active">{Math.round(useCase.score)}</span>
      </div>

      <div className="neo-case-card__tags">
        {tags.map((tag) => (
          <span key={tag} className="neo-tag">{tag}</span>
        ))}
        {useCase.match_type && (
          <span className="neo-tag" style={{
            background: 'rgba(139, 92, 246, 0.15)',
            borderColor: 'rgba(139, 92, 246, 0.3)',
            color: '#c084fc',
          }}>
            {useCase.match_type}
          </span>
        )}
      </div>

      <div className="neo-case-card__body">
        <div className="neo-case-card__col">
          <p className="neo-case-card__col-label">Problema</p>
          <p className="neo-case-card__col-text">{useCase.problema}</p>
        </div>
        <div className="neo-case-card__col">
          <p className="neo-case-card__col-label">Solucion</p>
          <p className="neo-case-card__col-text">{useCase.solucion}</p>
        </div>
      </div>

      {useCase.kpi_impacto && (
        <div className="neo-case-card__kpi">
          <span>{useCase.kpi_impacto}</span>
        </div>
      )}

      <div className="neo-case-card__footer">
        <div className="neo-case-card__footer-actions">
          {useCase.url_slide && (
            <a
              href={useCase.url_slide}
              target="_blank"
              rel="noopener noreferrer"
              className="neo-case-url-btn"
              onClick={(e) => e.stopPropagation()}
            >
              <Presentation size={12} /> Ver Diapositivas
            </a>
          )}
          <button
            type="button"
            className={`neo-case-select-btn${isSelected ? ' neo-case-select-btn--active' : ''}`}
            onClick={(e) => { e.stopPropagation(); onToggle() }}
          >
            {isSelected ? 'Seleccionado' : 'Seleccionar'}
          </button>
        </div>
      </div>
    </article>
  )
}
