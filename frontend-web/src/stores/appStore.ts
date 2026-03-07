import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ── V4 Types ────────────────────────────────────────────────────────────────

export type ActiveTab = 'descubrimiento' | 'propuestas' | 'seguimiento' | 'pipeline'
export type ActiveScreen = 1 | 2 | 3 | 4 | 5 | 6
export type DataSource = 'historico' | 'ai' | 'ambas'
export type ChatMode = 'chat' | 'refinar'
export type InsightType = 'pain_point' | 'objetivo' | 'contexto' | 'decision'

export interface Client {
  name: string
  display_name: string
  vertical: string
  priorities?: string[]
  constraints?: string[]
  logo_file?: string | null
  logo_path?: string | null
  brand_color?: string | null
}

export interface ClientKPIs {
  revenue?: string
  satisfaction?: string
  empleados_ti?: string
  proyectos?: string
}

export interface ClientProfile {
  company_id: string
  area: string
  profile_payload?: Record<string, unknown>
  insights?: Insight[]
  kpis?: ClientKPIs
  alerts?: RadarAlert[]
}

export interface Insight {
  id?: string
  type: InsightType
  description: string
  source: string
  area: string
  timestamp: string
  author?: string
  sentiment?: string
}

export interface RadarAlert {
  trigger_type: string
  title: string
  rationale: string
  severity: 'high' | 'medium' | 'low'
  evidence?: string
}

export interface UseCase {
  id: string
  case_id?: string
  titulo: string
  empresa: string
  industria?: string
  area: string
  problema: string
  solucion: string
  beneficios?: string[] | string
  kpi_impacto?: string
  stack?: string[]
  tecnologias: string[]
  url_slide?: string
  score: number
  score_client_fit?: number
  match_type?: string
  match_reason?: string
  score_raw?: number
  badge?: string
  evidence_label?: string
  data_quality_score?: number
  link_status?: string
  tipo: 'AI' | 'NEO'
  origen?: string
}

export interface Proposal {
  problem: string
  solution: string
  technology: string
  problem_metrics?: string[]
  solution_tags?: string[]
  kpis?: { label: string; value: string }[]
  raw_text?: string
}

export interface Team {
  id: string
  name: string
  description: string
  icon: string
  specialties: string[]
  is_best_match?: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  meta?: string
  isProposal?: boolean
}

// ── Store State ─────────────────────────────────────────────────────────────

interface AppState {
  // Navigation
  activeTab: ActiveTab
  activeScreen: ActiveScreen
  setActiveTab: (tab: ActiveTab) => void
  setActiveScreen: (screen: ActiveScreen) => void

  // Client Selection (Screen 2)
  selectedClient: Client | null
  selectedArea: string | null
  dataSource: DataSource
  problemDescription: string
  setSelectedClient: (client: Client | null) => void
  setSelectedArea: (area: string | null) => void
  setDataSource: (source: DataSource) => void
  setProblemDescription: (desc: string) => void

  // Workspace (Screen 3)
  threadId: string | null
  cases: UseCase[]
  sectorContext: string | null
  sectorTrends: string[]
  clientProfile: ClientProfile | null
  chatMode: ChatMode
  chatMessages: ChatMessage[]
  selectedCaseIds: string[]
  setThreadId: (id: string | null) => void
  setCases: (cases: UseCase[]) => void
  setSectorContext: (context: string | null) => void
  setSectorTrends: (trends: string[]) => void
  setClientProfile: (profile: ClientProfile | null) => void
  setChatMode: (mode: ChatMode) => void
  addChatMessage: (msg: ChatMessage) => void
  clearChatMessages: () => void
  selectCase: (id: string) => void
  unselectCase: (id: string) => void

  // Insights (Screen 4)
  activeProfileArea: string
  insights: Insight[]
  setActiveProfileArea: (area: string) => void
  setInsights: (insights: Insight[]) => void
  addInsight: (insight: Insight) => void

  // Proposal (Screen 5-6)
  currentProposal: Proposal | null
  proposalRawText: string | null
  selectedTeam: Team | null
  setCurrentProposal: (proposal: Proposal | null) => void
  setProposalRawText: (text: string | null) => void
  setSelectedTeam: (team: Team | null) => void

  // UI
  loading: boolean
  error: string | null
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  // Session from agent/start response
  setSessionFromSearch: (data: {
    threadId: string
    empresa: string
    area: string
    problema: string
    cases: UseCase[]
    perfil: Record<string, unknown> | null
    profileStatus: string | null
    inteligenciaSector: Record<string, unknown> | null
    humanInsights: Record<string, unknown>[]
    warning: string | null
  }) => void

  // Reset
  reset: () => void
}

const DEFAULT_CHAT: ChatMessage[] = [
  {
    role: 'assistant',
    content: 'Listo para trabajar. Selecciona casos en el panel izquierdo y genera una propuesta, o preguntame sobre el cliente o la oportunidad.'
  }
]

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Navigation
      activeTab: 'descubrimiento',
      activeScreen: 1,
      setActiveTab: (tab) => set({ activeTab: tab }),
      setActiveScreen: (screen) => set({ activeScreen: screen }),

      // Client Selection
      selectedClient: null,
      selectedArea: null,
      dataSource: 'ambas',
      problemDescription: '',
      setSelectedClient: (client) => set({ selectedClient: client }),
      setSelectedArea: (area) => set({ selectedArea: area }),
      setDataSource: (source) => set({ dataSource: source }),
      setProblemDescription: (desc) => set({ problemDescription: desc }),

      // Workspace
      threadId: null,
      cases: [],
      sectorContext: null,
      sectorTrends: [],
      clientProfile: null,
      chatMode: 'chat',
      chatMessages: DEFAULT_CHAT,
      selectedCaseIds: [],
      setThreadId: (id) => set({ threadId: id }),
      setCases: (cases) => set({ cases }),
      setSectorContext: (context) => set({ sectorContext: context }),
      setSectorTrends: (trends) => set({ sectorTrends: trends }),
      setClientProfile: (profile) => set({ clientProfile: profile }),
      setChatMode: (mode) => set({ chatMode: mode }),
      addChatMessage: (msg) => set((s) => ({ chatMessages: [...s.chatMessages, msg] })),
      clearChatMessages: () => set({ chatMessages: DEFAULT_CHAT }),
      selectCase: (id) => set((s) => ({
        selectedCaseIds: s.selectedCaseIds.includes(id)
          ? s.selectedCaseIds
          : [...s.selectedCaseIds, id]
      })),
      unselectCase: (id) => set((s) => ({
        selectedCaseIds: s.selectedCaseIds.filter((cid) => cid !== id)
      })),

      // Insights
      activeProfileArea: 'Operaciones',
      insights: [],
      setActiveProfileArea: (area) => set({ activeProfileArea: area }),
      setInsights: (insights) => set({ insights }),
      addInsight: (insight) => set((s) => ({ insights: [insight, ...s.insights] })),

      // Proposal
      currentProposal: null,
      proposalRawText: null,
      selectedTeam: null,
      setCurrentProposal: (proposal) => set({ currentProposal: proposal }),
      setProposalRawText: (text) => set({ proposalRawText: text }),
      setSelectedTeam: (team) => set({ selectedTeam: team }),

      // UI
      loading: false,
      error: null,
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),

      // Session from search
      setSessionFromSearch: (data) => {
        const sectorData = data.inteligenciaSector as Record<string, unknown> | null
        const tendencias = Array.isArray(sectorData?.tendencias) ? sectorData.tendencias as string[] : []
        const oportunidades = Array.isArray(sectorData?.oportunidades) ? sectorData.oportunidades as string[] : []

        // Build sector context from executive summary or opportunities
        let sectorText: string | null = null
        if (sectorData) {
          const executive = sectorData.executive_summary as string | undefined
          const industria = sectorData.industria as string | undefined
          if (executive) {
            sectorText = executive
          } else if (oportunidades.length > 0) {
            sectorText = `Industria: ${industria ?? data.empresa}. ${oportunidades.join('. ')}`
          } else if (industria) {
            sectorText = `Industria: ${industria}`
          }
        }

        // Build insights from perfil's pain_points, objetivos, decision_makers AND humanInsights
        const perfil = data.perfil as Record<string, unknown> | null
        const mappedInsights: Insight[] = []

        if (perfil) {
          const painPoints = Array.isArray(perfil.pain_points) ? perfil.pain_points as string[] : []
          const objetivos = Array.isArray(perfil.objetivos) ? perfil.objetivos as string[] : []
          const decisionMakers = Array.isArray(perfil.decision_makers) ? perfil.decision_makers as string[] : []

          painPoints.forEach((pp, idx) => {
            mappedInsights.push({
              id: `pp-${idx}`,
              type: 'pain_point' as InsightType,
              description: pp,
              source: 'profile',
              area: data.area,
              timestamp: new Date().toISOString(),
            })
          })
          objetivos.forEach((obj, idx) => {
            mappedInsights.push({
              id: `obj-${idx}`,
              type: 'objetivo' as InsightType,
              description: obj,
              source: 'profile',
              area: data.area,
              timestamp: new Date().toISOString(),
            })
          })
          decisionMakers.forEach((dm, idx) => {
            mappedInsights.push({
              id: `dm-${idx}`,
              type: 'decision' as InsightType,
              description: dm,
              source: 'profile',
              area: data.area,
              timestamp: new Date().toISOString(),
            })
          })
        }

        // Add human insights as contexto
        if (Array.isArray(data.humanInsights)) {
          data.humanInsights.forEach((hi, idx) => {
            const raw = hi as Record<string, unknown>
            mappedInsights.push({
              id: `hi-${idx}`,
              type: 'contexto' as InsightType,
              description: String(raw.text ?? raw.raw_text ?? ''),
              source: String(raw.source ?? 'agent'),
              area: data.area,
              timestamp: String(raw.created_at ?? new Date().toISOString()),
              author: String(raw.author ?? 'Sistema'),
              sentiment: String(raw.sentiment ?? 'Neutral'),
            })
          })
        }

        // Extract KPIs from perfil
        const kpis = perfil?.kpis as Record<string, string> | undefined

        set({
          threadId: data.threadId,
          cases: data.cases,
          selectedCaseIds: [],
          sectorContext: sectorText,
          sectorTrends: tendencias,
          clientProfile: perfil ? {
            company_id: data.empresa,
            area: data.area,
            profile_payload: perfil as Record<string, unknown>,
            insights: mappedInsights,
            kpis: kpis ? {
              revenue: kpis.revenue,
              satisfaction: kpis.satisfaction,
              empleados_ti: kpis.empleados_ti,
              proyectos: kpis.proyectos,
            } : undefined,
          } : null,
          activeScreen: 3 as ActiveScreen,
          chatMessages: DEFAULT_CHAT,
          chatMode: 'chat' as ChatMode,
          error: null,
          loading: false,
        })
      },

      // Reset
      reset: () => set({
        activeTab: 'descubrimiento',
        activeScreen: 1,
        selectedClient: null,
        selectedArea: null,
        dataSource: 'ambas',
        problemDescription: '',
        threadId: null,
        cases: [],
        sectorContext: null,
        sectorTrends: [],
        clientProfile: null,
        chatMode: 'chat',
        chatMessages: DEFAULT_CHAT,
        selectedCaseIds: [],
        activeProfileArea: 'Operaciones',
        insights: [],
        currentProposal: null,
        proposalRawText: null,
        selectedTeam: null,
        loading: false,
        error: null,
      }),
    }),
    {
      name: 'neo-v4-storage',
    }
  )
)
