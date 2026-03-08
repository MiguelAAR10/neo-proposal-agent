'use client'

import { useState } from 'react'
import { Send, Crown, Brain, Beaker, Megaphone, Server, Check, Loader2, ExternalLink } from 'lucide-react'
import { useAppStore, type Team } from '@/stores/appStore'
import { useTeams, useAssignTeam } from '@/hooks/useApi'

const ICON_MAP: Record<string, typeof Brain> = {
  brain: Brain,
  beaker: Beaker,
  sparkles: Beaker,
  megaphone: Megaphone,
  target: Megaphone,
  server: Server,
  cog: Server,
}

interface TeamAssignmentProps {
  onSend: () => void
}

function cleanProposalLine(input: string): string {
  return input
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]/g, '$1')
    .replace(/^[-*•]\s*/, '')
    .replace(/^\d+\.\s*/, '')
    .trim()
}

function getBlockByHeading(raw: string, patterns: RegExp[]): string {
  let bestStart = -1
  let bestLength = 0

  patterns.forEach((pattern) => {
    const match = raw.match(pattern)
    if (match && typeof match.index === 'number') {
      if (bestStart === -1 || match.index < bestStart) {
        bestStart = match.index
        bestLength = match[0].length
      }
    }
  })

  if (bestStart < 0) return ''

  const after = raw.slice(bestStart + bestLength)
  const nextSection = after.match(/\n\s*(###?\s*[🔍💡🏗📊🗓🎯]|Secci[oó]n\s*\d+|Seccion\s*\d+)\b/i)
  const block = nextSection && typeof nextSection.index === 'number'
    ? after.slice(0, nextSection.index)
    : after

  return block.trim()
}

function getProposalSummary(
  structured: Record<string, unknown> | null | undefined,
  raw: string,
  mode: 'problema' | 'solucion',
): string {
  if (structured) {
    const key = mode === 'problema' ? 'diagnostico' : 'solucion'
    const section = structured[key]
    if (Array.isArray(section)) {
      const line = section.map((item) => cleanProposalLine(String(item ?? ''))).find((v) => v.length > 10)
      if (line) return line
    }
  }

  const patterns = mode === 'problema'
    ? [/###?\s*🔍/i, /diagn[oó]stico/i, /problema identificado/i, /secci[oó]n\s*1/i]
    : [/###?\s*💡/i, /soluci[oó]n propuesta/i, /secci[oó]n\s*2/i]

  const block = getBlockByHeading(raw, patterns)
  if (!block) return mode === 'problema'
    ? 'Resumen de problema no disponible.'
    : 'Resumen de solución no disponible.'

  const candidate = block
    .split('\n')
    .map((line) => cleanProposalLine(line))
    .find((line) => line.length > 12)

  return candidate ?? cleanProposalLine(block).slice(0, 240)
}

export function TeamAssignment({ onSend }: TeamAssignmentProps) {
  const {
    setSelectedTeam,
    selectedArea,
    selectedClient,
    cases,
    selectedCaseIds,
    proposalStructured,
    proposalRawText,
    threadId,
  } = useAppStore()
  const { data: teams = [], isLoading: isTeamsLoading, isError: isTeamsError } = useTeams(threadId)
  const assignMutation = useAssignTeam()
  const [localTeam, setLocalTeam] = useState<Team | null>(null)

  const proposalCase = cases.find((c) => selectedCaseIds.includes(c.id))
  const backupCase = proposalCase ?? cases.find((c) => Boolean(c.url_slide)) ?? cases[0]
  const problemSummary = getProposalSummary(proposalStructured, proposalRawText ?? '', 'problema')
  const solutionSummary = getProposalSummary(proposalStructured, proposalRawText ?? '', 'solucion')

  // Auto-select best match when teams load and no local selection yet
  const effectiveTeam = localTeam ?? teams.find((t) => t.is_best_match) ?? null
  const bestMatch = teams.find((t) => t.is_best_match)

  const handleSelectTeam = (team: Team) => {
    setLocalTeam(team)
    setSelectedTeam(team)
  }

  const handleSend = async () => {
    const team = effectiveTeam
    if (!team || !threadId) return
    setSelectedTeam(team)
    assignMutation.mutate(
      { threadId, teamId: team.id },
      { onSuccess: () => onSend() },
    )
  }

  return (
    <div className="neo-team-assignment">
      {/* Left: Proposal Summary Card */}
      <div className="neo-team-proposal-card">
        <div className="neo-team-proposal-card__header">
          <h3>Resumen de Propuesta</h3>
          <span className="neo-tag neo-tag--active">{backupCase?.score ? Math.round(backupCase.score) : 92}</span>
        </div>

        <div className="neo-team-proposal-card__tags">
          {backupCase?.tecnologias?.slice(0, 3).map((t) => (
            <span key={t} className="neo-tag">{t}</span>
          ))}
          {selectedArea && <span className="neo-tag">{selectedArea}</span>}
        </div>

        <h4 className="neo-team-proposal-card__title">
          {selectedClient?.display_name ?? 'Cliente'} · {selectedArea ?? 'General'}
        </h4>

        <div className="neo-team-proposal-card__section">
          <span className="neo-team-proposal-card__label">Problema</span>
          <p>{problemSummary}</p>
        </div>

        <div className="neo-team-proposal-card__section">
          <span className="neo-team-proposal-card__label">Solucion</span>
          <p>{solutionSummary}</p>
        </div>

        <div className="neo-team-proposal-card__section">
          <span className="neo-team-proposal-card__label">Caso de exito de respaldo</span>
          {backupCase ? (
            <p>
              {backupCase.titulo}
              {backupCase.url_slide ? (
                <>
                  {' '}
                  <a
                    href={backupCase.url_slide}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="neo-team-proposal-card__link"
                  >
                    Ver respaldo <ExternalLink size={12} />
                  </a>
                </>
              ) : ' (sin enlace disponible)'}
            </p>
          ) : (
            <p>No hay caso de respaldo disponible.</p>
          )}
        </div>

        {backupCase?.kpi_impacto && (
          <div className="neo-team-proposal-card__kpi">
            {backupCase.kpi_impacto}
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
          {isTeamsLoading ? (
            <div style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: 13 }}>
              <Loader2 size={16} className="neo-spin" /> Cargando equipos...
            </div>
          ) : isTeamsError ? (
            <div style={{ gridColumn: '1 / -1', fontSize: 13, color: 'var(--text-muted)' }}>
              No se pudieron cargar los equipos. Intenta de nuevo.
            </div>
          ) : teams.map((team) => {
            const Icon = ICON_MAP[team.icon] ?? Brain
            const isSelected = effectiveTeam?.id === team.id
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
          disabled={!effectiveTeam || assignMutation.isPending}
          className="neo-pill neo-pill--primary neo-team-send-btn"
        >
          {assignMutation.isPending ? (
            <><Loader2 size={15} className="neo-spin" /> Asignando...</>
          ) : (
            <><Send size={15} /> Enviar al Equipo</>
          )}
        </button>
        {assignMutation.isError && (
          <p style={{ fontSize: 12, color: 'var(--error)', marginTop: 8 }}>
            Error al asignar. Intenta de nuevo.
          </p>
        )}
      </div>
    </div>
  )
}
