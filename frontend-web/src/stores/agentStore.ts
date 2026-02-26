import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Case {
  id: string
  titulo: string
  empresa: string
  area: string
  problema: string
  solucion: string
  beneficios?: string
  tecnologias: string[]
  url_slide?: string
  score: number
  tipo: 'AI' | 'NEO'
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
  selectedCaseIds: string[]
  perfilCliente: any | null
  proposal: string | null
  
  // UI
  loading: boolean
  error: string | null
  
  // Actions
  setSession: (data: { threadId: string, empresa: string, area: string, problema: string, cases: Case[], perfil: any }) => void
  selectCase: (id: string) => void
  unselectCase: (id: string) => void
  setProposal: (proposal: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
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
      selectedCaseIds: [],
      perfilCliente: null,
      proposal: null,
      loading: false,
      error: null,

      setSession: (data) => set({
        threadId: data.threadId,
        empresa: data.empresa,
        area: data.area,
        problema: data.problema,
        cases: data.cases,
        perfilCliente: data.perfil,
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

      reset: () => set({
        threadId: null,
        phase: 'idle',
        empresa: '',
        rubro: '',
        area: '',
        problema: '',
        switch: 'both',
        cases: [],
        selectedCaseIds: [],
        perfilCliente: null,
        proposal: null,
        loading: false,
        error: null,
      }),
    }),
    {
      name: 'neo-proposal-storage',
    }
  )
)
