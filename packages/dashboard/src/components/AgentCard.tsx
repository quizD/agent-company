import { Agent } from '../types'
import GradeTag from './GradeTag'

interface AgentCardProps {
  agent: Agent
}

export default function AgentCard({ agent }: AgentCardProps) {
  return (
    <div className="bg-dark-800 rounded-xl p-5 border border-dark-700 hover:border-dark-600 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium text-white">{agent.name}</h3>
        <GradeTag grade={agent.grade} />
      </div>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">分类</span>
          <span className="text-gray-200">{agent.category}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">模型等级</span>
          <span className="text-gray-200">{agent.model_tier}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">绩效分</span>
          <span className="text-gray-200">{agent.performance_score.toFixed(1)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">时薪</span>
          <span className="text-gray-200">¥{agent.hourly_cost}</span>
        </div>
        <div className="mt-3 flex flex-wrap gap-1">
          {agent.skills.slice(0, 4).map((skill) => (
            <span
              key={skill}
              className="px-2 py-0.5 text-xs rounded bg-dark-700 text-gray-300"
            >
              {skill}
            </span>
          ))}
          {agent.skills.length > 4 && (
            <span className="px-2 py-0.5 text-xs rounded bg-dark-700 text-gray-400">
              +{agent.skills.length - 4}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
