interface GradeTagProps {
  grade: string
}

const gradeColors: Record<string, string> = {
  S: 'bg-green-500/20 text-green-400 border-green-500/30',
  A: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  B: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  C: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  D: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  F: 'bg-red-500/20 text-red-400 border-red-500/30',
}

export default function GradeTag({ grade }: GradeTagProps) {
  const color = gradeColors[grade] || gradeColors.B
  return (
    <span className={`px-2 py-0.5 text-xs font-bold rounded border ${color}`}>
      {grade}
    </span>
  )
}
