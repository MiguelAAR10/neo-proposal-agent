'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, AlertTriangle, BarChart3, RefreshCcw, ShieldCheck, ArrowLeft, Download } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { getErrorMessage } from '@/lib/error'

interface FunnelRates {
  with_cases_over_started: number
  selected_over_started: number
  completed_over_started: number
  refined_over_completed: number
}

interface FunnelSummary {
  source: string
  window_sessions: number
  sessions_with_cases: number
  sessions_selected: number
  sessions_completed: number
  sessions_refined: number
  chat_interactions: number
  guardrail_blocked_interactions: number
  rates: FunnelRates
}

interface FunnelSession {
  thread_id: string
  empresa: string
  area: string
  total_cases: number
  selected_count: number
  proposal_generated: boolean
  refined_count: number
  chat_count: number
  guardrail_blocked_count: number
  last_update_utc: string
}

interface FunnelResponse {
  status: string
  environment: string
  query?: {
    company?: string
    time_range?: string
    completed_only?: boolean
    page?: number
    page_size?: number
    offset?: number
  }
  funnel: FunnelSummary
  sessions: {
    source: string
    returned: number
    offset: number
    limit: number
    total_available: number
    total_filtered: number
    items: FunnelSession[]
  }
}

interface AnalyticsResponse {
  status: string
  environment: string
  chat_analytics: {
    window_events: number
    guardrail_block_rate: number
    no_case_usage_rate: number
    top_case_ids: [string, number][]
    top_companies: [string, number][]
  }
}

interface AlertsResponse {
  status: string
  environment: string
  chat_alerts: {
    severity: 'ok' | 'warning' | 'critical'
    codes: string[]
    recommended_actions: {
      code: string
      priority: string
      owner: string
      playbook_hint: string
    }[]
  }
}

interface FunnelHistoryResponse {
  status: string
  environment: string
  history: {
    source: string
    bucket: 'hour' | 'day'
    returned_buckets: number
    series: Array<{
      bucket_start_utc: string
      metrics: {
        started: number
        completed: number
        selected: number
        completed_over_started: number
      }
    }>
  }
}

function pct(v: number | undefined): string {
  if (typeof v !== 'number' || Number.isNaN(v)) return '0.0%'
  return `${(v * 100).toFixed(1)}%`
}

function severityClass(severity: string): string {
  if (severity === 'critical') return 'text-rose-200 border-rose-300/40 bg-rose-300/15'
  if (severity === 'warning') return 'text-amber-200 border-amber-300/40 bg-amber-300/15'
  return 'text-emerald-200 border-emerald-300/40 bg-emerald-300/15'
}

function severityRank(severity: string): number {
  if (severity === 'critical') return 3
  if (severity === 'warning') return 2
  return 1
}

export default function OpsPage() {
  const [adminToken, setAdminToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [funnel, setFunnel] = useState<FunnelResponse | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null)
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null)
  const [companyFilter, setCompanyFilter] = useState('')
  const [timeRange, setTimeRange] = useState<'all' | '1h' | '24h' | '7d'>('24h')
  const [completedOnly, setCompletedOnly] = useState(false)
  const [minSeverity, setMinSeverity] = useState<'ok' | 'warning' | 'critical'>('ok')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [sortBy, setSortBy] = useState<'last_update_utc' | 'empresa' | 'total_cases' | 'selected_count' | 'chat_count' | 'guardrail_blocked_count'>('last_update_utc')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [historyBucket, setHistoryBucket] = useState<'hour' | 'day'>('hour')
  const [history, setHistory] = useState<FunnelHistoryResponse | null>(null)

  const headers = useMemo(() => {
    if (!adminToken.trim()) return undefined
    return { Authorization: `Bearer ${adminToken.trim()}` }
  }, [adminToken])

  const loadAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [funnelRes, analyticsRes, alertsRes, historyRes] = await Promise.all([
        apiClient.get('/ops/funnel', {
          headers,
          params: {
            company: companyFilter || undefined,
            time_range: timeRange,
            completed_only: completedOnly,
            sort_by: sortBy,
            sort_dir: sortDir,
            page,
            page_size: pageSize,
          },
        }),
        apiClient.get('/ops/chat-analytics', { headers }),
        apiClient.get('/ops/chat-alerts', { headers }),
        apiClient.get('/ops/funnel/history', {
          headers,
          params: {
            bucket: historyBucket,
            limit_buckets: historyBucket === 'hour' ? 24 : 14,
            company: companyFilter || undefined,
            time_range: timeRange,
            completed_only: completedOnly,
          },
        }),
      ])
      setFunnel(funnelRes.data as FunnelResponse)
      setAnalytics(analyticsRes.data as AnalyticsResponse)
      setAlerts(alertsRes.data as AlertsResponse)
      setHistory(historyRes.data as FunnelHistoryResponse)
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'No se pudo cargar el panel operativo. Verifica credenciales admin y backend.'))
    } finally {
      setLoading(false)
    }
  }, [headers, companyFilter, timeRange, completedOnly, sortBy, sortDir, page, pageSize, historyBucket])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  useEffect(() => {
    setPage(1)
  }, [companyFilter, timeRange, completedOnly, sortBy, sortDir, pageSize])

  const handleExportCsv = async () => {
    try {
      const response = await apiClient.get('/ops/funnel/export', {
        headers,
        params: {
          format: 'csv',
          company: companyFilter || undefined,
          time_range: timeRange,
          completed_only: completedOnly,
          sort_by: sortBy,
          sort_dir: sortDir,
        },
        responseType: 'blob',
      })
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'ops_funnel_export.csv')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'No se pudo exportar CSV del funnel.'))
    }
  }

  const sessions = useMemo(() => funnel?.sessions?.items ?? [], [funnel])

  const localTopCompanies = useMemo(() => {
    const counts = new Map<string, number>()
    for (const s of sessions) {
      const name = s.empresa || 'N/A'
      counts.set(name, (counts.get(name) ?? 0) + 1)
    }
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]).slice(0, 6)
  }, [sessions])

  const topCases = analytics?.chat_analytics?.top_case_ids ?? []
  const recommended = alerts?.chat_alerts?.recommended_actions ?? []
  const severity = alerts?.chat_alerts?.severity || 'ok'
  const severityPass = severityRank(severity) >= severityRank(minSeverity)
  const funnelSummary = funnel?.funnel
  const totalFiltered = Number(funnel?.sessions?.total_filtered || 0)
  const totalPages = Math.max(1, Math.ceil(totalFiltered / pageSize))
  const series = history?.history?.series ?? []

  return (
    <main className="neo-shell min-h-screen px-3 md:px-6 py-5 md:py-7">
      <div className="neo-content max-w-[1520px] mx-auto space-y-4">
        <motion.section
          initial={{ opacity: 0, y: 10, filter: 'blur(6px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          className="neo-glass-card p-4 md:p-5"
        >
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-slate-300">MVP Ops Center</div>
              <h1 className="text-2xl md:text-3xl font-semibold text-[var(--foreground)]">Funnel y Riesgo Operativo</h1>
              <p className="text-xs md:text-sm text-slate-200">Visibilidad de conversión comercial y señales de guardrails en tiempo real.</p>
            </div>
            <div className="flex items-center gap-2">
              <Link
                href="/"
                className="neo-pill inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-100 border border-white/20 bg-white/10 hover:bg-white/15"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Volver a Propuesta
              </Link>
              <button
                type="button"
                onClick={() => void loadAll()}
                disabled={loading}
                className="neo-pill inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-white bg-[var(--accent-soft)] disabled:opacity-50"
              >
                <RefreshCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Actualizar
              </button>
              <button
                type="button"
                onClick={() => void handleExportCsv()}
                className="neo-pill inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-100 border border-white/20 bg-white/10 hover:bg-white/15"
              >
                <Download className="w-3.5 h-3.5" /> Exportar CSV
              </button>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-1 md:grid-cols-[1fr_auto] gap-2 items-center">
            <input
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              placeholder="Admin token (opcional en local)"
              className="w-full rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-sm text-slate-100 outline-none focus:ring-2 focus:ring-[var(--accent)]"
            />
            <p className="text-[11px] text-slate-300">Si backend exige auth, ingresa token y pulsa actualizar.</p>
          </div>
          {error && <p className="mt-2 text-xs text-rose-200">{error}</p>}
        </motion.section>

        <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          <div className="neo-glass-card p-4">
            <p className="text-[11px] uppercase tracking-wider text-slate-300">Conversión final</p>
            <p className="mt-1 text-2xl font-semibold text-white">{pct(funnelSummary?.rates?.completed_over_started)}</p>
            <p className="text-xs text-slate-300">sesiones completadas / iniciadas</p>
          </div>
          <div className="neo-glass-card p-4">
            <p className="text-[11px] uppercase tracking-wider text-slate-300">Cobertura con casos</p>
            <p className="mt-1 text-2xl font-semibold text-white">{pct(funnelSummary?.rates?.with_cases_over_started)}</p>
            <p className="text-xs text-slate-300">sesiones con casos relevantes</p>
          </div>
          <div className="neo-glass-card p-4">
            <p className="text-[11px] uppercase tracking-wider text-slate-300">Bloqueo guardrail</p>
            <p className="mt-1 text-2xl font-semibold text-white">{pct(analytics?.chat_analytics?.guardrail_block_rate)}</p>
            <p className="text-xs text-slate-300">sobre interacciones chat</p>
          </div>
          <div className="neo-glass-card p-4">
            <p className="text-[11px] uppercase tracking-wider text-slate-300">Severidad alerta</p>
            <p className="mt-2">
              <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${severityClass(severity)}`}>
                {severity.toUpperCase()}
              </span>
            </p>
            <p className="text-xs text-slate-300 mt-1">estado consolidado de riesgo operativo</p>
          </div>
        </section>

        <section className="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-4 items-start">
          <article className="neo-glass-card p-4 md:p-5">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="w-4 h-4 text-[var(--accent)]" />
              <h2 className="text-sm md:text-base font-semibold text-white">Sesiones recientes (funnel)</h2>
            </div>
            <div className="mb-3 grid grid-cols-1 md:grid-cols-6 gap-2">
              <input
                value={companyFilter}
                onChange={(e) => setCompanyFilter(e.target.value)}
                placeholder="Filtrar empresa..."
                className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-slate-100 outline-none focus:ring-2 focus:ring-[var(--accent)]"
              />
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as 'all' | '1h' | '24h' | '7d')}
                className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-slate-100 outline-none"
              >
                <option value="1h">Última 1h</option>
                <option value="24h">Últimas 24h</option>
                <option value="7d">Últimos 7 días</option>
                <option value="all">Todo</option>
              </select>
              <label className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-slate-100 inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={completedOnly}
                  onChange={(e) => setCompletedOnly(e.target.checked)}
                />
                Solo completadas
              </label>
              <select
                value={minSeverity}
                onChange={(e) => setMinSeverity(e.target.value as 'ok' | 'warning' | 'critical')}
                className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-slate-100 outline-none"
              >
                <option value="ok">Severidad mínima: OK</option>
                <option value="warning">Severidad mínima: WARNING</option>
                <option value="critical">Severidad mínima: CRITICAL</option>
              </select>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'last_update_utc' | 'empresa' | 'total_cases' | 'selected_count' | 'chat_count' | 'guardrail_blocked_count')}
                className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-slate-100 outline-none"
              >
                <option value="last_update_utc">Ordenar: última actualización</option>
                <option value="empresa">Ordenar: empresa</option>
                <option value="total_cases">Ordenar: casos</option>
                <option value="selected_count">Ordenar: seleccionados</option>
                <option value="chat_count">Ordenar: chats</option>
                <option value="guardrail_blocked_count">Ordenar: guardrails</option>
              </select>
              <select
                value={sortDir}
                onChange={(e) => setSortDir(e.target.value as 'asc' | 'desc')}
                className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-slate-100 outline-none"
              >
                <option value="desc">Dirección: DESC</option>
                <option value="asc">Dirección: ASC</option>
              </select>
            </div>
            <div className="mb-3 flex items-center justify-between gap-2">
              <p className="text-[11px] text-slate-300">
                Mostrando {sessions.length} de {totalFiltered} sesiones filtradas.
              </p>
              <div className="flex items-center gap-2">
                <select
                  value={pageSize}
                  onChange={(e) => setPageSize(Number(e.target.value))}
                  className="rounded-lg border border-white/15 bg-white/10 px-2 py-1 text-[11px] text-slate-100 outline-none"
                >
                  <option value={10}>10 / página</option>
                  <option value={20}>20 / página</option>
                  <option value={50}>50 / página</option>
                </select>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="rounded-lg border border-white/20 bg-white/8 px-2 py-1 text-[11px] text-slate-100 disabled:opacity-50"
                >
                  Anterior
                </button>
                <span className="text-[11px] text-slate-200">Página {page}/{totalPages}</span>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="rounded-lg border border-white/20 bg-white/8 px-2 py-1 text-[11px] text-slate-100 disabled:opacity-50"
                >
                  Siguiente
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[780px] text-xs">
                <thead>
                  <tr className="text-slate-300 border-b border-white/10">
                    <th className="text-left py-2 font-medium">Empresa</th>
                    <th className="text-left py-2 font-medium">Área</th>
                    <th className="text-left py-2 font-medium">Casos</th>
                    <th className="text-left py-2 font-medium">Seleccionados</th>
                    <th className="text-left py-2 font-medium">Completado</th>
                    <th className="text-left py-2 font-medium">Refine</th>
                    <th className="text-left py-2 font-medium">Chat</th>
                    <th className="text-left py-2 font-medium">Guardrail</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.length === 0 && (
                    <tr>
                      <td colSpan={8} className="py-4 text-slate-400">Sin sesiones disponibles en ventana actual.</td>
                    </tr>
                  )}
                  {sessions.map((s) => (
                    <tr key={s.thread_id} className="border-b border-white/6 text-slate-100">
                      <td className="py-2">{s.empresa || 'N/A'}</td>
                      <td className="py-2">{s.area || 'N/A'}</td>
                      <td className="py-2">{s.total_cases}</td>
                      <td className="py-2">{s.selected_count}</td>
                      <td className="py-2">{s.proposal_generated ? 'Sí' : 'No'}</td>
                      <td className="py-2">{s.refined_count}</td>
                      <td className="py-2">{s.chat_count}</td>
                      <td className="py-2">{s.guardrail_blocked_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="space-y-4">
            <div className="neo-glass-card p-4 md:p-5">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-[var(--accent)]" />
                <h2 className="text-sm md:text-base font-semibold text-white">Top empresas</h2>
              </div>
              <div className="space-y-2">
                {localTopCompanies.length === 0 && <p className="text-xs text-slate-400">Sin datos de empresas aún.</p>}
                {localTopCompanies.map(([name, count]) => (
                  <div key={name} className="rounded-xl border border-white/10 bg-white/6 px-3 py-2 flex items-center justify-between">
                    <span className="text-xs text-slate-100">{name}</span>
                    <span className="text-xs text-slate-300">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="neo-glass-card p-4 md:p-5">
              <div className="flex items-center gap-2 mb-2">
                <ShieldCheck className="w-4 h-4 text-[var(--accent)]" />
                <h2 className="text-sm md:text-base font-semibold text-white">Top case IDs</h2>
              </div>
              <div className="space-y-2">
                {topCases.length === 0 && <p className="text-xs text-slate-400">Sin casos usados todavía.</p>}
                {topCases.map(([caseId, count]) => (
                  <div key={caseId} className="rounded-xl border border-white/10 bg-white/6 px-3 py-2 flex items-center justify-between">
                    <span className="text-xs text-slate-100">{caseId}</span>
                    <span className="text-xs text-slate-300">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="neo-glass-card p-4 md:p-5">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-[var(--accent)]" />
                <h2 className="text-sm md:text-base font-semibold text-white">Acciones recomendadas</h2>
              </div>
              <div className="space-y-2">
                {!severityPass && (
                  <p className="text-xs text-slate-400">
                    La severidad actual ({severity.toUpperCase()}) no alcanza el umbral seleccionado ({minSeverity.toUpperCase()}).
                  </p>
                )}
                {severityPass && recommended.length === 0 && <p className="text-xs text-slate-400">No hay acciones críticas en esta ventana.</p>}
                {severityPass && recommended.map((action) => (
                  <div key={`${action.code}-${action.priority}`} className="rounded-xl border border-white/10 bg-white/6 px-3 py-2">
                    <p className="text-xs text-slate-100 font-medium">{action.code} · {action.priority.toUpperCase()}</p>
                    <p className="text-[11px] text-slate-300">Owner: {action.owner}</p>
                    <p className="text-[11px] text-slate-200 mt-1">{action.playbook_hint}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="neo-glass-card p-4 md:p-5">
              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-[var(--accent)]" />
                  <h2 className="text-sm md:text-base font-semibold text-white">Tendencia de conversión</h2>
                </div>
                <select
                  value={historyBucket}
                  onChange={(e) => setHistoryBucket(e.target.value as 'hour' | 'day')}
                  className="rounded-lg border border-white/15 bg-white/10 px-2 py-1 text-[11px] text-slate-100 outline-none"
                >
                  <option value="hour">Bucket hora</option>
                  <option value="day">Bucket día</option>
                </select>
              </div>
              <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                {series.length === 0 && <p className="text-xs text-slate-400">Sin historial disponible en esta ventana.</p>}
                {series.map((b) => (
                  <div key={b.bucket_start_utc} className="rounded-xl border border-white/10 bg-white/6 px-3 py-2">
                    <p className="text-[11px] text-slate-300">{new Date(b.bucket_start_utc).toLocaleString()}</p>
                    <p className="text-xs text-slate-100">
                      Iniciadas: {b.metrics.started} · Seleccionadas: {b.metrics.selected} · Completadas: {b.metrics.completed}
                    </p>
                    <p className="text-[11px] text-[var(--accent)] mt-0.5">
                      Conversión: {pct(b.metrics.completed_over_started)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </article>
        </section>
      </div>
    </main>
  )
}
