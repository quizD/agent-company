const API_BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export const api = {
  pool: {
    list: () => request<any>('/pool'),
    stats: () => request<any>('/pool/stats'),
  },
  tender: {
    analyze: (data: { task_description: string; budget: number }) =>
      request<any>('/tender/analyze', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    run: (data: { task_description: string; budget: number; strategy?: string }) =>
      request<any>('/tender/run', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },
  values: {
    list: () => request<any>('/values'),
    categories: () => request<any>('/values/categories'),
    match: (taskType: string) => request<any>(`/values/match?task_type=${taskType}`),
  },
  health: {
    evaluate: (data?: any) =>
      request<any>('/health/evaluate', {
        method: 'POST',
        body: JSON.stringify(data || {}),
      }),
    dimensions: () => request<any>('/health/dimensions'),
  },
  performance: {
    simulate: (data?: any) =>
      request<any>('/performance/simulate', {
        method: 'POST',
        body: JSON.stringify(data || {}),
      }),
  },
}
