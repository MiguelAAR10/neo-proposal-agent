'use client'

import { Case, useAgentStore } from '@/stores/agentStore'
import { Check, ExternalLink, Tag, ShieldCheck, AlertTriangle } from 'lucide-react'
import { motion } from 'framer-motion'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface CaseCardProps {
  caseData: Case
}

export function CaseCard({ caseData }: CaseCardProps) {
  const { selectedCaseIds, selectCase, unselectCase } = useAgentStore()
  const isSelected = selectedCaseIds.includes(caseData.id)

  const handleToggle = () => {
    if (isSelected) {
      unselectCase(caseData.id)
    } else {
      selectCase(caseData.id)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, filter: 'blur(6px)', y: 8 }}
      animate={{ opacity: 1, filter: 'blur(0px)', y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      aria-label={`${isSelected ? 'Deseleccionar' : 'Seleccionar'} caso ${caseData.titulo}`}
      className={cn(
        "neo-glass-card relative flex flex-col p-5 border-2 transition-all duration-200 cursor-pointer group focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0b1022]",
        isSelected 
          ? "border-[var(--accent-soft)] shadow-[0_0_0_1px_rgba(108,140,255,0.3),0_14px_26px_rgba(16,25,63,0.45)]" 
          : "border-white/10 hover:border-white/25 hover:shadow-[0_12px_24px_rgba(12,18,46,0.45)]"
      )}
      onClick={handleToggle}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handleToggle()
        }
      }}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={cn(
              "text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider",
              caseData.tipo === 'AI' ? "bg-blue-200/20 text-blue-100" : "bg-emerald-200/20 text-emerald-100"
            )}>
              {caseData.tipo}
            </span>
            <span className="text-xs text-slate-200/85 font-medium">
              {caseData.score_label ?? 'Muy relevante'} ({caseData.confidence ?? `Score: ${Math.round((caseData.score ?? 0) * 100)}%`})
            </span>
            {caseData.badge && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-slate-100 font-semibold">
                {caseData.badge}
              </span>
            )}
          </div>
          <h3 className="font-bold text-[var(--foreground)] leading-tight group-hover:text-[var(--accent)] transition-colors">
            {caseData.titulo}
          </h3>
        </div>
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center border-2 transition-colors",
          isSelected ? "bg-[var(--accent-soft)] border-[var(--accent-soft)] text-white" : "border-white/25 text-transparent"
        )}>
          <Check className="w-4 h-4" strokeWidth={3} />
        </div>
      </div>

      {/* Info */}
      <div className="space-y-3 mb-4 flex-1">
        <div className="text-xs text-slate-300 flex items-center gap-1">
          <span className="font-semibold text-slate-100">{caseData.empresa}</span>
          <span>•</span>
          <span>{caseData.area}</span>
          {caseData.industria && (
            <>
              <span>•</span>
              <span>{caseData.industria}</span>
            </>
          )}
        </div>
        
        <p className="text-sm text-slate-100 line-clamp-3 leading-relaxed">
          {caseData.problema}
        </p>
        <p className="text-xs text-slate-300 line-clamp-2">
          {caseData.solucion}
        </p>

        {caseData.kpi_impacto && caseData.kpi_impacto !== 'No mapeado' && (
          <div className="rounded-lg border border-emerald-200/30 bg-emerald-200/10 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-100">KPI de impacto</p>
            <p className="text-xs text-emerald-50">{caseData.kpi_impacto}</p>
          </div>
        )}
      </div>

      {/* Techs */}
      {caseData.tecnologias && caseData.tecnologias.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {caseData.tecnologias.slice(0, 3).map((tech, index) => (
            <motion.div
              key={tech}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: 0.03 * index }}
              className="flex items-center gap-1 text-[10px] px-2 py-1 bg-white/8 text-slate-200 rounded-md border border-white/10"
            >
              <Tag className="w-2.5 h-2.5" />
              {tech}
            </motion.div>
          ))}
          {caseData.tecnologias.length > 3 && (
            <span className="text-[10px] text-slate-300 font-medium px-1">+{caseData.tecnologias.length - 3}</span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="pt-4 border-t border-white/10 flex justify-between items-center">
        <div className="flex items-center gap-3">
          {caseData.url_slide ? (
            <a 
              href={caseData.url_slide}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Abrir evidencia del caso ${caseData.titulo} en nueva pestaña`}
              onClick={(e) => e.stopPropagation()}
              className="text-xs font-semibold text-[var(--accent)] hover:text-white flex items-center gap-1"
            >
              Ver Presentación
              <ExternalLink className="w-3 h-3" />
            </a>
          ) : (
            <span className="text-[10px] text-amber-200 font-medium">Evidencia no verificable</span>
          )}

          {caseData.link_status === 'verified' && (
            <span className="text-[10px] text-emerald-200 font-semibold flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              Link verificado
            </span>
          )}
          {caseData.link_status === 'inaccessible' && (
            <span className="text-[10px] text-amber-200 font-semibold flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Link no accesible
            </span>
          )}
        </div>
        <div className="text-right">
          <p className="text-[10px] text-slate-300">Completitud</p>
          <p className="text-xs font-bold text-slate-100">
            {Math.round((caseData.data_quality_score ?? 0) * 100)}%
          </p>
        </div>
      </div>
      <div className="mt-3">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            handleToggle()
          }}
          aria-pressed={isSelected}
          aria-label={`${isSelected ? 'Quitar' : 'Agregar'} caso ${caseData.titulo} a la selección`}
          className={cn(
            "w-full rounded-md border px-3 py-2 text-xs font-semibold transition-colors",
            isSelected
              ? "border-[var(--accent)] bg-[rgba(108,140,255,0.16)] text-white"
              : "border-white/20 bg-white/8 text-slate-100 hover:border-white/35"
          )}
        >
          {isSelected ? 'Caso seleccionado' : 'Seleccionar caso'}
        </button>
      </div>
    </motion.div>
  )
}
