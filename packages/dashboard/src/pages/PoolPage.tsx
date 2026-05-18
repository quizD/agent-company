import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Agent } from '../types'
import AgentCard from '../components/AgentCard'
import GradeTag from '../components/GradeTag'

export default function PoolPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table')

  useEffect(() => {
    api.pool.list()
      .then((data) => {
        const list = Array.isArray(data) ? data : data.agents || []
        setAgents(list)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const categories = ['all', ...new Set(agents.map((a) => a.category))]
  const filtered = filter === 'all' ? agents : agents.filter((a) => a.category === filter)

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">加载中...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">人才池</h1>
          <p className="text-gray-400 text-sm mt-1">共 {agents.length} 位 Agent</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('table')}
            className={`px-3 py-1.5 text-sm rounded-lg ${viewMode === 'table' ? 'bg-blue-500 text-white' : 'bg-dark-700 text-gray-400'}`}
          >
            表格
          </button>
          <button
            onClick={() => setViewMode('card')}
            className={`px-3 py-1.5 text-sm rounded-lg ${viewMode === 'card' ? 'bg-blue-500 text-white' : 'bg-dark-700 text-gray-400'}`}
          >
            卡片
          </button>
        </div>
      </div>

      {/* 筛选 */}
      <div className="flex gap-2 flex-wrap">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              filter === cat
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-dark-800 text-gray-400 border border-dark-700 hover:text-white'
            }`}
          >
            {cat === 'all' ? '全部' : cat}
          </button>
        ))}
      </div>

      {/* 表格视图 */}
      {viewMode === 'table' ? (
        <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700 text-gray-400">
                <th className="text-left p-4">名称</th>
                <th className="text-left p-4">分类</th>
                <th className="text-left p-4">技能</th>
                <th className="text-left p-4">模型等级</th>
                <th className="text-left p-4">绩效</th>
                <th className="text-left p-4">等级</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((agent) => (
                <tr key={agent.id} className="border-b border-dark-700 hover:bg-dark-700/50">
                  <td className="p-4 font-medium">{agent.name}</td>
                  <td className="p-4 text-gray-400">{agent.category}</td>
                  <td className="p-4">
                    <div className="flex gap-1 flex-wrap">
                      {agent.skills.slice(0, 3).map((s) => (
                        <span key={s} className="px-1.5 py-0.5 text-xs bg-dark-700 rounded">
                          {s}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="p-4 text-gray-300">{agent.model_tier}</td>
                  <td className="p-4">{agent.performance_score?.toFixed(1)}</td>
                  <td className="p-4"><GradeTag grade={agent.grade} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  )
}
