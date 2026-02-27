'use client'

import { useAgentStore } from '@/stores/agentStore'
import { InitialForm } from '@/components/forms/InitialForm'
import { CaseCard } from '@/components/cards/CaseCard'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { Loader2, FileText, ArrowLeft, Send } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function Home() {
  const { 
    phase, 
    cases, 
    selectedCaseIds, 
    empresa, 
    area, 
    threadId, 
    proposal,
    perfilCliente,
    setProposal, 
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
      setLoading(false)
    },
    onError: (error: any) => {
      console.error(error)
      setLoading(false)
    }
  })

  return (
    <main className="min-h-screen bg-gray-50/50 py-12 px-4 md:px-8">
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
              <h1 className="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">
                NEO <span className="text-blue-600">Proposal</span> Agent
              </h1>
              <p className="text-lg text-gray-600 max-w-xl">
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
                  className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-2 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 mr-1" />
                  Nueva búsqueda
                </button>
                <h2 className="text-3xl font-bold text-gray-900">Casos Sugeridos</h2>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-gray-500">Para: <span className="font-semibold text-gray-700">{empresa}</span></p>
                  <span className="text-gray-300">|</span>
                  <p className="text-gray-500">Área: <span className="font-semibold text-gray-700">{area}</span></p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <p className="text-sm font-medium text-gray-600">
                  <span className="text-blue-600 font-bold">{selectedCaseIds.length}</span> seleccionados
                </p>
                <button
                  onClick={() => generateMutation.mutate()}
                  disabled={selectedCaseIds.length === 0 || generateMutation.isPending}
                  className="flex items-center bg-blue-600 text-white px-6 py-2.5 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-200"
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

            {/* Split Layout */}
            <div className="flex flex-col lg:flex-row gap-8">
              {/* Main Content (Cards) */}
              <div className="flex-1 px-4">
                {/* Banner de Perfil (Si existe) */}
                {perfilCliente && perfilCliente.notas !== "Empresa nueva sin historial previo." && (
                  <div className="mb-8 p-4 bg-amber-50 border border-orange-100 rounded-xl flex items-start gap-3">
                    <div className="bg-orange-100 p-2 rounded-lg text-orange-600">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-orange-800">Conocimiento Institucional Detectado</h4>
                      <p className="text-xs text-orange-700 mt-0.5">{perfilCliente.notas}</p>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {cases.map((c) => (
                    <CaseCard key={c.id} caseData={c} />
                  ))}
                </div>
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
                className="flex items-center text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Editar selección
              </button>
              <div className="flex gap-2">
                <button 
                  onClick={() => window.print()}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Exportar PDF
                </button>
                <button 
                  onClick={reset}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Nueva Propuesta
                </button>
              </div>
            </div>

            <div className="bg-white p-10 rounded-2xl shadow-xl border border-gray-100 prose prose-blue max-w-none">
              <div className="whitespace-pre-wrap leading-relaxed text-gray-800">
                {proposal}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  )
}
