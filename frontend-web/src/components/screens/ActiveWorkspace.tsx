'use client'

import { CasesSidebar } from '@/components/workspace/CasesSidebar'
import { SectorContextPanel } from '@/components/workspace/SectorContextPanel'
import { ClientProfileInline } from '@/components/workspace/ClientProfileInline'
import { ChatPanel } from '@/components/chat/ChatPanel'

interface ActiveWorkspaceProps {
  onNavigateToInsights: () => void
}

export function ActiveWorkspace({ onNavigateToInsights }: ActiveWorkspaceProps) {
  return (
    <div className="neo-v4-workspace">
      {/* Left: Cases Sidebar (360px) */}
      <div className="neo-v4-workspace__sidebar">
        <CasesSidebar />
      </div>

      {/* Right Area (flex: 1) */}
      <div className="neo-v4-workspace__main">
        {/* Top split: Sector Context + Client Profile */}
        <div className="neo-v4-workspace__top-split">
          <div className="neo-v4-workspace__sector">
            <SectorContextPanel />
          </div>
          <div className="neo-v4-workspace__profile">
            <ClientProfileInline onNavigateToInsights={onNavigateToInsights} />
          </div>
        </div>

        {/* Bottom: Chat Panel */}
        <div className="neo-v4-workspace__chat">
          <ChatPanel />
        </div>
      </div>
    </div>
  )
}
