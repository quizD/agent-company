import { useState } from 'react'
import { Gavel, Loader2 } from 'lucide-react'
import { api } from '../api/client'
import { TenderResult } from '../types'
import GradeTag from '../components/GradeTag'

export default function TenderPage() {
  const [taskDesc, setTaskDesc] = useState('')
  const [budget, setBudget] = useState<number>(1000)
  const [strategy, setStrategy] = useState('quality_first')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TenderResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async () => {
    if (!taskDesc.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await api.tender.run({
        task_description: taskDesc,
        budget,
        strategy,
      })
      setResult(data)
    } catch (e: any) {
      setError(e.message || '招标失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">招标中心</h1>
        <p className="text-gray-400 text-sm mt-1">发布任务需求，自动匹配最优 Agent 团队</p>
      </div>

      {/* 输入表单 */}
      <div className="bg-dark-800 rounded-xl p-6 border border-dark-700 space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-2">任务描述</label>
          <textarea
            value={taskDesc}
            onChange={(e) => setTaskDesc(e.target.value)}
            placeholder="描述你的任务需求..."
            className="w-full h-32 bg-dark-700 border border-dark-600 rounded-lg p-3 text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500"
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">预算 (¥)</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">招标策略</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="quality_first">质量优先</option>
              <option value="cost_first">成本优先</option>
              <option value="balanced">均衡策略</option>
              <option value="speed_first">速度优先</option>
            </select>
          </div>
        </div>
        <button
          onClick={handleRun}
          disabled={loading || !taskDesc.trim()}
          className="flex items-center gap-2 px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Gavel size={18} />}
          {loading ? '招标进行中...' : '开始招标'}
        </button>
      </div>

      {/* 错误 */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400">
          {error}
        </div>
      )}

      {/* 结果 */}
      {result && (
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700 space-y-4">
          <h2 className="text-lg font-semibold text-green-400">招标完成</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="p-3 bg-dark-700 rounded-lg">
              <div className="text-xs text-gray-400">策略</div>
              <div className="text-sm font-medium mt-1">{result.strategy_used}</div>
            </div>
            <div className="p-3 bg-dark-700 rounded-lg">
              <div className="text-xs text-gray-400">总成本</div>
              <div className="text-sm font-medium mt-1">¥{result.total_cost?.toFixed(0)}</div>
            </div>
            <div className="p-3 bg-dark-700 rounded-lg">
              <div className="text-xs text-gray-400">预估质量</div>
              <div className="text-sm font-medium mt-1">{result.estimated_quality?.toFixed(1)}分</div>
            </div>
          </div>

          {/* 中标团队 */}
          <div>
            <h3 className="text-sm font-medium text-gray-300 mb-2">中标团队</h3>
            <div className="space-y-2">
              {result.winning_team?.map((member, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <div>
                    <span className="font-medium">{member.name}</span>
                    <span className="text-gray-400 text-sm ml-2">{member.role}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-400">¥{member.bid_amount}</span>
                    <GradeTag grade={member.score >= 90 ? 'S' : member.score >= 80 ? 'A' : 'B'} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
