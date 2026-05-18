import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  Gavel,
  BarChart3,
  Activity,
  BookOpen,
} from 'lucide-react'

const navItems = [
  { path: '/', label: '总览', icon: LayoutDashboard },
  { path: '/pool', label: '人才池', icon: Users },
  { path: '/tender', label: '招标中心', icon: Gavel },
  { path: '/performance', label: '绩效看板', icon: BarChart3 },
  { path: '/health', label: '健康度', icon: Activity },
  { path: '/values', label: '价值观库', icon: BookOpen },
]

export default function Sidebar() {
  return (
    <aside className="w-60 bg-dark-800 border-r border-dark-700 flex flex-col">
      <div className="p-6 border-b border-dark-700">
        <h1 className="text-xl font-bold text-blue-400">Agent Company</h1>
        <p className="text-xs text-gray-400 mt-1">智能体公司管理面板</p>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-blue-500/10 text-blue-400 font-medium'
                  : 'text-gray-400 hover:text-white hover:bg-dark-700'
              }`
            }
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-dark-700 text-xs text-gray-500">
        v0.2.0 · FastAPI Backend
      </div>
    </aside>
  )
}
