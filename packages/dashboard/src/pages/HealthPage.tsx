import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { HealthEvaluation, HealthDimension } from '../types'
import RadarChart from '../components/RadarChart'

export default function HealthPage() {
  const [evaluation, setEvaluation] = useState<HealthEvaluation | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.health.evaluate()
      .then(setEvaluation)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">加载中...</div>
  }

  const radarData = evaluation?.dimensions?.map((d: HealthDimension) => ({
    dimension: d.dimension,
    score: d.score,
    fullMark: 100,
  })) || []

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    if (score >= 40) return 'text-orange-400'
    return 'text-red-400'
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">组织健康度</h1>
        <p className="text-gray-400 text-sm mt-1">十二维度健康评估雷达图</p>
      </div>

      {/* 总分 */}
      {evaluation && (
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700 text-center">
          <div className="text-sm text-gray-400 mb-1">综合健康度</div>
          <div className={`text-4xl font-bold ${getScoreColor(evaluation.overall_score)}`}>
            {evaluation.overall_score?.toFixed(1)}
          </div>
          <div className="text-sm text-gray-500 mt-1">/ 100</div>
        </div>
      )}

      {/* 雷达图 */}
      {radarData.length > 0 && (
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
          <h2 className="text-sm font-medium text-gray-400 mb-4">维度雷达图</h2>
          <RadarChart data={radarData} height={420} />
        </div>
      )}

      {/* 维度详情 */}
      {evaluation?.dimensions && (
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
          <h2 className="text-sm font-medium text-gray-400 mb-4">维度详情</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {evaluation.dimensions.map((dim) => (
              <div key={dim.dimension} className="p-4 bg-dark-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{dim.dimension}</span>
                  <span className={`text-sm font-bold ${getScoreColor(dim.score)}`}>
                    {dim.score?.toFixed(1)}
                  </span>
                </div>
                <div className="w-full bg-dark-600 rounded-full h-2 mb-2">
                  <div
                    className="h-2 rounded-full bg-blue-500 transition-all"
                    style={{ width: `${dim.score}%` }}
                  />
                </div>
                {dim.description && (
                  <p className="text-xs text-gray-400">{dim.description}</p>
                )}
                {dim.suggestion && (
                  <p className="text-xs text-blue-400 mt-1">建议: {dim.suggestion}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 优化建议 */}
      {evaluation?.suggestions && evaluation.suggestions.length > 0 && (
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
          <h2 className="text-sm font-medium text-gray-400 mb-4">优化建议</h2>
          <ul className="space-y-2">
            {evaluation.suggestions.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                <span className="text-blue-400 mt-0.5">•</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
