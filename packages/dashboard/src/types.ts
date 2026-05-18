export interface Agent {
  id: string
  name: string
  category: string
  skills: string[]
  model_tier: string
  performance_score: number
  grade: string
  hourly_cost: number
  status: string
}

export interface PoolStats {
  total_agents: number
  by_category: Record<string, number>
  by_grade: Record<string, number>
  average_score: number
}

export interface TenderRequest {
  task_description: string
  budget: number
  strategy?: string
}

export interface TenderResult {
  task_description: string
  winning_team: TeamMember[]
  total_cost: number
  estimated_quality: number
  strategy_used: string
}

export interface TeamMember {
  agent_id: string
  name: string
  role: string
  bid_amount: number
  score: number
}

export interface HealthDimension {
  dimension: string
  score: number
  weight: number
  description: string
  suggestion?: string
}

export interface HealthEvaluation {
  overall_score: number
  dimensions: HealthDimension[]
  suggestions: string[]
}

export interface Value {
  id: string
  content: string
  category: string
  source: string
  weight: number
}

export interface PerformanceRecord {
  agent_id: string
  name: string
  score: number
  grade: string
  trend: 'up' | 'down' | 'stable'
  tasks_completed: number
}
