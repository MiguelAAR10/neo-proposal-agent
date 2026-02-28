'use client'

import { useAgentStore } from '@/stores/agentStore'
import { InitialForm } from '@/components/forms/InitialForm'
import { CaseCard } from '@/components/cards/CaseCard'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { Loader2, FileText, ArrowLeft, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function Home() {
  const { 
    phase, 
    cases, 
    neoCases,
    aiCases,
    topMatchGlobal,
    topMatchGlobalReason,
    selectedCaseIds, 
    empresa, 
    area, 
    threadId, 
    proposal,
    perfilCliente,
    error,
    setProposal, 
    setError,
    setLoading, 
    reset 
  } = useAgentStore()

  const generateMutation = useMutation({
    mutationFn: async () => {
      setLoading(true)
      const response = await apiClient.post(`/agent/${threadId}/select`, {
        case_ids: selectedCaseIds
      })
      return response.data
    },
    onSuccess: (data) => {
      setProposal(data.propuesta_final)
      setError(null)
      setLoading(false)
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail
      const message =
        (typeof detail === 'object' && detail?.message) ||
        (typeof detail === 'string' && detail) ||
        error?.message ||
        'No se pudo generar la propuesta.'
      setError(message)
      setLoading(false)
    }
  })

  const effectiveNeoCases = neoCases.length > 0 ? neoCases : cases.filter((c) => c.tipo === 'NEO')
  const effectiveAiCases = aiCases.length > 0 ? aiCases : cases.filter((c) => c.tipo === 'AI')

  return (
    <main className="neo-shell min-h-screen py-12 px-4 md:px-8">
      <div className="neo-content">
      <AnimatePresence mode="wait">
        {/* PHASE: IDLE (Formulario inicial) */}
        {phase === 'idle' && (
          <motion.div
            key="form"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="flex flex-col items-center justify-center min-h-[80vh]"
          >
            <div className="text-center mb-12">
              <h1 className="text-4xl font-semibold text-[var(--foreground)] mb-4 tracking-tight">
                NEO <span className="text-[var(--accent)]">Proposal</span> Agent
              </h1>
              <p className="text-lg text-slate-200/85 max-w-xl">
                Triangulamos casos de éxito, perfiles de cliente e inteligencia de sector para crear propuestas de impacto en minutos.
              </p>
            </div>
            <InitialForm />
          </motion.div>
        )}

        {/* PHASE: CURATING (Selección de casos) */}
        {phase === 'curating' && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="max-w-[1600px] mx-auto"
          >
            {/* Header de resultados */}
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4 px-4">
              <div>
                <button 
                  onClick={reset}
                  className="flex items-center text-sm text-slate-300 hover:text-white mb-2 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 mr-1" />
                  Nueva búsqueda
                </button>
                <h2 className="text-3xl font-semibold text-[var(--foreground)]">Casos Sugeridos</h2>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-slate-300">Para: <span className="font-semibold text-white">{empresa}</span></p>
                  <span className="text-slate-500">|</span>
                  <p className="text-slate-300">Área: <span className="font-semibold text-white">{area}</span></p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <p className="text-sm font-medium text-slate-300">
                  <span className="text-[var(--accent)] font-bold">{selectedCaseIds.length}</span> seleccionados
                </p>
                <button
                  onClick={() => generateMutation.mutate()}
                  disabled={selectedCaseIds.length === 0 || generateMutation.isPending}
                  className="neo-pill flex items-center bg-[var(--accent-soft)] text-white px-6 py-2.5 font-semibold hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-900/50"
                >
                  {generateMutation.isPending ? (
                    <>
                      <Loader2 className="animate-spin w-4 h-4 mr-2" />
                      Generando...
                    </>
                  ) : (
                    <>
                      <FileText className="w-4 h-4 mr-2" />
                      Generar Propuesta
                    </>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="mx-4 mb-6 neo-glass-card rounded-2xl border-rose-300/30 bg-rose-300/10 p-3 text-sm text-rose-100">
                {error}
              </div>
            )}

            {/* Split Layout */}
            <div className="flex flex-col lg:flex-row gap-8">
              {/* Main Content (Cards) */}
              <div className="flex-1 px-4">
                {/* Banner de Perfil (Si existe) */}
                {perfilCliente && perfilCliente.notas !== "Empresa nueva sin historial previo." && (
                  <div className="mb-8 p-4 bg-amber-200/15 border border-amber-200/30 rounded-xl flex items-start gap-3">
                    <div className="bg-amber-200/20 p-2 rounded-lg text-amber-200">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-amber-100">Conocimiento Institucional Detectado</h4>
                      <p className="text-xs text-amber-100/90 mt-0.5">{perfilCliente.notas}</p>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {topMatchGlobal && (
                    <div className="md:col-span-2 p-4 rounded-xl border border-indigo-200 bg-indigo-50/70">
                      <div className="flex items-start gap-3">
                        <div className="bg-indigo-100 p-2 rounded-lg text-indigo-700">
                          <Sparkles className="w-4 h-4" />
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-indigo-900">Top Match Global</h4>
                          <p className="text-xs text-indigo-800 mt-0.5">
                            {topMatchGlobal.titulo} • {topMatchGlobal.score_label ?? 'Muy relevante'} ({topMatchGlobal.confidence ?? `${Math.round((topMatchGlobal.score ?? 0) * 100)}% match`})
                          </p>
                          {topMatchGlobalReason && (
                            <p className="text-[11px] text-indigo-700 mt-1">{topMatchGlobalReason}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {effectiveNeoCases.length > 0 && (
                  <section className="mt-8">
                    <div className="mb-3 flex items-center gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider bg-emerald-200/20 text-emerald-100">
                        NEO
                      </span>
                      <h3 className="text-sm font-semibold text-slate-100">Casos ya ejecutados</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {effectiveNeoCases.map((c) => (
                        <CaseCard key={c.id} caseData={c} />
                      ))}
                    </div>
                  </section>
                )}

                {effectiveAiCases.length > 0 && (
                  <section className="mt-8">
                    <div className="mb-3 flex items-center gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider bg-blue-200/20 text-blue-100">
                        AI
                      </span>
                      <h3 className="text-sm font-semibold text-slate-100">Referencias externas</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {effectiveAiCases.map((c) => (
                        <CaseCard key={c.id} caseData={c} />
                      ))}
                    </div>
                  </section>
                )}

                {effectiveNeoCases.length === 0 && effectiveAiCases.length === 0 && (
                  <div className="mt-8 rounded-xl border border-dashed border-white/20 p-6 text-sm text-slate-200">
                    No encontramos casos con suficiente evidencia para este problema.
                  </div>
                )}
              </div>

              {/* Sidebar (Chat) */}
              <aside className="w-full lg:w-[400px] px-4">
                <div className="sticky top-8">
                  <ChatPanel />
                </div>
              </aside>
            </div>
          </motion.div>
        )}

        {/* PHASE: COMPLETE (Propuesta final) */}
        {phase === 'complete' && (
          <motion.div
            key="proposal"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-4xl mx-auto"
          >
            <div className="flex justify-between items-center mb-8">
              <button 
                onClick={() => useAgentStore.setState({ phase: 'curating' })}
                className="flex items-center text-sm text-slate-300 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Editar selección
              </button>
              <div className="flex gap-2">
                <button 
                  onClick={() => window.print()}
                  className="px-4 py-2 text-sm font-medium text-slate-100 bg-white/10 border border-white/20 rounded-lg hover:bg-white/15 transition-colors"
                >
                  Exportar PDF
                </button>
                <button 
                  onClick={reset}
                  className="px-4 py-2 text-sm font-medium text-white bg-[var(--accent-soft)] rounded-lg hover:brightness-110 transition-colors"
                >
                  Nueva Propuesta
                </button>
              </div>
            </div>

            {error && (
              <div className="mb-6 neo-glass-card rounded-2xl border-rose-300/30 bg-rose-300/10 p-3 text-sm text-rose-100">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
              <div className="neo-glass-card p-10 shadow-xl prose prose-invert max-w-none">
                <div className="whitespace-pre-wrap leading-relaxed text-[var(--foreground)]">
                  {proposal}
                </div>
              </div>
              <div className="lg:sticky lg:top-8 h-fit">
                <ChatPanel />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      </div>
    </main>
  )
}
