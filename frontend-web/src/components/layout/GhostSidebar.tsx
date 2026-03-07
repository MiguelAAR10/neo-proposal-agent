'use client'

import { Search, Folder, MessageSquare, TrendingUp } from 'lucide-react'

export function GhostSidebar() {
  const icons = [
    { icon: Search, label: 'Buscar' },
    { icon: Folder, label: 'Proyectos' },
    { icon: MessageSquare, label: 'Chat' },
    { icon: TrendingUp, label: 'Tendencias' },
  ]

  return (
    <aside className="neo-ghost-sidebar" aria-hidden="true">
      {icons.map((item) => {
        const Icon = item.icon
        return (
          <div key={item.label} className="neo-ghost-sidebar__icon" title={item.label}>
            <Icon size={18} />
          </div>
        )
      })}
    </aside>
  )
}
