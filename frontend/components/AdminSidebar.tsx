import React from 'react'
import { BookIcon, ChartIcon, MailIcon, UsersIcon } from './icons'
import { displayName, initialsOf, roleLabel } from '../lib/auth'

export type AdminTab = 'overview' | 'documents' | 'users' | 'invites'

interface AdminSidebarProps {
  activeTab: AdminTab
  onTabChange: (tab: AdminTab) => void
  user: any
}

const items: { id: AdminTab; label: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'overview', label: 'Overview', icon: ChartIcon },
  { id: 'documents', label: 'Documents', icon: BookIcon },
  { id: 'users', label: 'People', icon: UsersIcon },
  { id: 'invites', label: 'Invitations', icon: MailIcon },
]

/** Vertical navigation on large screens, scrollable tab strip on small ones. */
const AdminSidebar: React.FC<AdminSidebarProps> = ({ activeTab, onTabChange, user }) => {
  return (
    <aside className="shrink-0 border-b border-line bg-surface lg:min-h-[calc(100dvh-var(--header-h))] lg:w-64 lg:border-b-0 lg:border-r">
      <div className="hidden items-center gap-3 border-b border-line p-5 lg:flex">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-soft font-semibold text-brand">{initialsOf(user)}</span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-ink">{displayName(user)}</p>
          <p className="text-xs text-muted">{roleLabel(user?.role)}</p>
        </div>
      </div>

      <nav className="flex gap-1 overflow-x-auto p-2 lg:flex-col lg:p-3" aria-label="Administration sections">
        {items.map((item) => {
          const active = activeTab === item.id
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onTabChange(item.id)}
              aria-current={active ? 'page' : undefined}
              className={`flex shrink-0 items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium transition-colors lg:py-3 ${
                active ? 'bg-brand-soft text-brand' : 'text-ink-soft hover:bg-raised hover:text-ink'
              }`}
            >
              <item.icon className="h-[18px] w-[18px]" />
              {item.label}
            </button>
          )
        })}
      </nav>
    </aside>
  )
}

export default AdminSidebar
