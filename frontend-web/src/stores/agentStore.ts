import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ContextChip } from '@/types/dashboard'

export interface Case {
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
  match_type?: 'exacto' | 'relacionado' | 'inspiracional' | string
  match_reason?: string
  score_raw?: number
  score_label?: string
  confidence?: string
  score_breakdown?: {
    similitud_semantica?: number
    match_industria?: number
    match_area?: number
    confianza_fuente?: number
    recencia?: number
  }
  badge?: string
  evidence_label?: string
  data_quality_score?: number
  link_status?: 'verified' | 'inaccessible' | 'unknown' | string
  semantic_quality?: 'good' | 'basic' | string
  confianza_fuente?: number
  origen?: string
  tipo: 'AI' | 'NEO'
}

export interface PerfilCliente {
  notas?: string
  [key: string]: unknown
}

export interface InteligenciaSector {
  industria?: string
  area?: string
  tendencias?: string[]
  oportunidades?: string[]
  benchmarks?: Record<string, unknown>
  source?: string
}

export interface ProposalState {
  // Session
  threadId: string | null
  phase: 'idle' | 'searching' | 'curating' | 'generating' | 'complete'
  
  // Data
  empresa: string
  rubro: string
  area: string
  problema: string
  switch: 'neo' | 'ai' | 'both'
  
  // Results
  cases: Case[]
  neoCases: Case[]
  aiCases: Case[]
  topMatchGlobal: Case | null
  topMatchGlobalReason: string | null
  selectedCaseIds: string[]
  perfilCliente: PerfilCliente | null
  profileStatus: 'found' | 'not_found' | 'incomplete' | null
  inteligenciaSector: InteligenciaSector | null
  proposal: string | null
  
  // UI
  loading: boolean
  error: string | null
  warning: string | null
  
  // Actions
  setSession: (data: {
    threadId: string
    empresa: string
    area: string
    problema: string
    cases: Case[]
    neoCases?: Case[]
    aiCases?: Case[]
    topMatchGlobal?: Case | null
    topMatchGlobalReason?: string | null
    perfil: PerfilCliente | null
    profileStatus?: 'found' | 'not_found' | 'incomplete' | null
    inteligenciaSector?: InteligenciaSector | null
    warning?: string | null
  }) => void
  selectCase: (id: string) => void
  unselectCase: (id: string) => void
  setProposal: (proposal: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setWarning: (warning: string | null) => void
  contextChips: ContextChip[]
  addContextChip: (chip: ContextChip) => void
  removeContextChip: (id: string) => void
  clearContextChips: () => void
  reset: () => void
}

export const useAgentStore = create<ProposalState>()(
  persist(
    (set) => ({
      threadId: null,
      phase: 'idle',
      empresa: '',
      rubro: '',
      area: '',
      problema: '',
      switch: 'both',
      cases: [],
      neoCases: [],
      aiCases: [],
      topMatchGlobal: null,
      topMatchGlobalReason: null,
      selectedCaseIds: [],
      perfilCliente: null,
      profileStatus: null,
      inteligenciaSector: null,
      proposal: null,
      loading: false,
      error: null,
      warning: null,
      contextChips: [],

      setSession: (data) => set({
        threadId: data.threadId,
        empresa: data.empresa,
        area: data.area,
        problema: data.problema,
        cases: data.cases,
        neoCases: data.neoCases ?? data.cases.filter((c) => c.tipo === 'NEO'),
        aiCases: data.aiCases ?? data.cases.filter((c) => c.tipo === 'AI'),
        topMatchGlobal: data.topMatchGlobal ?? null,
        topMatchGlobalReason: data.topMatchGlobalReason ?? null,
        perfilCliente: data.perfil,
        profileStatus: data.profileStatus ?? null,
        inteligenciaSector: data.inteligenciaSector ?? null,
        warning: data.warning ?? null,
        phase: 'curating'
      }),

      selectCase: (id) => set((state) => ({
        selectedCaseIds: state.selectedCaseIds.includes(id) 
          ? state.selectedCaseIds 
          : [...state.selectedCaseIds, id]
      })),

      unselectCase: (id) => set((state) => ({
        selectedCaseIds: state.selectedCaseIds.filter(cid => cid !== id)
      })),

      setProposal: (proposal) => set({
        proposal,
        phase: 'complete'
      }),

      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      setWarning: (warning) => set({ warning }),
      addContextChip: (chip) => set((state) => ({
        contextChips: state.contextChips.some((c) => c.id === chip.id)
          ? state.contextChips
          : [...state.contextChips, chip],
      })),
      removeContextChip: (id) => set((state) => ({
        contextChips: state.contextChips.filter((c) => c.id !== id),
      })),
      clearContextChips: () => set({ contextChips: [] }),

      reset: () => set({
        threadId: null,
        phase: 'idle',
        empresa: '',
        rubro: '',
        area: '',
        problema: '',
        switch: 'both',
        cases: [],
        neoCases: [],
        aiCases: [],
        topMatchGlobal: null,
        topMatchGlobalReason: null,
        selectedCaseIds: [],
        perfilCliente: null,
        profileStatus: null,
        inteligenciaSector: null,
        proposal: null,
        loading: false,
        error: null,
        warning: null,
        contextChips: [],
      }),
    }),
    {
      name: 'neo-proposal-storage',
    }
  )
)
