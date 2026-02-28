'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useAgentStore } from '@/stores/agentStore'
import { apiClient } from '@/lib/api'
import { useMutation } from '@tanstack/react-query'
import { Loader2, Search } from 'lucide-react'

const formSchema = z.object({
  empresa: z.string().min(1, 'La empresa es requerida'),
  rubro: z.string().min(1, 'El rubro es requerido'),
  area: z.string().min(1, 'El área es requerida'),
  problema: z.string().min(20, 'El problema debe tener al menos 20 caracteres'),
  switch: z.enum(['neo', 'ai', 'both']),
})

type FormData = z.infer<typeof formSchema>

export function InitialForm() {
  const { setSession, setLoading, setError } = useAgentStore()

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      switch: 'both',
    }
  })
  const problemaValue = watch('problema', '')

  const mutation = useMutation({
    mutationFn: async (values: FormData) => {
      setLoading(true)
      const response = await apiClient.post('/agent/start', values)
      return response.data
    },
    onSuccess: (data) => {
      setSession({
        threadId: data.thread_id,
        empresa: data.empresa,
        area: data.area,
        problema: data.problema,
        cases: data.casos_encontrados,
        neoCases: data.neo_cases ?? [],
        aiCases: data.ai_cases ?? [],
        topMatchGlobal: data.top_match_global ?? null,
        topMatchGlobalReason: data.top_match_global_reason ?? null,
        perfil: data.perfil_cliente
      })
      setError(null)
      setLoading(false)
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail
      const message =
        (typeof detail === 'object' && detail?.message) ||
        (typeof detail === 'string' && detail) ||
        error?.message ||
        'Error al iniciar el agente'
      setError(message)
      setLoading(false)
    }
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="neo-glass-card space-y-6 max-w-2xl mx-auto p-6 md:p-8 shadow-2xl"
      aria-label="Formulario inicial de propuesta"
    >
      <div className="space-y-2">
        <h2 className="text-3xl font-semibold text-[var(--foreground)]">Iniciar Propuesta</h2>
        <p className="text-slate-200/85 text-sm">Cuéntanos sobre el cliente y el desafío para buscar la mejor solución.</p>
      </div>

      <div className="space-y-4">
        {/* Switch */}
        <div>
          <label htmlFor="switch" className="block text-sm font-medium text-slate-100 mb-1">¿Qué tipo de casos buscas?</label>
          <select 
            id="switch"
            {...register('switch')}
            className="w-full rounded-2xl border border-white/15 bg-white/10 text-[var(--foreground)] px-4 py-2.5 outline-none focus:ring-2 focus:ring-[var(--accent)]"
          >
            <option value="both">Ambos (Recomendado)</option>
            <option value="neo">Solo casos NEO</option>
            <option value="ai">Solo benchmarks AI</option>
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Empresa */}
          <div>
            <label htmlFor="empresa" className="block text-sm font-medium text-slate-100 mb-1">Empresa Cliente</label>
            <input 
              id="empresa"
              {...register('empresa')}
              placeholder="Ej: BCP, Alicorp..."
              autoComplete="organization"
              aria-invalid={Boolean(errors.empresa)}
              aria-describedby={errors.empresa ? 'empresa-error' : undefined}
              className="w-full rounded-2xl border border-white/15 bg-white/10 text-[var(--foreground)] placeholder:text-slate-300/70 px-4 py-2.5 outline-none focus:ring-2 focus:ring-[var(--accent)]"
            />
            {errors.empresa && <p id="empresa-error" className="mt-1 text-xs text-rose-300">{errors.empresa.message}</p>}
          </div>

          {/* Rubro */}
          <div>
            <label htmlFor="rubro" className="block text-sm font-medium text-slate-100 mb-1">Industria/Rubro</label>
            <input 
              id="rubro"
              {...register('rubro')}
              placeholder="Ej: Banca, Retail..."
              autoComplete="organization-title"
              aria-invalid={Boolean(errors.rubro)}
              aria-describedby={errors.rubro ? 'rubro-error' : undefined}
              className="w-full rounded-2xl border border-white/15 bg-white/10 text-[var(--foreground)] placeholder:text-slate-300/70 px-4 py-2.5 outline-none focus:ring-2 focus:ring-[var(--accent)]"
            />
            {errors.rubro && <p id="rubro-error" className="mt-1 text-xs text-rose-300">{errors.rubro.message}</p>}
          </div>
        </div>

        {/* Área */}
        <div>
          <label htmlFor="area" className="block text-sm font-medium text-slate-100 mb-1">Área de la Empresa</label>
          <select 
            id="area"
            {...register('area')}
            aria-invalid={Boolean(errors.area)}
            aria-describedby={errors.area ? 'area-error' : undefined}
            className="w-full rounded-2xl border border-white/15 bg-white/10 text-[var(--foreground)] px-4 py-2.5 outline-none focus:ring-2 focus:ring-[var(--accent)]"
          >
            <option value="">Selecciona un área...</option>
            <option value="Operaciones">Operaciones</option>
            <option value="Marketing">Marketing</option>
            <option value="TI">TI</option>
            <option value="Finanzas">Finanzas</option>
            <option value="Ventas">Ventas</option>
            <option value="RRHH">RRHH</option>
            <option value="Innovación">Innovación</option>
          </select>
          {errors.area && <p id="area-error" className="mt-1 text-xs text-rose-300">{errors.area.message}</p>}
        </div>

        {/* Problema */}
        <div>
          <div className="mb-1 flex items-center justify-between gap-3">
            <label htmlFor="problema" className="block text-sm font-medium text-slate-100">Describe el Problema</label>
            <span className="text-xs text-slate-300">{problemaValue.trim().length}/500</span>
          </div>
          <textarea 
            id="problema"
            {...register('problema')}
            rows={4}
            maxLength={500}
            placeholder="Describe el dolor del cliente y lo que busca resolver..."
            aria-invalid={Boolean(errors.problema)}
            aria-describedby={errors.problema ? 'problema-error' : 'problema-help'}
            className="w-full rounded-2xl border border-white/15 bg-white/10 text-[var(--foreground)] placeholder:text-slate-300/70 px-4 py-2.5 outline-none focus:ring-2 focus:ring-[var(--accent)]"
          />
          <p id="problema-help" className="mt-1 text-xs text-slate-300">Mínimo 20 caracteres. Enfócate en dolor, impacto y urgencia.</p>
          {errors.problema && <p id="problema-error" className="mt-1 text-xs text-rose-300">{errors.problema.message}</p>}
        </div>
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="neo-pill w-full flex items-center justify-center py-3 px-4 border border-transparent text-sm font-medium text-white bg-[var(--accent-soft)] hover:brightness-110 disabled:opacity-50 transition-colors"
      >
        {mutation.isPending ? (
          <>
            <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
            Buscando casos relevantes...
          </>
        ) : (
          <>
            <Search className="-ml-1 mr-2 h-4 w-4" />
            Buscar Casos
          </>
        )}
      </button>
    </form>
  )
}
