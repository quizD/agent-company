import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import PoolPage from './pages/PoolPage'
import TenderPage from './pages/TenderPage'
import PerformancePage from './pages/PerformancePage'
import HealthPage from './pages/HealthPage'
import ValuesPage from './pages/ValuesPage'

function App() {
  return (
    <div className="flex h-screen bg-dark-900 text-white">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/pool" element={<PoolPage />} />
          <Route path="/tender" element={<TenderPage />} />
          <Route path="/performance" element={<PerformancePage />} />
          <Route path="/health" element={<HealthPage />} />
          <Route path="/values" element={<ValuesPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
