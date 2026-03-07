'use client'

import { Search, FolderOpen, MessageCircle, TrendingUp } from 'lucide-react'
import type { ActiveTab } from '@/stores/appStore'

interface AppTabsProps {
  activeTab: ActiveTab
  onTabChange: (tab: ActiveTab) => void
}

const TABS: { id: ActiveTab; label: string; icon: typeof Search }[] = [
  { id: 'descubrimiento', label: 'Descubrimiento', icon: Search },
  { id: 'propuestas', label: 'Propuestas', icon: FolderOpen },
  { id: 'seguimiento', label: 'Seguimiento', icon: MessageCircle },
  { id: 'pipeline', label: 'Pipeline', icon: TrendingUp },
]

export function AppTabs({ activeTab, onTabChange }: AppTabsProps) {
  return (
    <nav className="neo-app-tabs" aria-label="Proceso principal">
      {TABS.map((tab) => {
        const Icon = tab.icon
        const isActive = activeTab === tab.id
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onTabChange(tab.id)}
            className={`neo-app-tab${isActive ? ' neo-app-tab--active' : ''}`}
          >
            <Icon size={14} />
            <span>{tab.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
