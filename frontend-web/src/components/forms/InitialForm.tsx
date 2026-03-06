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
  logo_path?: string | null
  brand_color?: string | null
}

interface InitialFormProps {
  compact?: boolean
}

const FALLBACK_CATALOG: PrioritizedClientCatalogEntry[] = [
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

export function InitialForm({ compact = false }: InitialFormProps) {
  const { setSession, setLoading, setError } = useAgentStore()
  const [catalog, setCatalog] = useState<PrioritizedClientCatalogEntry[]>(FALLBACK_CATALOG)
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [empresaPreset, setEmpresaPreset] = useState<string>('')

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
          setCatalog(FALLBACK_CATALOG)
          setCatalogError(
            `${getErrorMessage(error, 'No se pudo cargar el catálogo de clientes priorizados.')} Usando catálogo local mínimo.`,
          )
          if (!empresaValue) {
            setValue('empresa', FALLBACK_CATALOG[0].name, { shouldValidate: true })
            setValue('rubro', FALLBACK_CATALOG[0].vertical, { shouldValidate: true })
          }
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
    if (empresaPreset && empresaPreset !== '__OTHER__') {
      const found = catalog.find((item) => item.name === empresaPreset)
      if (found) {
        setValue('empresa', found.name, { shouldValidate: true })
        setValue('rubro', found.vertical, { shouldValidate: true })
      }
      return
    }
    if (!empresaValue || catalog.length === 0) return
    const found = catalog.find((item) => item.name === empresaValue || item.display_name === empresaValue)
    if (found?.vertical) {
      setValue('empresa', found.name, { shouldValidate: true })
      setValue('rubro', found.vertical, { shouldValidate: true })
    }
  }, [empresaPreset, empresaValue, catalog, setValue])

  const areaOptions = useMemo(
    () => ['Operaciones', 'Marketing', 'TI', 'Finanzas', 'Ventas', 'RRHH', 'Innovación'],
    [],
  )
  const selectedEntry = useMemo(
    () => catalog.find((item) => item.name === empresaValue),
    [catalog, empresaValue],
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
        className="neo-glass-card p-3 md:p-3.5 space-y-2.5"
        aria-label="Formulario compacto de búsqueda"
      >
        <div className="grid grid-cols-1 md:grid-cols-12 gap-2">
          <div className="md:col-span-3">
            <div className="flex items-center justify-between mb-0.5">
              <label htmlFor="empresaPreset" className="block text-[11px] font-semibold text-slate-200">Empresa objetivo</label>
              {selectedEntry?.logo_path ? (
                <span
                  className="h-7 w-7 rounded-md border border-white/20 bg-white/10 overflow-hidden flex items-center justify-center"
                  style={{ boxShadow: selectedEntry.brand_color ? `0 0 0 1px ${selectedEntry.brand_color}44 inset` : undefined }}
                >
                  <span className="text-[11px] font-semibold text-slate-100">
                    {selectedEntry.display_name.slice(0, 2).toUpperCase()}
                  </span>
                </span>
              ) : null}
            </div>
            <select
              id="empresaPreset"
              value={empresaPreset}
              onChange={(e) => {
                const value = e.target.value
                setEmpresaPreset(value)
                if (value === '__OTHER__') {
                  setValue('empresa', '', { shouldValidate: true })
                }
              }}
              className="w-full rounded-xl border border-white/15 bg-white/10 text-[var(--foreground)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
            >
              <option value="">Selecciona empresa priorizada...</option>
              {catalog.map((entry) => (
                <option key={entry.name} value={entry.name}>
                  {entry.display_name}
                </option>
              ))}
              <option value="__OTHER__">Otra empresa (manual)</option>
            </select>
            {empresaPreset === '__OTHER__' && (
              <input
                id="empresa"
                {...register('empresa')}
                placeholder="Escribe empresa objetivo..."
                className="mt-2 w-full rounded-xl border border-white/15 bg-white/10 text-[var(--foreground)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
              />
            )}
            {empresaPreset !== '__OTHER__' && <input type="hidden" {...register('empresa')} />}
            {catalogLoading && <p className="mt-1 text-xs text-slate-300">Actualizando catálogo priorizado...</p>}
            {errors.empresa && <p className="mt-1 text-xs text-rose-300">{errors.empresa.message}</p>}
          </div>

          <div className="md:col-span-2">
            <label htmlFor="rubro" className="block text-[11px] font-semibold text-slate-200 mb-0.5">Industria</label>
            <input
              id="rubro"
              {...register('rubro')}
              placeholder="Ej. Banca, Seguros, Retail"
              className="w-full rounded-xl border border-white/15 bg-white/10 text-slate-100 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
            />
            {errors.rubro && <p className="mt-1 text-xs text-rose-300">{errors.rubro.message}</p>}
          </div>

          <div className="md:col-span-2">
            <label htmlFor="area" className="block text-[11px] font-semibold text-slate-200 mb-0.5">Área</label>
            <input
              id="area"
              list="area-suggestions"
              {...register('area')}
              placeholder="Ej. Operaciones, Finanzas, Comercial..."
              className="w-full rounded-xl border border-white/15 bg-white/10 text-[var(--foreground)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
            />
            <datalist id="area-suggestions">
              {areaOptions.map((area) => (
                <option key={area} value={area}>{area}</option>
              ))}
            </datalist>
            {errors.area && <p className="mt-1 text-xs text-rose-300">{errors.area.message}</p>}
          </div>

          <div className="md:col-span-3">
            <label htmlFor="switch" className="block text-[11px] font-semibold text-slate-200 mb-0.5">Fuente</label>
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
              disabled={mutation.isPending}
              className="neo-pill w-full h-[36px] flex items-center justify-center text-sm font-semibold text-white bg-[var(--accent-soft)] hover:brightness-110 disabled:opacity-50"
            >
              {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Search className="h-4 w-4 mr-1.5" /> Buscar</>}
            </button>
          </div>
        </div>

        <div>
          <div className="mb-0.5 flex items-center justify-between">
            <label htmlFor="problema" className="block text-[11px] font-semibold text-slate-200">Problema de negocio</label>
            <span className="text-[11px] text-slate-300">{problemaValue.trim().length}/500</span>
          </div>
          <textarea
            id="problema"
            {...register('problema')}
            rows={1}
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
