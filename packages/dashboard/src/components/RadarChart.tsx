import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

interface RadarDataPoint {
  dimension: string
  score: number
  fullMark?: number
}

interface RadarChartProps {
  data: RadarDataPoint[]
  height?: number
}

export default function RadarChart({ data, height = 400 }: RadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsRadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="#334155" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fill: '#94a3b8', fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: '#64748b', fontSize: 10 }}
        />
        <Radar
          name="健康度"
          dataKey="score"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.3}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
            color: '#fff',
          }}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  )
}
