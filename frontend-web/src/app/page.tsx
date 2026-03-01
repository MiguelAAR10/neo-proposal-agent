'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Loader2, WandSparkles, RefreshCcw, AlertCircle, Copy, Check, LayoutDashboard, Sparkles } from 'lucide-react'
import { InitialForm } from '@/components/forms/InitialForm'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { apiClient } from '@/lib/api'
import { getErrorMessage } from '@/lib/error'
import { useAgentStore, type Case } from '@/stores/agentStore'
import { CaseFlashCard } from '@/components/cards/CaseFlashCard'

function extractContextSnippets(
  perfilCliente: Record<string, unknown> | null,
  inteligenciaSector: Record<string, unknown> | null,
): string[] {
  const snippets: string[] = []

  const objetivos = perfilCliente?.objetivos
  if (Array.isArray(objetivos)) {
    for (const item of objetivos) snippets.push(`Objetivo cliente: ${String(item)}`)
  }

  const painPoints = perfilCliente?.pain_points
  if (Array.isArray(painPoints)) {
    for (const item of painPoints) snippets.push(`Pain point: ${String(item)}`)
  }

  const notas = perfilCliente?.notas
  if (typeof notas === 'string' && notas.trim()) snippets.push(`Nota cliente: ${notas.trim()}`)

  const tendencias = inteligenciaSector?.tendencias
  if (Array.isArray(tendencias)) {
    for (const item of tendencias) snippets.push(`Tendencia sector: ${String(item)}`)
  }

  return snippets.slice(0, 10)
}

function hashToHue(input: string): number {
  let hash = 0
  for (let i = 0; i < input.length; i += 1) {
    hash = input.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash) % 360
}

function initials(name: string): string {
  const raw = (name || 'Cliente').trim()
  const parts = raw.split(/\s+/).slice(0, 2)
  return parts.map((p) => p[0]?.toUpperCase() || '').join('') || 'CL'
}

export default function Home() {
  const {
    threadId,
    phase,
    empresa,
    area,
    error,
    cases,
    selectedCaseIds,
    proposal,
    perfilCliente,
    inteligenciaSector,
    setProposal,
    setError,
    setLoading,
    selectCase,
    unselectCase,
    reset,
  } = useAgentStore()

  const [copied, setCopied] = useState(false)
  const [companyQuery, setCompanyQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState<'all' | 'NEO' | 'AI'>('all')

  const visibleCases = useMemo(() => {
    const q = companyQuery.trim().toLowerCase()
    return cases.filter((c) => {
      const sourceOk = sourceFilter === 'all' || c.tipo === sourceFilter
      const text = `${c.titulo} ${c.empresa} ${c.problema}`.toLowerCase()
      const searchOk = !q || text.includes(q)
      return sourceOk && searchOk
    })
  }, [cases, companyQuery, sourceFilter])

  const selectableWithUrlIds = useMemo(
    () => visibleCases.filter((c) => !!c.url_slide).map((c) => c.id),
    [visibleCases],
  )

  const unselectedWithUrlIds = useMemo(() => {
    const selected = new Set(selectedCaseIds)
    return selectableWithUrlIds.filter((id) => !selected.has(id))
  }, [selectedCaseIds, selectableWithUrlIds])

  const snippets = useMemo(
    () => extractContextSnippets(perfilCliente as Record<string, unknown> | null, inteligenciaSector as Record<string, unknown> | null),
    [perfilCliente, inteligenciaSector],
  )

  const logoHue = useMemo(() => hashToHue(empresa || 'NEO'), [empresa])
  const logoStyle = useMemo(
    () => ({
      background: `radial-gradient(circle at 30% 30%, hsla(${logoHue}, 92%, 72%, 0.5), hsla(${(logoHue + 40) % 360}, 88%, 60%, 0.22))`,
    }),
    [logoHue],
  )

  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!threadId) throw new Error('No hay thread activo')
      setLoading(true)
      const response = await apiClient.post(`/agent/${threadId}/select`, {
        case_ids: selectedCaseIds,
      })
      return response.data
    },
    onSuccess: (data) => {
      setProposal(data.propuesta_final)
      setError(null)
      setLoading(false)
    },
    onError: (err: unknown) => {
      setError(getErrorMessage(err, 'No se pudo generar la propuesta.'))
      setLoading(false)
    },
  })

  const handleSelectTop = (count: number) => {
    for (const id of unselectedWithUrlIds.slice(0, count)) {
      selectCase(id)
    }
  }

  const handleClearSelection = () => {
    for (const id of selectedCaseIds) {
      unselectCase(id)
    }
  }

  const handleCopyProposal = async () => {
    if (!proposal) return
    try {
      await navigator.clipboard.writeText(proposal)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setError('No se pudo copiar la propuesta al portapapeles.')
    }
  }

  const canGenerate = !!threadId && selectedCaseIds.length > 0

  return (
    <main className="neo-shell min-h-screen px-3 md:px-6 py-4 md:py-6">
      <div className="neo-content max-w-[1700px] mx-auto space-y-4">
        <section className="neo-glass-card p-4 md:p-5 relative overflow-hidden">
          <div className="absolute -right-8 -top-10 h-28 w-28 rounded-full blur-3xl" style={logoStyle} />
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-3 relative z-10">
            <div className="flex items-center gap-3 min-w-0">
              <div className="h-10 w-10 rounded-2xl border border-white/20 flex items-center justify-center text-xs font-semibold text-white" style={logoStyle}>
                {initials(empresa || 'Cliente')}
              </div>
              <div className="min-w-0">
                <h1 className="text-2xl md:text-3xl font-semibold text-[var(--foreground)] tracking-tight">
                  NEO Proposal Agent
                </h1>
                <p className="text-xs md:text-sm text-slate-200 truncate">
                  {empresa || 'Cliente priorizado'}{area ? ` • ${area}` : ''} • Flujo visual 2 paneles
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link
                href="/ops"
                className="neo-pill inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-100 border border-white/20 bg-white/10 hover:bg-white/15"
              >
                <LayoutDashboard className="w-3.5 h-3.5" /> Panel Ops
              </Link>
              <button
                type="button"
                onClick={reset}
                className="neo-pill inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-100 border border-white/20 bg-white/10 hover:bg-white/15"
              >
                <RefreshCcw className="w-3.5 h-3.5" /> Reiniciar
              </button>
            </div>
          </div>
          <InitialForm compact />
        </section>

        {error && (
          <section className="neo-glass-card rounded-2xl border-rose-300/30 bg-rose-300/10 p-3 text-sm text-rose-100 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <span>{error}</span>
          </section>
        )}

        <section className="grid grid-cols-1 xl:grid-cols-[1.25fr_1fr] gap-4 items-start">
          <article className="neo-glass-card p-4 md:p-5">
            <div className="flex items-center justify-between gap-2 mb-3">
              <h2 className="text-sm md:text-base font-semibold text-[var(--foreground)]">Fichas dinámicas de casos</h2>
              <span className="text-[11px] md:text-xs text-slate-200">{selectedCaseIds.length} seleccionados</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-2 mb-3">
              <input
                value={companyQuery}
                onChange={(e) => setCompanyQuery(e.target.value)}
                placeholder="Buscar por empresa, título o problema..."
                className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-slate-100 outline-none focus:ring-2 focus:ring-[var(--accent)]"
              />
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value as 'all' | 'NEO' | 'AI')}
                className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-slate-100 outline-none"
              >
                <option value="all">Todos</option>
                <option value="NEO">Solo NEO</option>
                <option value="AI">Solo AI</option>
              </select>
              <button
                type="button"
                onClick={() => handleSelectTop(4)}
                className="neo-pill px-3 py-2 text-xs border border-white/20 bg-white/10 text-slate-100"
              >
                Top 4
              </button>
            </div>

            <div className="mb-3 flex items-center gap-2 flex-wrap">
              <button
                type="button"
                onClick={() => handleSelectTop(8)}
                className="neo-pill px-3 py-1.5 text-[11px] border border-white/20 bg-white/10 text-slate-100"
              >
                Seleccionar top 8
              </button>
              <button
                type="button"
                onClick={handleClearSelection}
                disabled={selectedCaseIds.length === 0}
                className="neo-pill px-3 py-1.5 text-[11px] border border-white/20 bg-white/10 text-slate-100 disabled:opacity-50"
              >
                Limpiar selección
              </button>
              <span className="text-[11px] text-slate-300 inline-flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-[var(--accent)]" /> Hover/tap para voltear ficha
              </span>
            </div>

            {visibleCases.length === 0 ? (
              <div className="rounded-2xl border border-white/12 bg-white/6 p-5 text-sm text-slate-300">
                No hay casos visibles con esos filtros. Ajusta búsqueda o fuente.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[68vh] overflow-y-auto pr-1">
                {visibleCases.map((caseData: Case) => (
                  <CaseFlashCard key={caseData.id} caseData={caseData} />
                ))}
              </div>
            )}
          </article>

          <article className="space-y-3">
            <div className="neo-glass-card p-4">
              <div className="flex items-center justify-between gap-2 mb-2">
                <h2 className="text-sm md:text-base font-semibold text-[var(--foreground)]">Propuesta de valor viva</h2>
                <button
                  type="button"
                  onClick={handleCopyProposal}
                  disabled={!proposal}
                  className="text-[11px] inline-flex items-center gap-1 px-2.5 py-1.5 rounded-full border border-white/15 bg-white/8 text-slate-100 hover:bg-white/12 disabled:opacity-50"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'Copiada' : 'Copiar'}
                </button>
              </div>
              <p className="text-xs text-slate-300 mb-3">Genera con casos seleccionados y luego refina por chat.</p>
              <button
                type="button"
                onClick={() => generateMutation.mutate()}
                disabled={!canGenerate || generateMutation.isPending}
                className="neo-pill w-full h-10 inline-flex items-center justify-center gap-2 text-sm font-semibold text-white bg-[var(--accent-soft)] hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generateMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Generando...
                  </>
                ) : (
                  <>
                    <WandSparkles className="w-4 h-4" /> Generar propuesta
                  </>
                )}
              </button>
              {phase === 'complete' && proposal && (
                <p className="mt-2 text-[11px] text-emerald-200">Propuesta lista para refinamiento.</p>
              )}
            </div>

            <ChatPanel />

            <div className="neo-glass-card p-4 md:p-5 space-y-3">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-3 min-h-[240px] max-h-[38vh] overflow-y-auto">
                {proposal ? (
                  <pre className="whitespace-pre-wrap text-sm leading-relaxed text-slate-100 font-sans">{proposal}</pre>
                ) : (
                  <p className="text-xs text-slate-300">Aquí aparecerá la propuesta generada.</p>
                )}
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-2">Contexto arrastrable</h3>
                <div className="flex flex-wrap gap-2">
                  {snippets.length === 0 && <p className="text-xs text-slate-400">Sin contexto adicional aún.</p>}
                  {snippets.map((snippet) => (
                    <button
                      key={snippet}
                      type="button"
                      draggable
                      onDragStart={(e) => e.dataTransfer.setData('text/plain', snippet)}
                      className="text-[11px] px-2.5 py-1.5 rounded-full border border-white/15 bg-white/8 text-slate-100 hover:bg-white/12 text-left"
                      title="Arrastra este contexto al chat"
                    >
                      {snippet}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </article>
        </section>
      </div>
    </main>
  )
}
