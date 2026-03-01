'use client'

import { useEffect, useMemo, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useAgentStore } from '@/stores/agentStore'
import { apiClient } from '@/lib/api'
import { getErrorMessage } from '@/lib/error'
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

interface PrioritizedClientCatalogEntry {
  name: string
  display_name: string
  vertical: string
}

interface InitialFormProps {
  compact?: boolean
}

export function InitialForm({ compact = false }: InitialFormProps) {
  const { setSession, setLoading, setError } = useAgentStore()
  const [catalog, setCatalog] = useState<PrioritizedClientCatalogEntry[]>([])
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [catalogLoading, setCatalogLoading] = useState(true)

  const { register, handleSubmit, control, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      switch: 'both',
    },
  })

  const empresaValue = useWatch({ control, name: 'empresa', defaultValue: '' })
  const problemaValue = useWatch({ control, name: 'problema', defaultValue: '' })

  useEffect(() => {
    let cancelled = false
    async function loadCatalog() {
      setCatalogLoading(true)
      try {
        const response = await apiClient.get('/api/prioritized-clients')
        const entries = Array.isArray(response.data?.catalog)
          ? (response.data.catalog as PrioritizedClientCatalogEntry[])
          : []
        if (!cancelled) {
          setCatalog(entries)
          setCatalogError(null)
          if (entries.length > 0 && !empresaValue) {
            setValue('empresa', entries[0].name, { shouldValidate: true })
            setValue('rubro', entries[0].vertical, { shouldValidate: true })
          }
        }
      } catch (error: unknown) {
        if (!cancelled) {
          setCatalogError(getErrorMessage(error, 'No se pudo cargar el catálogo de clientes priorizados.'))
        }
      } finally {
        if (!cancelled) setCatalogLoading(false)
      }
    }
    loadCatalog()
    return () => {
      cancelled = true
    }
  }, [setValue, empresaValue])

  useEffect(() => {
    if (!empresaValue || catalog.length === 0) return
    const found = catalog.find((item) => item.name === empresaValue || item.display_name === empresaValue)
    if (found?.vertical) {
      setValue('empresa', found.name, { shouldValidate: true })
      setValue('rubro', found.vertical, { shouldValidate: true })
    }
  }, [empresaValue, catalog, setValue])

  const areaOptions = useMemo(
    () => ['Operaciones', 'Marketing', 'TI', 'Finanzas', 'Ventas', 'RRHH', 'Innovación'],
    [],
  )

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
        perfil: data.perfil_cliente,
        profileStatus: data.profile_status ?? null,
        inteligenciaSector: data.inteligencia_sector ?? null,
      })
      setError(null)
      setLoading(false)
    },
    onError: (error: unknown) => {
      setError(getErrorMessage(error, 'Error al iniciar el agente'))
      setLoading(false)
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  if (compact) {
    return (
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="neo-glass-card p-4 md:p-5 space-y-3"
        aria-label="Formulario compacto de búsqueda"
      >
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
          <div className="md:col-span-3">
            <label htmlFor="empresa" className="block text-[11px] font-semibold text-slate-200 mb-1">Empresa priorizada</label>
            <select
              id="empresa"
              {...register('empresa')}
              disabled={catalogLoading}
              className="w-full rounded-xl border border-white/15 bg-white/10 text-[var(--foreground)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
            >
              <option value="">Selecciona empresa...</option>
              {catalog.map((entry) => (
                <option key={entry.name} value={entry.name}>{entry.display_name}</option>
              ))}
            </select>
            {catalogLoading && <p className="mt-1 text-xs text-slate-300">Cargando empresas priorizadas...</p>}
            {errors.empresa && <p className="mt-1 text-xs text-rose-300">{errors.empresa.message}</p>}
          </div>

          <div className="md:col-span-2">
            <label htmlFor="rubro" className="block text-[11px] font-semibold text-slate-200 mb-1">Industria</label>
            <input
              id="rubro"
              {...register('rubro')}
              readOnly
              className="w-full rounded-xl border border-white/10 bg-white/5 text-slate-100 px-3 py-2 text-sm outline-none"
            />
            {errors.rubro && <p className="mt-1 text-xs text-rose-300">{errors.rubro.message}</p>}
          </div>

          <div className="md:col-span-2">
            <label htmlFor="area" className="block text-[11px] font-semibold text-slate-200 mb-1">Área</label>
            <select
              id="area"
              {...register('area')}
              className="w-full rounded-xl border border-white/15 bg-white/10 text-[var(--foreground)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
            >
              <option value="">Selecciona...</option>
              {areaOptions.map((area) => (
                <option key={area} value={area}>{area}</option>
              ))}
            </select>
            {errors.area && <p className="mt-1 text-xs text-rose-300">{errors.area.message}</p>}
          </div>

          <div className="md:col-span-3">
            <label htmlFor="switch" className="block text-[11px] font-semibold text-slate-200 mb-1">Fuente</label>
            <select
              id="switch"
              {...register('switch')}
              className="w-full rounded-xl border border-white/15 bg-white/10 text-[var(--foreground)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
            >
              <option value="both">Ambos</option>
              <option value="neo">Solo NEO</option>
              <option value="ai">Solo AI</option>
            </select>
          </div>

          <div className="md:col-span-2 flex items-end">
            <button
              type="submit"
              disabled={mutation.isPending || catalogLoading || catalog.length === 0}
              className="neo-pill w-full h-[38px] flex items-center justify-center text-sm font-semibold text-white bg-[var(--accent-soft)] hover:brightness-110 disabled:opacity-50"
            >
              {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Search className="h-4 w-4 mr-1.5" /> Buscar</>}
            </button>
          </div>
        </div>

        <div>
          <div className="mb-1 flex items-center justify-between">
            <label htmlFor="problema" className="block text-[11px] font-semibold text-slate-200">Problema de negocio</label>
            <span className="text-[11px] text-slate-300">{problemaValue.trim().length}/500</span>
          </div>
          <textarea
            id="problema"
            {...register('problema')}
            rows={2}
            maxLength={500}
            placeholder="Describe el dolor, impacto y urgencia..."
            className="w-full rounded-xl border border-white/15 bg-white/10 text-[var(--foreground)] placeholder:text-slate-300/70 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
          />
          {errors.problema && <p className="mt-1 text-xs text-rose-300">{errors.problema.message}</p>}
        </div>
        {catalogError && <p className="text-xs text-amber-200">{catalogError}</p>}
      </form>
    )
  }

  return (
    <div className="neo-glass-card p-6 text-sm text-slate-200">
      Usa el modo compacto para la pantalla única.
    </div>
  )
}
