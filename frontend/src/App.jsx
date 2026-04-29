import { useState } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { useAuth } from './services/auth'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Proteins from './pages/Proteins'
import Molecules from './pages/Molecules'
import Analysis from './pages/Analysis'
import Similarity from './pages/Similarity'

const navItems = [
  { path: '/', label: 'Dashboard', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4" /></svg>
  )},
  { path: '/molecules', label: 'Gerar Moleculas', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-1.5 4.5H6.5L5 14.5m14 0H5" /></svg>
  )},
  { path: '/proteins', label: 'Alvo Proteico', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 7.5l-2.25-1.313M21 7.5v2.25m0-2.25l-2.25 1.313M3 7.5l2.25-1.313M3 7.5l2.25 1.313M3 7.5v2.25m9 3l2.25-1.313M12 12.75l-2.25-1.313M12 12.75V15m0 6.75l2.25-1.313M12 21.75V19.5m0 2.25l-2.25-1.313m0-16.875L12 2.25l2.25 1.313M21 14.25v2.25l-2.25 1.313m-13.5 0L3 16.5v-2.25" /></svg>
  )},
  { path: '/analysis', label: 'Avaliacoes', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>
  )},
  { path: '/similarity', label: 'Similaridade', icon: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" /></svg>
  )},
]

export default function App() {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { user, logout, loading } = useAuth()

  if (loading) return <div className="min-h-screen bg-navy-950 flex items-center justify-center"><p className="text-gray-500">Carregando...</p></div>
  if (!user) return <Login />

  return (
    <div className="flex h-screen bg-navy-950">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-56' : 'w-16'} bg-navy-800 border-r border-navy-600/50 flex flex-col transition-all duration-300`}>
        {/* Logo */}
        <div className="p-4 border-b border-navy-600/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-teal flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-navy-950" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
            </div>
            {sidebarOpen && (
              <div>
                <h1 className="font-bold text-lg text-white leading-tight">Pharma<span className="text-accent-cyan">AI</span></h1>
                <p className="text-[10px] text-gray-500 leading-tight">IA que cria. Ciencia que transforma.</p>
              </div>
            )}
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(item => {
            const active = location.pathname === item.path
            return (
              <Link key={item.path} to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? 'bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20'
                    : 'text-gray-400 hover:text-white hover:bg-navy-700/50'
                }`}>
                {item.icon}
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* User + Toggle */}
        <div className="p-3 border-t border-navy-600/50 space-y-2">
          {user && (
            <div className="flex items-center gap-2 px-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-cyan to-accent-teal flex items-center justify-center flex-shrink-0">
                <span className="text-navy-950 text-xs font-bold">{user.username?.charAt(0).toUpperCase()}</span>
              </div>
              {sidebarOpen && (
                <div className="flex-1 min-w-0">
                  <p className="text-white text-xs font-medium truncate">{user.full_name || user.username}</p>
                  <button onClick={logout} className="text-[10px] text-gray-500 hover:text-red-400 transition-colors">Sair</button>
                </div>
              )}
            </div>
          )}
          <button onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-gray-500 hover:text-white hover:bg-navy-700/50 text-xs transition-colors">
            <svg className={`w-4 h-4 transition-transform ${sidebarOpen ? '' : 'rotate-180'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
            {sidebarOpen && <span>Recolher</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/proteins" element={<Proteins />} />
            <Route path="/molecules" element={<Molecules />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/similarity" element={<Similarity />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
