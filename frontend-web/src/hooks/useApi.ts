'use client'

import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { getErrorMessage } from '@/lib/error'
import { useAppStore } from '@/stores/appStore'
import type { Client, UseCase, Insight, InsightType } from '@/stores/appStore'

// ── Catalog query ──────────────────────────────────────────────────────────

const FALLBACK_CATALOG: Client[] = [
  { name: 'BCP', display_name: 'BCP', vertical: 'Banca' },
  { name: 'INTERBANK', display_name: 'Interbank', vertical: 'Banca' },
  { name: 'BBVA', display_name: 'BBVA', vertical: 'Banca' },
  { name: 'ALICORP', display_name: 'Alicorp', vertical: 'Consumo masivo' },
  { name: 'RIMAC', display_name: 'Rimac', vertical: 'Seguros' },
  { name: 'PACIFICO', display_name: 'Pacifico', vertical: 'Seguros' },
  { name: 'SCOTIABANK', display_name: 'Scotiabank', vertical: 'Banca' },
  { name: 'MIBANCO', display_name: 'MiBanco', vertical: 'Microfinanzas' },
  { name: 'CREDICORP', display_name: 'Credicorp', vertical: 'Servicios financieros' },
  { name: 'PLAZA VEA', display_name: 'Plaza Vea', vertical: 'Retail' },
  { name: 'FALABELLA', display_name: 'Falabella', vertical: 'Retail' },
  { name: 'SODIMAC', display_name: 'Sodimac', vertical: 'Retail' },
]

export function usePrioritizedClients() {
  return useQuery({
    queryKey: ['prioritized-clients'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/prioritized-clients')
        const raw = Array.isArray(response.data?.catalog) ? (response.data.catalog as Client[]) : []
        return raw.length > 0 ? raw : FALLBACK_CATALOG
      } catch {
        // Keep discovery usable even if catalog API is temporarily unavailable.
        return FALLBACK_CATALOG
      }
    },
    staleTime: 1000 * 60 * 10,
  })
}

export { FALLBACK_CATALOG }

// ── Client Profile query ───────────────────────────────────────────────────

export function useClientProfile(companyId: string | null, area?: string) {
  return useQuery({
    queryKey: ['client-profile', companyId, area],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (area) params.set('area', area)
      const response = await apiClient.get(`/intel/company/${companyId}/profile?${params.toString()}`)
      return response.data
    },
    enabled: !!companyId,
    staleTime: 30_000,
    retry: 1,
  })
}

// ── Platform metrics ───────────────────────────────────────────────────────

export function usePlatformMetrics() {
  return useQuery({
    queryKey: ['platform-metrics'],
    queryFn: async () => {
      const [metricsRes, funnelRes] = await Promise.all([
        apiClient.get('/ops/metrics', {
          headers: { Authorization: `Bearer ${process.env.NEXT_PUBLIC_ADMIN_TOKEN ?? 'neo-admin'}` }
        }).catch(() => null),
        apiClient.get('/ops/funnel', {
          headers: { Authorization: `Bearer ${process.env.NEXT_PUBLIC_ADMIN_TOKEN ?? 'neo-admin'}` }
        }).catch(() => null),
      ])
      return {
        metrics: metricsRes?.data ?? null,
        funnel: funnelRes?.data ?? null,
      }
    },
    staleTime: 60_000,
  })
}

// ── Search mutation (agent/start) ──────────────────────────────────────────

function mapCase(raw: Record<string, unknown>): UseCase {
  const id = String(raw.id ?? raw.case_id ?? '')
  return {
    id,
    case_id: raw.case_id ? String(raw.case_id) : undefined,
    titulo: String(raw.titulo ?? 'Caso sin titulo'),
    empresa: String(raw.empresa ?? 'N/A'),
    industria: raw.industria ? String(raw.industria) : undefined,
    area: String(raw.area ?? 'N/A'),
    problema: String(raw.problema ?? 'Sin detalle'),
    solucion: String(raw.solucion ?? 'Sin detalle'),
    beneficios: Array.isArray(raw.beneficios)
      ? (raw.beneficios as string[])
      : raw.beneficios ? String(raw.beneficios) : undefined,
    kpi_impacto: raw.kpi_impacto ? String(raw.kpi_impacto) : undefined,
    stack: Array.isArray(raw.stack) ? (raw.stack as string[]) : undefined,
    tecnologias: Array.isArray(raw.tecnologias)
      ? (raw.tecnologias as string[]).map(String)
      : [],
    url_slide: raw.url_slide ? String(raw.url_slide) : undefined,
    score: Number(raw.score ?? raw.score_raw ?? 0),
    score_client_fit: raw.score_client_fit ? Number(raw.score_client_fit) : undefined,
    match_type: raw.match_type ? String(raw.match_type) : undefined,
    match_reason: raw.match_reason ? String(raw.match_reason) : undefined,
    score_raw: raw.score_raw ? Number(raw.score_raw) : undefined,
    badge: raw.badge ? String(raw.badge) : undefined,
    evidence_label: raw.evidence_label ? String(raw.evidence_label) : undefined,
    data_quality_score: raw.data_quality_score ? Number(raw.data_quality_score) : undefined,
    link_status: raw.link_status ? String(raw.link_status) : undefined,
    tipo: String(raw.tipo ?? 'AI').toUpperCase() === 'NEO' ? 'NEO' : 'AI',
    origen: raw.origen ? String(raw.origen) : undefined,
  }
}

export function useSearchCases() {
  const store = useAppStore()

  return useMutation({
    mutationFn: async (params: {
      empresa: string
      rubro: string
      area: string
      problema: string
      switch: string
      use_client_profile?: boolean
    }) => {
      store.setLoading(true)
      const response = await apiClient.post('/agent/start', params)
      return response.data
    },
    onSuccess: (data) => {
      const resetSearchState = () => {
        store.setThreadId(null)
        store.setCases([])
        store.setSectorContext(null)
        store.setSectorTrends([])
      }

      // P0.2: Validate backend response before advancing screen
      const backendError = data.error ? String(data.error).trim() : ''
      if (backendError) {
        resetSearchState()
        store.setError(backendError)
        store.setLoading(false)
        return
      }

      if (!data.thread_id) {
        resetSearchState()
        store.setError('Respuesta del servidor incompleta: falta thread_id.')
        store.setLoading(false)
        return
      }

      const mappedCases = Array.isArray(data.casos_encontrados)
        ? data.casos_encontrados.map((item: Record<string, unknown>) => mapCase(item))
        : []

      if (mappedCases.length === 0) {
        resetSearchState()
        store.setError(
          data.warning
            ? String(data.warning)
            : 'No se encontraron casos relevantes. Intenta reformular el problema.'
        )
        store.setLoading(false)
        return
      }

      store.setSessionFromSearch({
        threadId: String(data.thread_id),
        empresa: String(data.empresa),
        area: String(data.area),
        problema: String(data.problema),
        cases: mappedCases,
        perfil: data.perfil_cliente ?? null,
        profileStatus: data.profile_status ?? null,
        inteligenciaSector: data.inteligencia_sector ?? null,
        humanInsights: Array.isArray(data.human_insights) ? data.human_insights : [],
        warning: data.warning ?? null,
      })
    },
    onError: (error: unknown) => {
      store.setError(getErrorMessage(error, 'No se pudo ejecutar la busqueda.'))
      store.setLoading(false)
    },
  })
}

// ── Generate proposal (agent/{tid}/select) ─────────────────────────────────

export function useGenerateProposal() {
  const store = useAppStore()

  return useMutation({
    mutationFn: async () => {
      if (!store.threadId) throw new Error('No hay sesion activa')
      if (store.selectedCaseIds.length === 0) throw new Error('Selecciona al menos un caso')

      // Extraer mensajes de chat seleccionados como contexto
      const chatContext = store.proposalContext.chatMessageIndices
        .map((idx) => store.chatMessages[idx])
        .filter((msg) => msg && msg.role === 'assistant')
        .map((msg) => msg.content)

      const response = await apiClient.post(`/agent/${store.threadId}/select`, {
        case_ids: store.selectedCaseIds,
        chat_context: chatContext.length > 0 ? chatContext : undefined,
        insight_ids: store.proposalContext.insightIds.length > 0
          ? store.proposalContext.insightIds
          : undefined,
      })
      return response.data
    },
    onSuccess: (data) => {
      const rawText = String(data.propuesta_final ?? '')
      store.setProposalRawText(rawText)
      store.setCurrentProposal({
        problem: rawText,
        solution: '',
        technology: '',
        raw_text: rawText,
      })
      store.setProposalSentSuccess(true)
      // Reset success after 2.5 seconds
      setTimeout(() => store.setProposalSentSuccess(false), 2500)
      store.setActiveScreen(5)
    },
    onError: (error: unknown) => {
      store.setError(getErrorMessage(error, 'No se pudo generar la propuesta.'))
    },
  })
}

// ── Chat mutation ──────────────────────────────────────────────────────────

export function useChatMessage() {
  const store = useAppStore()

  return useMutation({
    mutationFn: async (params: { message: string; mode: 'chat' | 'refinar' }) => {
      if (!store.threadId) throw new Error('No hay sesion activa')
      if (params.mode === 'refinar' && store.proposalRawText) {
        const response = await apiClient.post(`/agent/${store.threadId}/refine`, {
          instruction: params.message,
        })
        return { type: 'refine' as const, data: response.data }
      } else {
        const response = await apiClient.post(`/agent/${store.threadId}/chat`, {
          message: params.message,
        })
        return { type: 'chat' as const, data: response.data }
      }
    },
    onSuccess: (result) => {
      if (result.type === 'refine') {
        const refined = result.data?.propuesta_final
        if (typeof refined === 'string' && refined.trim()) {
          store.setProposalRawText(refined)
          store.addChatMessage({
            role: 'assistant',
            content: refined,
            meta: 'Propuesta refinada',
            isProposal: true,
          })
        }
      } else {
        const answer = result.data?.answer
        if (typeof answer === 'string' && answer.trim()) {
          store.addChatMessage({
            role: 'assistant',
            content: answer,
            meta: result.data?.status === 'guardrail_blocked'
              ? `Guardrail${result.data.guardrail_code ? ` (${result.data.guardrail_code})` : ''}`
              : undefined,
          })
        }
      }
    },
    onError: (error: unknown) => {
      store.addChatMessage({
        role: 'assistant',
        content: getErrorMessage(error, 'Error procesando tu solicitud.'),
      })
    },
  })
}

// ── Radar intelligence ─────────────────────────────────────────────────────

export function useRadarRun() {
  return useMutation({
    mutationFn: async (industryTarget: string) => {
      const response = await apiClient.post('/intel/radar/run', {
        industry_target: industryTarget,
      })
      return response.data
    },
  })
}

// ── Save insight ───────────────────────────────────────────────────────────

export function useSaveInsight() {
  const store = useAppStore()

  return useMutation({
    mutationFn: async (params: {
      companyId: string
      author: string
      text: string
      source: string
    }) => {
      const response = await apiClient.post(`/intel/company/${params.companyId}/insights`, {
        author: params.author,
        text: params.text,
        source: params.source,
      })
      return response.data
    },
    onSuccess: (data, variables) => {
      const newInsight: Insight = {
        id: data.insight_id,
        type: mapDepartmentToInsightType(data.department),
        description: variables.text,
        source: variables.source,
        area: store.activeProfileArea,
        timestamp: data.created_at ?? new Date().toISOString(),
        author: variables.author,
        sentiment: data.sentiment,
      }
      store.addInsight(newInsight)
    },
  })
}

function mapDepartmentToInsightType(department: string): InsightType {
  const map: Record<string, InsightType> = {
    'Operaciones': 'contexto',
    'Marketing': 'objetivo',
    'Comercial': 'pain_point',
    'TI': 'contexto',
    'Finanzas': 'decision',
  }
  return map[department] ?? 'contexto'
}

// ── Teams query ─────────────────────────────────────────────────────────────

export function useTeams(threadId: string | null) {
  return useQuery({
    queryKey: ['teams', threadId],
    queryFn: async () => {
      const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
      const response = await apiClient.get(`/teams${params}`)
      const raw = Array.isArray(response.data) ? response.data : []
      return raw.map((t: Record<string, unknown>): import('@/stores/appStore').Team => ({
        id: String(t.id ?? ''),
        name: String(t.name ?? ''),
        description: String(t.description ?? ''),
        icon: String(t.icon ?? 'brain'),
        specialties: Array.isArray(t.capabilities) ? (t.capabilities as string[]) : [],
        is_best_match: Boolean(t.is_best_match),
      }))
    },
    enabled: !!threadId,
    staleTime: 60_000,
    retry: 1,
  })
}

// ── Assign team mutation ────────────────────────────────────────────────────

export function useAssignTeam() {
  const store = useAppStore()

  return useMutation({
    mutationFn: async (params: { threadId: string; teamId: string; notes?: string }) => {
      const response = await apiClient.post(`/agent/${params.threadId}/assign`, {
        team_id: params.teamId,
        notes: params.notes,
      })
      return response.data
    },
    onSuccess: (data) => {
      const team = store.selectedTeam
      if (team) {
        store.setSelectedTeam({ ...team })
      }
      return data
    },
    onError: (error: unknown) => {
      store.setError(getErrorMessage(error, 'No se pudo asignar el equipo.'))
    },
  })
}

// ── Area options constant ──────────────────────────────────────────────────

export const AREA_OPTIONS = [
  'Operaciones',
  'Marketing',
  'Corporativo',
  'TI',
  'Finanzas',
  'Comercial',
  'Innovacion',
  'Atencion al cliente',
  'Supply Chain',
]
