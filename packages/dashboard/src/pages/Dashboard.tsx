import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, Gavel, BarChart3, Activity } from 'lucide-react'
import StatCard from '../components/StatCard'
import { api } from '../api/client'
import { PoolStats } from '../types'

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<PoolStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.pool.stats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const quickActions = [
    { label: '查看人才池', path: '/pool', icon: Users, color: 'blue' },
    { label: '发起招标', path: '/tender', icon: Gavel, color: 'green' },
    { label: '绩效评估', path: '/performance', icon: BarChart3, color: 'orange' },
    { label: '健康检查', path: '/health', icon: Activity, color: 'purple' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">控制台总览</h1>
        <p className="text-gray-400 text-sm mt-1">Agent Company 运营状态一览</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Agent 总数"
          value={loading ? '...' : stats?.total_agents ?? 0}
          icon={Users}
          color="blue"
        />
        <StatCard
          title="平均绩效"
          value={loading ? '...' : stats?.average_score?.toFixed(1) ?? '0'}
          icon={BarChart3}
          color="green"
        />
        <StatCard
          title="分类数"
          value={loading ? '...' : Object.keys(stats?.by_category ?? {}).length}
          icon={Activity}
          color="orange"
        />
        <StatCard
          title="S 级人才"
          value={loading ? '...' : stats?.by_grade?.['S'] ?? 0}
          icon={Users}
          color="purple"
          subtitle="最优等级"
        />
      </div>

      {/* 快速操作 */}
      <div>
        <h2 className="text-lg font-semibold mb-3">快速操作</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {quickActions.map((action) => (
            <button
              key={action.path}
              onClick={() => navigate(action.path)}
              className="flex flex-col items-center gap-2 p-4 bg-dark-800 rounded-xl border border-dark-700 hover:border-blue-500/50 transition-colors"
            >
              <action.icon size={24} className="text-blue-400" />
              <span className="text-sm text-gray-300">{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 分类分布 */}
      {stats?.by_category && (
        <div>
          <h2 className="text-lg font-semibold mb-3">人才分布</h2>
          <div className="bg-dark-800 rounded-xl p-5 border border-dark-700">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {Object.entries(stats.by_category).map(([cat, count]) => (
                <div key={cat} className="flex justify-between items-center p-3 bg-dark-700 rounded-lg">
                  <span className="text-sm text-gray-300">{cat}</span>
                  <span className="text-sm font-bold text-blue-400">{count as number}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
