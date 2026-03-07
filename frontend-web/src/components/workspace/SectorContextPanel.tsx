'use client'

import { TrendingUp, BookOpen } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'

export function SectorContextPanel() {
  const { sectorContext, sectorTrends, selectedClient } = useAppStore()

  return (
    <div className="neo-sector-panel">
      <div className="neo-sector-panel__header">
        <BookOpen size={14} />
        <h3 className="neo-sector-panel__title">Contexto Sectorial</h3>
      </div>
      <div className="neo-sector-panel__body">
        {sectorContext ? (
          <>
            <p className="neo-sector-panel__narrative">{sectorContext}</p>
            {sectorTrends.length > 0 && (
              <div className="neo-sector-panel__trends">
                {sectorTrends.map((trend, i) => (
                  <span key={i} className="neo-trend-chip">
                    <TrendingUp size={11} />
                    {trend}
                  </span>
                ))}
              </div>
            )}
          </>
        ) : (
          <p className="neo-sector-panel__empty">
            {selectedClient
              ? 'Ejecuta una busqueda para ver el contexto sectorial generado por Gemini.'
              : 'Selecciona un cliente para obtener inteligencia sectorial.'}
          </p>
        )}
      </div>
    </div>
  )
}
