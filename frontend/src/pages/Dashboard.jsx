import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { proteinApi, moleculeApi, analysisApi } from '../services/api'

export default function Dashboard() {
  const [stats, setStats] = useState({ proteins: 0, molecules: 0, analyses: 0, valid: 0, invalid: 0 })
  const [molecules, setMolecules] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => { loadStats() }, [])

  async function loadStats() {
    try {
      const [proteins, mols, analyses] = await Promise.all([
        proteinApi.list(), moleculeApi.list(), analysisApi.list(),
      ])
      const m = mols.data
      setMolecules(m.slice(-6).reverse())
      setStats({
        proteins: proteins.data.length,
        molecules: m.length,
        analyses: analyses.data.length,
        valid: m.filter(x => x.is_valid === true).length,
        invalid: m.filter(x => x.is_valid === false).length,
      })
    } catch (e) { console.error(e) }
    setLoading(false)
  }


  const viabilityData = [
    { label: 'Alta', pct: stats.molecules ? Math.round(stats.valid / Math.max(stats.molecules, 1) * 100) : 0, color: '#A3E635' },
    { label: 'Media', pct: stats.molecules ? Math.round((stats.molecules - stats.valid - stats.invalid) / Math.max(stats.molecules, 1) * 100) : 0, color: '#22D3EE' },
    { label: 'Baixa', pct: stats.molecules ? Math.round(stats.invalid / Math.max(stats.molecules, 1) * 100) : 0, color: '#F87171' },
  ]

  if (loading) return <div className="flex items-center justify-center h-64"><div className="text-gray-500">Carregando...</div></div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Bem-vindo(a) ao <span className="text-accent-cyan">PharmaAI</span></h1>
          <p className="text-gray-400 text-sm mt-1">Selecione uma proteina alvo e gere novas moleculas com apoio da inteligencia artificial.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate('/molecules?tab=generate')}
            className="bg-gradient-to-r from-accent-cyan to-accent-teal text-navy-950 px-5 py-2.5 rounded-lg font-semibold text-sm hover:opacity-90 transition-opacity flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            Gerar Novas Estruturas
          </button>
        </div>
      </div>

      {/* Pipeline Steps */}
      <div className="bg-navy-800 rounded-xl border border-navy-600/50 p-5">
        <div className="grid grid-cols-3 gap-4">
          {[
            { step: 1, title: 'Selecionar Alvo', desc: 'Escolha ou carregue sua proteina alvo', icon: <svg className="w-6 h-6 text-accent-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>, path: '/proteins' },
            { step: 2, title: 'Gerar Moleculas', desc: 'IA gera novas estruturas quimicas', icon: <svg className="w-6 h-6 text-accent-green" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-1.5 4.5H6.5L5 14.5m14 0H5" /></svg>, path: '/molecules' },
            { step: 3, title: 'Avaliar', desc: 'ADMET, interacao e viabilidade', icon: <svg className="w-6 h-6 text-accent-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>, path: '/analysis' },
          ].map(s => (
            <Link key={s.step} to={s.path} className="relative bg-navy-700/50 rounded-xl p-4 border border-navy-600/30 hover:border-accent-cyan/30 transition-colors group">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">{s.icon}</div>
                <div>
                  <p className="font-semibold text-white text-sm group-hover:text-accent-cyan transition-colors">{s.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{s.desc}</p>
                </div>
              </div>
              <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-navy-800 border border-navy-600/50 flex items-center justify-center">
                <span className="text-accent-cyan text-xs font-bold">{s.step}</span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Moleculas geradas', value: stats.molecules, color: 'from-accent-cyan/20 to-accent-cyan/5', iconColor: 'text-accent-cyan', icon: <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-1.5 4.5H6.5L5 14.5m14 0H5" /></svg> },
          { label: 'Potenciais candidatos', value: stats.valid, color: 'from-accent-green/20 to-accent-green/5', iconColor: 'text-accent-green', icon: <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" /></svg> },
          { label: 'Avaliacoes realizadas', value: stats.analyses, color: 'from-accent-blue/20 to-accent-blue/5', iconColor: 'text-accent-blue', icon: <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg> },
          { label: 'Alvos explorados', value: stats.proteins, color: 'from-accent-teal/20 to-accent-teal/5', iconColor: 'text-accent-teal', icon: <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 7.5l-2.25-1.313M21 7.5v2.25m0-2.25l-2.25 1.313M3 7.5l2.25-1.313M3 7.5l2.25 1.313M3 7.5v2.25m9 3l2.25-1.313M12 12.75l-2.25-1.313M12 12.75V15m0 6.75l2.25-1.313M12 21.75V19.5m0 2.25l-2.25-1.313m0-16.875L12 2.25l2.25 1.313M21 14.25v2.25l-2.25 1.313m-13.5 0L3 16.5v-2.25" /></svg> },
        ].map(s => (
          <div key={s.label} className={`bg-gradient-to-br ${s.color} bg-navy-800 rounded-xl border border-navy-600/50 p-5`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-xs">{s.label}</p>
                <p className="text-3xl font-bold text-white mt-1">{s.value}</p>
              </div>
              <div className={`${s.iconColor} opacity-50`}>{s.icon}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-3 gap-6">
        {/* Moleculas em destaque */}
        <div className="col-span-2 bg-navy-800 rounded-xl border border-navy-600/50 p-5">
          <h3 className="font-semibold text-white mb-4">Moleculas em destaque</h3>
          {molecules.length === 0 ? (
            <p className="text-gray-500 text-sm">Nenhuma molecula ainda. Clique em "Inicializar Banco" acima.</p>
          ) : (
            <div className="grid grid-cols-3 gap-3">
              {molecules.slice(0, 3).map(m => (
                <div key={m.id} className="bg-navy-700/50 rounded-lg border border-navy-600/30 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-white truncate max-w-[120px]" title={m.name}>{m.name}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      m.lipinski_pass ? 'bg-accent-green/20 text-accent-green' : 'bg-red-500/20 text-red-400'
                    }`}>{m.molecular_weight?.toFixed(0) || '?'}</span>
                  </div>
                  <p className="text-[10px] text-gray-500 truncate mb-2" title={m.smiles}>{m.smiles}</p>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">LogP: <span className="text-gray-300">{m.logp?.toFixed(2) || '-'}</span></span>
                    <span className={`font-medium ${m.lipinski_pass ? 'text-accent-green' : m.lipinski_pass === false ? 'text-red-400' : 'text-gray-500'}`}>
                      {m.lipinski_pass ? 'Viavel' : m.lipinski_pass === false ? 'Inviavel' : 'Pendente'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
          {molecules.length > 0 && (
            <Link to="/molecules" className="inline-flex items-center gap-1 text-xs text-accent-cyan hover:text-accent-teal mt-4 transition-colors">
              Ver todos os resultados <span>&rarr;</span>
            </Link>
          )}
        </div>

        {/* Distribuicao de Viabilidade */}
        <div className="bg-navy-800 rounded-xl border border-navy-600/50 p-5">
          <h3 className="font-semibold text-white mb-4">Distribuicao de Viabilidade</h3>
          <div className="flex items-center justify-center">
            <div className="relative w-36 h-36">
              <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                {(() => {
                  let offset = 0
                  const total = Math.max(stats.molecules, 1)
                  return viabilityData.map((d, i) => {
                    const pct = d.pct
                    const dasharray = `${pct * 2.51} ${251 - pct * 2.51}`
                    const el = (
                      <circle key={i} cx="50" cy="50" r="40" fill="none" stroke={d.color}
                        strokeWidth="8" strokeDasharray={dasharray} strokeDashoffset={-offset * 2.51}
                        className="transition-all duration-500" />
                    )
                    offset += pct
                    return el
                  })
                })()}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-bold text-white">{stats.molecules}</span>
                <span className="text-[10px] text-gray-500">moleculas</span>
              </div>
            </div>
          </div>
          <div className="mt-4 space-y-2">
            {viabilityData.map(d => (
              <div key={d.label} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                  <span className="text-gray-400">{d.label}</span>
                </div>
                <span className="text-white font-medium">{d.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
