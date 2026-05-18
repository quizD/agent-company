import { useEffect, useState } from 'react'
import { Search } from 'lucide-react'
import { api } from '../api/client'
import { Value } from '../types'

export default function ValuesPage() {
  const [values, setValues] = useState<Value[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('all')

  useEffect(() => {
    Promise.all([api.values.list(), api.values.categories()])
      .then(([valData, catData]) => {
        const valList = Array.isArray(valData) ? valData : valData.values || []
        const catList = Array.isArray(catData) ? catData : catData.categories || []
        setValues(valList)
        setCategories(catList)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filtered = values.filter((v) => {
    const matchCategory = activeCategory === 'all' || v.category === activeCategory
    const matchSearch = !search || v.content.toLowerCase().includes(search.toLowerCase())
    return matchCategory && matchSearch
  })

  const grouped = filtered.reduce<Record<string, Value[]>>((acc, v) => {
    if (!acc[v.category]) acc[v.category] = []
    acc[v.category].push(v)
    return acc
  }, {})

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">加载中...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">价值观库</h1>
        <p className="text-gray-400 text-sm mt-1">组织核心价值观与行为准则</p>
      </div>

      {/* 搜索和筛选 */}
      <div className="flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-3 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索价值观..."
            className="w-full pl-10 pr-4 py-2.5 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setActiveCategory('all')}
            className={`px-3 py-1.5 text-sm rounded-lg ${
              activeCategory === 'all'
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-dark-800 text-gray-400 border border-dark-700'
            }`}
          >
            全部
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1.5 text-sm rounded-lg ${
                activeCategory === cat
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'bg-dark-800 text-gray-400 border border-dark-700'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* 按分类分组展示 */}
      {Object.entries(grouped).map(([category, items]) => (
        <div key={category} className="space-y-3">
          <h2 className="text-lg font-semibold text-blue-400">{category}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {items.map((value) => (
              <div
                key={value.id}
                className="bg-dark-800 rounded-xl p-4 border border-dark-700 hover:border-dark-600 transition-colors"
              >
                <p className="text-sm text-gray-200 mb-3">{value.content}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs px-2 py-0.5 bg-dark-700 rounded text-gray-400">
                    {value.source}
                  </span>
                  <span className="text-xs text-gray-500">权重: {value.weight}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="text-center text-gray-500 py-12">
          没有找到匹配的价值观
        </div>
      )}
    </div>
  )
}
