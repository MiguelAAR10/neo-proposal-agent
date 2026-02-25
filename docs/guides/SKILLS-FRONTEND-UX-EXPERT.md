# SKILL: Frontend/UX Expert (Next.js + React + Tailwind)

## Perfil del Experto

**Especialización:** Desarrollador frontend senior especializado en:
- Aplicaciones conversacionales y HITL (Human-in-the-Loop)
- Dashboards de datos con visualización compleja
- Experiencias de usuario que balancean autonomía del sistema con control humano
- Animaciones y transiciones suaves
- Responsive design y accesibilidad

**Experiencia requerida:**
- 5+ años con React
- 3+ años con Next.js
- 2+ años con TypeScript strict
- Experiencia con Tailwind CSS
- Conocimiento de UX/UI patterns
- Experiencia con state management (Zustand, Redux)

**Responsabilidades:**
- Diseñar e implementar interfaz de usuario
- Asegurar experiencia fluida y responsiva
- Optimizar performance (Core Web Vitals)
- Implementar accesibilidad (WCAG 2.1)
- Manejar estados complejos
- Crear animaciones y transiciones

---

## Stack Obligatorio

```
Framework & Runtime:
  - Next.js 14+ (App Router)
  - React 18+
  - TypeScript (strict mode)
  - Node.js 20+

Estilos & UI:
  - Tailwind CSS 3.4+
  - Shadcn/ui (componentes base)
  - Framer Motion (animaciones)
  - Lucide React (iconos)

Estado & Data:
  - Zustand (estado global)
  - TanStack Query (React Query) (data fetching)
  - React Hook Form (formularios)
  - Zod (validación)

Utilidades:
  - clsx (class names)
  - date-fns (fechas)
  - axios o fetch (HTTP)

Testing:
  - Jest
  - React Testing Library
  - Playwright (E2E)

Build & Deploy:
  - Vercel (recomendado)
  - ESLint
  - Prettier
```

---

## Estructura de Código Esperada

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout, providers
│   ├── page.tsx                # Pantalla inicial (formulario)
│   ├── search/
│   │   └── page.tsx            # Pantalla de resultados
│   ├── proposal/
│   │   └── page.tsx            # Pantalla de propuesta
│   ├── admin/
│   │   ├── page.tsx            # Dashboard admin
│   │   ├── ingest/page.tsx     # Ingesta de casos
│   │   └── stats/page.tsx      # Estadísticas
│   ├── api/
│   │   └── [...]/              # Route handlers si necesario
│   ├── globals.css
│   └── providers.tsx           # QueryClient, Zustand providers
│
├── components/
│   ├── ui/                     # Shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── textarea.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── toast.tsx
│   │
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   │
│   ├── forms/
│   │   ├── InitialForm.tsx     # Formulario de entrada
│   │   ├── ProfileForm.tsx     # Formulario de perfil
│   │   └── IngestForm.tsx      # Formulario de ingesta
│   │
│   ├── cards/
│   │   ├── CaseCard.tsx        # Tarjeta de caso
│   │   └── ProposalCard.tsx    # Tarjeta de propuesta
│   │
│   ├── chat/
│   │   ├── ChatPanel.tsx       # Panel de chat
│   │   ├── ChatMessage.tsx     # Mensaje individual
│   │   ├── ChatInput.tsx       # Input de chat
│   │   └── ChatSuggestions.tsx # Sugerencias rápidas
│   │
│   ├── proposal/
│   │   ├── ProposalView.tsx    # Visualización propuesta
│   │   ├── ProposalToolbar.tsx # Toolbar de acciones
│   │   └── ProposalVersions.tsx # Selector de versiones
│   │
│   └── common/
│       ├── LoadingSpinner.tsx
│       ├── ErrorBoundary.tsx
│       └── Toast.tsx
│
├── hooks/
│   ├── useAgent.ts             # Lógica de interacción con API
│   ├── useCases.ts             # Query de casos
│   ├── useProposal.ts          # Generación y refinamiento
│   ├── useProfile.ts           # Gestión de perfiles
│   └── useLocalStorage.ts      # Persistencia local
│
├── stores/
│   ├── agentStore.ts           # Zustand: estado global agente
│   ├── uiStore.ts             # Zustand: estado UI
│   └── authStore.ts           # Zustand: autenticación
│
├── types/
│   ├── index.ts               # Interfaces TypeScript
│   ├── api.ts                 # Tipos de API
│   └── domain.ts              # Tipos de dominio
│
├── lib/
│   ├── api.ts                 # Cliente HTTP
│   ├── utils.ts               # Utilidades
│   ├── constants.ts           # Constantes
│   └── validators.ts          # Validadores Zod
│
├── public/
│   ├── images/
│   ├── icons/
│   └── logo.svg
│
├── styles/
│   └── globals.css
│
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

---

## Patrones de Implementación Clave

### 1. Zustand Store para Estado Global

```typescript
// stores/agentStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AgentState {
  // Datos de entrada
  threadId: string | null
  formData: {
    empresa: string
    rubro: string
    area: string
    problema: string
    switch: 'neo' | 'ai' | 'both'
  } | null
  
  // Búsqueda
  cases: Case[]
  selectedCaseIds: string[]
  
  // Propuesta
  proposal: Proposal | null
  proposalVersion: number
  chatHistory: ChatMessage[]
  
  // UI
  phase: 'idle' | 'searching' | 'curating' | 'generating' | 'complete'
  loading: boolean
  error: string | null
  
  // Acciones
  setThreadId: (id: string) => void
  setFormData: (data: AgentState['formData']) => void
  setCases: (cases: Case[]) => void
  selectCase: (id: string) => void
  unselectCase: (id: string) => void
  setProposal: (proposal: Proposal) => void
  addChatMessage: (message: ChatMessage) => void
  setPhase: (phase: AgentState['phase']) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

export const useAgentStore = create<AgentState>()(
  persist(
    (set, get) => ({
      threadId: null,
      formData: null,
      cases: [],
      selectedCaseIds: [],
      proposal: null,
      proposalVersion: 1,
      chatHistory: [],
      phase: 'idle',
      loading: false,
      error: null,
      
      setThreadId: (id) => set({ threadId: id }),
      setFormData: (data) => set({ formData: data }),
      setCases: (cases) => set({ cases }),
      
      selectCase: (id) => set((state) => ({
        selectedCaseIds: [...state.selectedCaseIds, id]
      })),
      
      unselectCase: (id) => set((state) => ({
        selectedCaseIds: state.selectedCaseIds.filter((cid) => cid !== id)
      })),
      
      setProposal: (proposal) => set({
        proposal,
        phase: 'complete'
      }),
      
      addChatMessage: (message) => set((state) => ({
        chatHistory: [...state.chatHistory, message]
      })),
      
      setPhase: (phase) => set({ phase }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      
      reset: () => set({
        threadId: null,
        formData: null,
        cases: [],
        selectedCaseIds: [],
        proposal: null,
        proposalVersion: 1,
        chatHistory: [],
        phase: 'idle',
        loading: false,
        error: null,
      }),
    }),
    {
      name: 'neo-agent-storage',
      partialize: (state) => ({
        threadId: state.threadId,
        formData: state.formData,
        cases: state.cases,
        selectedCaseIds: state.selectedCaseIds,
        proposal: state.proposal,
        chatHistory: state.chatHistory,
      }),
    }
  )
)
```

### 2. TanStack Query para Data Fetching

```typescript
// hooks/useCases.ts
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

export function useSearchCases() {
  return useMutation({
    mutationFn: async (data: SearchRequest) => {
      const response = await apiClient.post('/agent/search', data)
      return response.data.data as Case[]
    },
    onSuccess: (cases) => {
      useAgentStore.setState({ cases })
    },
    onError: (error) => {
      useAgentStore.setState({ error: error.message })
    },
  })
}

export function useGenerateProposal() {
  return useMutation({
    mutationFn: async ({ threadId, caseIds }: GenerateRequest) => {
      const response = await apiClient.post(
        `/agent/${threadId}/select`,
        { case_ids: caseIds }
      )
      return response.data.data as Proposal
    },
    onSuccess: (proposal) => {
      useAgentStore.setState({ proposal, phase: 'complete' })
    },
  })
}

export function useRefineProposal() {
  return useMutation({
    mutationFn: async ({
      threadId,
      message,
    }: RefineRequest) => {
      const response = await apiClient.post(
        `/agent/${threadId}/refine`,
        { message }
      )
      return response.data.data as Proposal
    },
  })
}
```

### 3. Componente de Tarjeta con Selección

```typescript
// components/cards/CaseCard.tsx
'use client'

import { motion } from 'framer-motion'
import { Checkbox } from '@/components/ui/checkbox'
import { useAgentStore } from '@/stores/agentStore'
import { ExternalLink } from 'lucide-react'

interface CaseCardProps {
  caseData: Case
}

export function CaseCard({ caseData }: CaseCardProps) {
  const { selectedCaseIds, selectCase, unselectCase } = useAgentStore()
  const isSelected = selectedCaseIds.includes(caseData.id)
  
  const handleToggle = (checked: boolean) => {
    if (checked) {
      selectCase(caseData.id)
    } else {
      unselectCase(caseData.id)
    }
  }
  
  return (
    <motion.div
      layout
      animate={{ scale: isSelected ? 1.02 : 1 }}
      className={`
        rounded-lg border-2 p-4 transition-all duration-200
        ${isSelected 
          ? 'border-blue-500 bg-blue-50 shadow-lg' 
          : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
        }
      `}
    >
      <div className="flex justify-between items-start gap-3">
        <div className="flex-1">
          <h3 className="font-semibold text-lg text-gray-900">
            {caseData.titulo}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {caseData.empresa} • {caseData.area}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Score: {(caseData.score * 100).toFixed(0)}% relevancia
          </p>
        </div>
        
        <Checkbox
          checked={isSelected}
          onCheckedChange={handleToggle}
          className="mt-1"
        />
      </div>
      
      <div className="mt-3 space-y-2">
        <div>
          <span className="text-xs font-medium text-gray-500">Problema:</span>
          <p className="text-sm text-gray-700 line-clamp-2">
            {caseData.problema}
          </p>
        </div>
        <div>
          <span className="text-xs font-medium text-gray-500">Solución:</span>
          <p className="text-sm text-gray-700 line-clamp-2">
            {caseData.solucion}
          </p>
        </div>
      </div>
      
      <div className="mt-3 flex flex-wrap gap-1">
        {caseData.tecnologias.slice(0, 3).map((tech) => (
          <span 
            key={tech}
            className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full"
          >
            {tech}
          </span>
        ))}
        {caseData.tecnologias.length > 3 && (
          <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
            +{caseData.tecnologias.length - 3}
          </span>
        )}
      </div>
      
      <a 
        href={caseData.url_slide}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-3 inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 hover:underline"
      >
        Ver slide original
        <ExternalLink className="w-4 h-4" />
      </a>
    </motion.div>
  )
}
```

### 4. Layout Dividido (Desktop)

```typescript
// app/search/page.tsx
'use client'

import { useAgentStore } from '@/stores/agentStore'
import { CaseCard } from '@/components/cards/CaseCard'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { motion } from 'framer-motion'

export default function SearchPage() {
  const { cases, selectedCaseIds } = useAgentStore()
  
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">
          Casos Encontrados
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          {cases.length} casos relevantes • {selectedCaseIds.length} seleccionados
        </p>
      </header>
      
      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Panel Izquierdo: Tarjetas */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cases.map((caseData, index) => (
              <motion.div
                key={caseData.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <CaseCard caseData={caseData} />
              </motion.div>
            ))}
          </div>
          
          {cases.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500">No se encontraron casos</p>
            </div>
          )}
        </main>
        
        {/* Panel Derecho: Chat */}
        <aside className="w-96 border-l bg-white flex flex-col">
          <ChatPanel />
        </aside>
      </div>
    </div>
  )
}
```

### 5. Formulario con React Hook Form

```typescript
// components/forms/InitialForm.tsx
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAgentStore } from '@/stores/agentStore'
import { useSearchCases } from '@/hooks/useCases'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'

const formSchema = z.object({
  empresa: z.string().min(1, 'Empresa requerida').max(100),
  rubro: z.string().min(1, 'Rubro requerido'),
  area: z.string().min(1, 'Área requerida'),
  problema: z.string().min(20, 'Mínimo 20 caracteres').max(2000),
  switch: z.enum(['neo', 'ai', 'both']).default('both'),
})

type FormData = z.infer<typeof formSchema>

export function InitialForm() {
  const { setFormData, setPhase } = useAgentStore()
  const { mutate: searchCases, isPending } = useSearchCases()
  
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      switch: 'both',
    },
  })
  
  const onSubmit = async (data: FormData) => {
    setFormData(data)
    setPhase('searching')
    
    searchCases({
      problema: data.problema,
      switch: data.switch,
    })
  }
  
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Switch */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          ¿Qué tipo de casos buscas?
        </label>
        <select
          {...register('switch')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
        >
          <option value="neo">Solo casos NEO</option>
          <option value="ai">Solo benchmarks AI</option>
          <option value="both">Ambos (recomendado)</option>
        </select>
      </div>
      
      {/* Empresa */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Empresa cliente
        </label>
        <Input
          {...register('empresa')}
          placeholder="TechCorp"
          list="empresas"
        />
        {errors.empresa && (
          <p className="text-red-500 text-sm mt-1">{errors.empresa.message}</p>
        )}
      </div>
      
      {/* Rubro */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Industria/Rubro
        </label>
        <Select {...register('rubro')}>
          <option value="">Seleccionar...</option>
          <option value="Banca">Banca</option>
          <option value="Retail">Retail</option>
          <option value="Tecnología">Tecnología</option>
          <option value="Salud">Salud</option>
          <option value="Manufactura">Manufactura</option>
        </Select>
        {errors.rubro && (
          <p className="text-red-500 text-sm mt-1">{errors.rubro.message}</p>
        )}
      </div>
      
      {/* Área */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Área de la empresa
        </label>
        <Select {...register('area')}>
          <option value="">Seleccionar...</option>
          <option value="Marketing">Marketing</option>
          <option value="Operaciones">Operaciones</option>
          <option value="TI">TI</option>
          <option value="Ventas">Ventas</option>
          <option value="RRHH">RRHH</option>
        </select>
        {errors.area && (
          <p className="text-red-500 text-sm mt-1">{errors.area.message}</p>
        )}
      </div>
      
      {/* Problema */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Describe el problema
        </label>
        <Textarea
          {...register('problema')}
          placeholder="Necesitamos reducir el tiempo de elaboración de reportes..."
          rows={4}
        />
        {errors.problema && (
          <p className="text-red-500 text-sm mt-1">{errors.problema.message}</p>
        )}
      </div>
      
      {/* Submit */}
      <Button
        type="submit"
        disabled={isPending}
        className="w-full"
      >
        {isPending ? 'Buscando casos...' : '🔍 Buscar casos'}
      </Button>
    </form>
  )
}
```

### 6. Chat Panel

```typescript
// components/chat/ChatPanel.tsx
'use client'

import { useAgentStore } from '@/stores/agentStore'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { useRefineProposal } from '@/hooks/useProposal'
import { useEffect, useRef } from 'react'

export function ChatPanel() {
  const { chatHistory, selectedCaseIds, proposal } = useAgentStore()
  const { mutate: refineProposal } = useRefineProposal()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [chatHistory])
  
  const handleSendMessage = (message: string) => {
    if (proposal) {
      refineProposal({
        threadId: useAgentStore.getState().threadId!,
        message,
      })
    }
  }
  
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b p-4">
        <h3 className="font-semibold text-gray-900">💬 Asistente NEO</h3>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {chatHistory.length === 0 ? (
          <div className="text-center text-gray-500 text-sm">
            <p>Encontré {selectedCaseIds.length} casos relevantes.</p>
            <p>¿Alguno te parece aplicable?</p>
          </div>
        ) : (
          chatHistory.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Summary */}
      {selectedCaseIds.length > 0 && (
        <div className="border-t p-4 bg-blue-50">
          <p className="text-sm text-gray-700">
            📋 <strong>{selectedCaseIds.length}</strong> casos seleccionados
          </p>
          <Button
            onClick={() => {
              // Generar propuesta
            }}
            className="w-full mt-2"
            disabled={selectedCaseIds.length === 0}
          >
            Generar propuesta →
          </Button>
        </div>
      )}
      
      {/* Input */}
      <ChatInput onSend={handleSendMessage} />
    </div>
  )
}
```

---

## Reglas de Oro del Frontend

### 1. Mobile-First
```typescript
// ✅ BIEN - Mobile first
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  {/* Responsive por defecto */}
</div>
```

### 2. Estados de Loading
```typescript
// ✅ BIEN - Siempre feedback
{isPending ? (
  <LoadingSpinner />
) : error ? (
  <ErrorMessage error={error} />
) : (
  <Content />
)}
```

### 3. Optimistic UI
```typescript
// ✅ BIEN - Actualizar UI antes de confirmación
const handleSelect = (id: string) => {
  selectCase(id)  // Actualizar UI inmediatamente
  mutation.mutate(id)  // Confirmar en servidor
}
```

### 4. Error Boundaries
```typescript
// ✅ BIEN - Capturar errores de React
<ErrorBoundary fallback={<ErrorPage />}>
  <YourComponent />
</ErrorBoundary>
```

### 5. Accesibilidad
```typescript
// ✅ BIEN - ARIA labels, keyboard navigation
<button
  aria-label="Seleccionar caso"
  onClick={handleSelect}
  onKeyDown={(e) => {
    if (e.key === 'Enter') handleSelect()
  }}
>
  Seleccionar
</button>
```

### 6. Performance
```typescript
// ✅ BIEN - Code splitting, lazy loading
const ProposalView = dynamic(() => import('./ProposalView'), {
  loading: () => <LoadingSpinner />,
})
```

---

## Animaciones Clave

```typescript
// Framer Motion variants
const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
  selected: { scale: 1.02, borderColor: '#0066FF' }
}

const pageTransition = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 }
}

const loadingPulse = {
  animate: {
    opacity: [0.5, 1, 0.5],
  },
  transition: {
    duration: 2,
    repeat: Infinity,
  }
}
```

---

## Testing

```bash
# Unit tests
npm test

# E2E tests
npx playwright test

# Coverage
npm test -- --coverage

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

---

## Performance Checklist

- [ ] Lazy loading de componentes pesados
- [ ] Code splitting por ruta
- [ ] Optimización de imágenes
- [ ] Memoización de componentes costosos
- [ ] Debouncing en inputs
- [ ] Virtual scrolling para listas largas
- [ ] Caching de queries
- [ ] Preloading de recursos críticos
- [ ] Minificación de CSS/JS
- [ ] Core Web Vitals > 90

---

## Deployment Checklist

- [ ] Variables de entorno configuradas
- [ ] Build optimizado
- [ ] Sourcemaps deshabilitados en prod
- [ ] Analytics configurado
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] SEO optimizado
- [ ] Robots.txt y sitemap
- [ ] SSL/HTTPS
- [ ] CDN configurado