import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { api } from '../api/client'
import { PerformanceRecord } from '../types'
import GradeTag from '../components/GradeTag'

export default function PerformancePage() {
  const [records, setRecords] = useState<PerformanceRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.performance.simulate()
      .then((data) => {
        const list = Array.isArray(data) ? data : data.records || data.results || []
        setRecords(list)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const trendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp size={14} className="text-green-400" />
      case 'down': return <TrendingDown size={14} className="text-red-400" />
      default: return <Minus size={14} className="text-gray-400" />
    }
  }

  const chartData = records.slice(0, 15).map((r) => ({
    name: r.name,
    score: r.score,
  }))

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">加载中...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">绩效看板</h1>
        <p className="text-gray-400 text-sm mt-1">Agent 绩效评估与排名</p>
      </div>

      {/* 柱状图 */}
      {chartData.length > 0 && (
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
          <h2 className="text-sm font-medium text-gray-400 mb-4">绩效评分分布</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="name"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                angle={-30}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Bar dataKey="score" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 表格 */}
      <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700 text-gray-400">
              <th className="text-left p-4">排名</th>
              <th className="text-left p-4">名称</th>
              <th className="text-left p-4">评分</th>
              <th className="text-left p-4">等级</th>
              <th className="text-left p-4">趋势</th>
              <th className="text-left p-4">完成任务</th>
            </tr>
          </thead>
          <tbody>
            {records
              .sort((a, b) => b.score - a.score)
              .map((record, idx) => (
                <tr key={record.agent_id} className="border-b border-dark-700 hover:bg-dark-700/50">
                  <td className="p-4 font-medium text-gray-400">#{idx + 1}</td>
                  <td className="p-4 font-medium">{record.name}</td>
                  <td className="p-4">{record.score?.toFixed(1)}</td>
                  <td className="p-4"><GradeTag grade={record.grade} /></td>
                  <td className="p-4">{trendIcon(record.trend)}</td>
                  <td className="p-4 text-gray-400">{record.tasks_completed}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
