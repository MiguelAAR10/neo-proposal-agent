'use client'

import { ChevronLeft, ChevronRight, ChevronUp, ChevronDown } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'
import { CasesSidebar } from '@/components/workspace/CasesSidebar'
import { SectorContextPanel } from '@/components/workspace/SectorContextPanel'
import { ClientProfileInline } from '@/components/workspace/ClientProfileInline'
import { ChatPanel } from '@/components/chat/ChatPanel'

interface ActiveWorkspaceProps {
  onNavigateToInsights: () => void
}

export function ActiveWorkspace({ onNavigateToInsights }: ActiveWorkspaceProps) {
  const { sidebarCollapsed, topPanelsCollapsed, toggleSidebar, toggleTopPanels } = useAppStore()

  return (
    <div className={`neo-v4-workspace ${sidebarCollapsed ? 'neo-v4-workspace--sidebar-collapsed' : ''}`}>
      {/* Left: Cases Sidebar */}
      <div className={`neo-v4-workspace__sidebar ${sidebarCollapsed ? 'neo-v4-workspace__sidebar--collapsed' : ''}`}>
        {!sidebarCollapsed && <CasesSidebar />}
        <button
          type="button"
          onClick={toggleSidebar}
          className="neo-v4-workspace__collapse-btn neo-v4-workspace__collapse-btn--sidebar"
          title={sidebarCollapsed ? 'Expandir casos' : 'Colapsar casos'}
        >
          {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Right Area */}
      <div className="neo-v4-workspace__main">
        {/* Top split: Sector Context + Client Profile */}
        <div className={`neo-v4-workspace__top-split ${topPanelsCollapsed ? 'neo-v4-workspace__top-split--collapsed' : ''}`}>
          {!topPanelsCollapsed && (
            <>
              <div className="neo-v4-workspace__sector">
                <SectorContextPanel />
              </div>
              <div className="neo-v4-workspace__profile">
                <ClientProfileInline onNavigateToInsights={onNavigateToInsights} />
              </div>
            </>
          )}
          <button
            type="button"
            onClick={toggleTopPanels}
            className="neo-v4-workspace__collapse-btn neo-v4-workspace__collapse-btn--top"
            title={topPanelsCollapsed ? 'Expandir contexto' : 'Colapsar contexto'}
          >
            {topPanelsCollapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
            <span className="neo-v4-workspace__collapse-label">
              {topPanelsCollapsed ? 'Mostrar contexto' : 'Ocultar'}
            </span>
          </button>
        </div>

        {/* Bottom: Chat Panel */}
        <div className={`neo-v4-workspace__chat ${topPanelsCollapsed ? 'neo-v4-workspace__chat--expanded' : ''}`}>
          <ChatPanel />
        </div>
      </div>
    </div>
  )
}
