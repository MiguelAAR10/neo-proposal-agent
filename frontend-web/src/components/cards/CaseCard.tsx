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
      whileHover={{ y: -4 }}
      className={cn(
        "relative flex flex-col p-5 rounded-xl border-2 transition-all duration-200 cursor-pointer group bg-white",
        isSelected 
          ? "border-blue-500 bg-blue-50/50 shadow-md" 
          : "border-gray-100 hover:border-gray-200 hover:shadow-sm"
      )}
      onClick={handleToggle}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={cn(
              "text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider",
              caseData.tipo === 'AI' ? "bg-blue-100 text-blue-700" : "bg-emerald-100 text-emerald-700"
            )}>
              {caseData.tipo}
            </span>
            <span className="text-xs text-gray-500 font-medium">
              {caseData.score_label ?? 'Muy relevante'} ({caseData.confidence ?? `Score: ${Math.round((caseData.score ?? 0) * 100)}%`})
            </span>
            {caseData.badge && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-semibold">
                {caseData.badge}
              </span>
            )}
          </div>
          <h3 className="font-bold text-gray-900 leading-tight group-hover:text-blue-600 transition-colors">
            {caseData.titulo}
          </h3>
        </div>
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center border-2 transition-colors",
          isSelected ? "bg-blue-500 border-blue-500 text-white" : "border-gray-200 text-transparent"
        )}>
          <Check className="w-4 h-4" strokeWidth={3} />
        </div>
      </div>

      {/* Info */}
      <div className="space-y-3 mb-4 flex-1">
        <div className="text-xs text-gray-500 flex items-center gap-1">
          <span className="font-semibold text-gray-700">{caseData.empresa}</span>
          <span>•</span>
          <span>{caseData.area}</span>
          {caseData.industria && (
            <>
              <span>•</span>
              <span>{caseData.industria}</span>
            </>
          )}
        </div>
        
        <p className="text-sm text-gray-600 line-clamp-3 leading-relaxed">
          {caseData.problema}
        </p>
        <p className="text-xs text-gray-500 line-clamp-2">
          {caseData.solucion}
        </p>

        {caseData.kpi_impacto && caseData.kpi_impacto !== 'No mapeado' && (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2">
            <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-700">KPI de impacto</p>
            <p className="text-xs text-emerald-800">{caseData.kpi_impacto}</p>
          </div>
        )}
      </div>

      {/* Techs */}
      {caseData.tecnologias && caseData.tecnologias.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {caseData.tecnologias.slice(0, 3).map((tech) => (
            <div key={tech} className="flex items-center gap-1 text-[10px] px-2 py-1 bg-gray-50 text-gray-500 rounded-md border border-gray-100">
              <Tag className="w-2.5 h-2.5" />
              {tech}
            </div>
          ))}
          {caseData.tecnologias.length > 3 && (
            <span className="text-[10px] text-gray-400 font-medium px-1">+{caseData.tecnologias.length - 3}</span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="pt-4 border-t border-gray-50 flex justify-between items-center">
        <div className="flex items-center gap-3">
          {caseData.url_slide ? (
            <a 
              href={caseData.url_slide}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              Ver Presentación
              <ExternalLink className="w-3 h-3" />
            </a>
          ) : (
            <span className="text-[10px] text-amber-600 font-medium">Evidencia no verificable</span>
          )}

          {caseData.link_status === 'verified' && (
            <span className="text-[10px] text-emerald-700 font-semibold flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              Link verificado
            </span>
          )}
          {caseData.link_status === 'inaccessible' && (
            <span className="text-[10px] text-amber-700 font-semibold flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Link no accesible
            </span>
          )}
        </div>
        <div className="text-right">
          <p className="text-[10px] text-gray-400">Completitud</p>
          <p className="text-xs font-bold text-gray-700">
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
          className={cn(
            "w-full rounded-md border px-3 py-2 text-xs font-semibold transition-colors",
            isSelected
              ? "border-blue-300 bg-blue-50 text-blue-700"
              : "border-gray-200 bg-white text-gray-600 hover:border-gray-300"
          )}
        >
          {isSelected ? 'Caso seleccionado' : 'Seleccionar caso'}
        </button>
      </div>
    </motion.div>
  )
}
