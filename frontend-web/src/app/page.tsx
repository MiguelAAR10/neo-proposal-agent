'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Loader2,
  WandSparkles,
  RefreshCcw,
  AlertCircle,
  Copy,
  Check,
  LayoutDashboard,
  Sparkles,
  PanelLeftOpen,
  PanelLeftClose,
  TriangleAlert,
} from 'lucide-react'
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

function companyLogoPath(company: string): string {
  const key = (company || '').trim().toLowerCase()
  if (!key) return ''
  const map: Record<string, string> = {
    bcp: 'bcp.png',
    interbank: 'interbank.png',
    bbva: 'bbva.png',
    alicorp: 'alicorp.png',
    rimac: 'rimac.png',
    pacifico: 'pacifico.png',
    scotiabank: 'scotiabank.png',
    mibanco: 'mibanco.png',
    credicorp: 'credicorp.png',
    'plaza vea': 'plaza-vea.png',
    falabella: 'falabella.png',
    sodimac: 'sodimac.png',
  }
  const file = map[key]
  return file ? `/logos/companies/${file}` : ''
}

export default function Home() {
  const {
    threadId,
    phase,
    empresa,
    area,
    error,
    warning,
    cases,
    selectedCaseIds,
    proposal,
    perfilCliente,
    inteligenciaSector,
    setProposal,
    setError,
    setWarning,
    setLoading,
    selectCase,
    unselectCase,
    reset,
  } = useAgentStore()

  const [copied, setCopied] = useState(false)
  const [companyQuery, setCompanyQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState<'all' | 'NEO' | 'AI'>('all')
  const [casesSidebarOpen, setCasesSidebarOpen] = useState(true)
  const [failedLogoSrc, setFailedLogoSrc] = useState<string | null>(null)

  const visibleCases = useMemo(() => {
    const q = companyQuery.trim().toLowerCase()
    return cases.filter((c) => {
      const sourceOk = sourceFilter === 'all' || c.tipo === sourceFilter
      const text = `${c.titulo} ${c.empresa} ${c.problema} ${c.match_reason || ''}`.toLowerCase()
      const searchOk = !q || text.includes(q)
      return sourceOk && searchOk
    })
  }, [cases, companyQuery, sourceFilter])

  const selectableIds = useMemo(() => visibleCases.map((c) => c.id), [visibleCases])

  const unselectedIds = useMemo(() => {
    const selected = new Set(selectedCaseIds)
    return selectableIds.filter((id) => !selected.has(id))
  }, [selectedCaseIds, selectableIds])

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
  const companyLogo = useMemo(() => companyLogoPath(empresa), [empresa])

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
      setWarning(data.warning ?? null)
      setError(null)
      setLoading(false)
    },
    onError: (err: unknown) => {
      setError(getErrorMessage(err, 'No se pudo generar la propuesta.'))
      setLoading(false)
    },
  })

  const handleSelectTop = (count: number) => {
    for (const id of unselectedIds.slice(0, count)) {
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
    <main className="neo-shell neo-shell-vivid min-h-screen px-3 md:px-6 py-4 md:py-6">
      <div className="neo-content max-w-[1780px] mx-auto space-y-3">
        <section className="neo-glass-card neo-hero neo-hero-compact p-3 md:p-4 relative overflow-hidden">
          <div className="absolute -right-8 -top-10 h-20 w-20 rounded-full blur-3xl" style={logoStyle} />
          <div className="neo-hero-ribbon neo-hero-ribbon-a" />
          <div className="neo-hero-ribbon neo-hero-ribbon-b" />
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between mb-2 relative z-10">
            <div className="flex items-center gap-3 min-w-0">
              <div className="h-9 w-9 rounded-xl border border-white/20 overflow-hidden flex items-center justify-center text-[11px] font-semibold text-white" style={logoStyle}>
                {companyLogo && failedLogoSrc !== companyLogo ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={companyLogo}
                    alt={`Logo ${empresa || 'Cliente'}`}
                    width={30}
                    height={30}
                    className="object-contain"
                    onError={() => setFailedLogoSrc(companyLogo)}
                  />
                ) : (
                  initials(empresa || 'Cliente')
                )}
              </div>
              <div className="min-w-0">
                <h1 className="text-xl md:text-2xl font-semibold text-[var(--foreground)] tracking-tight neo-title-gradient">
                  NEO Proposal Agent
                </h1>
                <p className="text-[11px] md:text-xs text-slate-200 truncate">
                  {empresa || 'Cliente priorizado'}{area ? ` • ${area}` : ''} • Panel lateral de casos desplegable
                </p>
                <p className="text-[11px] mt-0.5 neo-business-copy line-clamp-1">
                  De casos a <span className="neo-highlight">decisión comercial</span> con <span className="neo-highlight-cyan">evidencia</span> y <span className="neo-highlight-blue">ROI</span>.
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
          <div className="neo-hero-tags mb-2">
            <span>HITL</span>
            <span>Casos Priorizados</span>
            <span className="hidden md:inline-flex">Propuesta + Chat</span>
          </div>
          <InitialForm compact />
        </section>

        {error && (
          <section className="neo-glass-card rounded-2xl border-rose-300/30 bg-rose-300/10 p-3 text-sm text-rose-100 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <span>{error}</span>
          </section>
        )}

        {warning && (
          <section className="neo-glass-card rounded-2xl border-amber-300/35 bg-amber-200/10 p-3 text-sm text-amber-100 flex items-start gap-2">
            <TriangleAlert className="w-4 h-4 mt-0.5" />
            <span>{warning}</span>
          </section>
        )}

        <section className="grid grid-cols-1 xl:grid-cols-[auto_1fr] gap-4 items-start">
          <aside
            className={`neo-glass-card transition-all duration-300 overflow-hidden ${casesSidebarOpen ? 'xl:w-[520px] p-4 md:p-5' : 'xl:w-[74px] p-2.5'}`}
          >
            <div className="flex items-center justify-between gap-2 mb-2">
              {casesSidebarOpen ? (
                <>
                  <h2 className="text-sm md:text-base font-semibold text-[var(--foreground)]">Casos sugeridos</h2>
                  <span className="text-[11px] md:text-xs text-slate-200">{selectedCaseIds.length} seleccionados</span>
                </>
              ) : (
                <span className="text-[11px] text-slate-200 font-semibold">Casos</span>
              )}
              <button
                type="button"
                onClick={() => setCasesSidebarOpen((v) => !v)}
                className="neo-pill inline-flex items-center justify-center h-8 w-8 border border-white/20 bg-white/10 text-slate-100"
                title={casesSidebarOpen ? 'Ocultar panel de casos' : 'Mostrar panel de casos'}
              >
                {casesSidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
              </button>
            </div>

            {casesSidebarOpen ? (
              <>
                <div className="grid grid-cols-1 gap-2 mb-3">
                  <input
                    value={companyQuery}
                    onChange={(e) => setCompanyQuery(e.target.value)}
                    placeholder="Buscar por empresa, título o problema..."
                    className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-slate-100 outline-none focus:ring-2 focus:ring-[var(--accent)]"
                  />
                  <div className="grid grid-cols-[1fr_auto_auto] gap-2">
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
                    <button
                      type="button"
                      onClick={handleClearSelection}
                      disabled={selectedCaseIds.length === 0}
                      className="neo-pill px-3 py-2 text-xs border border-white/20 bg-white/10 text-slate-100 disabled:opacity-50"
                    >
                      Limpiar
                    </button>
                  </div>
                </div>

                <p className="text-[11px] text-slate-300 inline-flex items-center gap-1 mb-3">
                  <Sparkles className="w-3.5 h-3.5 text-[var(--accent)]" /> Selecciona el caso y abre evidencia desde la ficha.
                </p>
                <div className="neo-value-callout mb-3">
                  <p className="neo-value-title">Cómo decidir rápido</p>
                  <p className="neo-value-line">
                    1) Prioriza fichas con <span className="neo-highlight">match alto</span>.
                  </p>
                  <p className="neo-value-line">
                    2) Revisa <span className="neo-highlight-cyan">diapositivas de evidencia</span>.
                  </p>
                  <p className="neo-value-line">
                    3) Selecciona solo casos con <span className="neo-highlight-blue">valor de negocio claro</span>.
                  </p>
                </div>

                {visibleCases.length === 0 ? (
                  <div className="rounded-2xl border border-white/12 bg-white/6 p-5 text-sm text-slate-300">
                    No hay resultados para el filtro actual.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-3 max-h-[72vh] overflow-y-auto pr-1">
                    {visibleCases.map((caseData: Case) => (
                      <CaseFlashCard key={caseData.id} caseData={caseData} />
                    ))}
                  </div>
                )}
              </>
            ) : (
              <div className="h-full min-h-[300px] flex items-center justify-center">
                <button
                  type="button"
                  onClick={() => setCasesSidebarOpen(true)}
                  className="neo-pill inline-flex items-center gap-1 px-2.5 py-1.5 text-[11px] text-slate-100 border border-white/20 bg-white/10"
                >
                  <PanelLeftOpen className="w-3.5 h-3.5" /> Ver casos
                </button>
              </div>
            )}
          </aside>

          <article className="neo-right-stage space-y-3 p-3 md:p-4">
            <div className="neo-glass-card neo-right-card p-4">
              <div className="flex items-center justify-between gap-2 mb-2">
                <h2 className="text-sm md:text-base font-semibold text-[var(--foreground)] neo-section-title">Propuesta de Valor</h2>
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
              <p className="text-xs text-slate-300 mb-3">
                Construye una narrativa ejecutiva: <span className="neo-highlight">dolor</span> {'->'} <span className="neo-highlight-cyan">solución</span> {'->'} <span className="neo-highlight-blue">retorno esperado</span>.
              </p>
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

            <div className="neo-right-card">
              <ChatPanel />
            </div>

            <div className="neo-glass-card neo-right-card p-4 md:p-5 space-y-3">
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
