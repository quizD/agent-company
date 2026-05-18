import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  color?: string
  subtitle?: string
}

export default function StatCard({ title, value, icon: Icon, color = 'blue', subtitle }: StatCardProps) {
  const colorMap: Record<string, string> = {
    blue: 'text-blue-400 bg-blue-400/10',
    green: 'text-green-400 bg-green-400/10',
    orange: 'text-orange-400 bg-orange-400/10',
    red: 'text-red-400 bg-red-400/10',
    purple: 'text-purple-400 bg-purple-400/10',
  }

  return (
    <div className="bg-dark-800 rounded-xl p-5 border border-dark-700">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-400">{title}</span>
        <div className={`p-2 rounded-lg ${colorMap[color] || colorMap.blue}`}>
          <Icon size={18} />
        </div>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  )
}
