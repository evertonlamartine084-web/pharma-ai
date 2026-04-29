import { useState, useEffect } from 'react'
import { moleculeApi, similarityApi } from '../services/api'
import Card from '../components/Card'
import { inputCls, tabCls } from '../styles'

export default function Similarity() {
  const [molecules, setMolecules] = useState([])
  const [selectedMol, setSelectedMol] = useState('')
  const [results, setResults] = useState(null)
  const [matrix, setMatrix] = useState(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState('find')

  useEffect(() => {
    moleculeApi.list().then(res => setMolecules(res.data)).catch(() => {})
  }, [])

  async function findSimilar() {
    if (!selectedMol) return
    setLoading(true); setResults(null)
    try {
      const res = await similarityApi.find(parseInt(selectedMol), 15)
      setResults(res.data)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  async function loadMatrix() {
    setLoading(true); setMatrix(null)
    try {
      const res = await similarityApi.matrix(20)
      setMatrix(res.data)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  function simColor(val) {
    if (val >= 0.85) return 'bg-accent-green/80 text-navy-950'
    if (val >= 0.7) return 'bg-accent-green/40 text-white'
    if (val >= 0.5) return 'bg-accent-cyan/30 text-white'
    if (val >= 0.3) return 'bg-navy-600/50 text-gray-300'
    return 'bg-navy-700/30 text-gray-500'
  }

  function simBar(val) {
    if (val >= 0.7) return 'bg-accent-green'
    if (val >= 0.5) return 'bg-accent-cyan'
    if (val >= 0.3) return 'bg-yellow-400'
    return 'bg-red-400'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Similaridade Molecular</h1>
        <div className="flex gap-2">
          {['find', 'matrix'].map(t => (
            <button key={t} onClick={() => setTab(t)} className={tabCls(tab === t)}>
              {{ find: 'Buscar Similares', matrix: 'Matriz' }[t]}
            </button>
          ))}
        </div>
      </div>

      {tab === 'find' && (
        <div className="space-y-6">
          <Card title="Buscar Moleculas Similares (Tanimoto ECFP4)">
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm text-gray-400 mb-1">Molecula de Referencia</label>
                <select className={inputCls} value={selectedMol} onChange={e => setSelectedMol(e.target.value)}>
                  <option value="">Selecione...</option>
                  {molecules.map(m => <option key={m.id} value={m.id}>{m.name} ({m.smiles.substring(0, 30)}...)</option>)}
                </select>
              </div>
              <button onClick={findSimilar} disabled={loading || !selectedMol}
                className="bg-gradient-to-r from-accent-cyan to-accent-teal text-navy-950 px-5 py-2 rounded-lg font-semibold text-sm hover:opacity-90 disabled:opacity-50">
                {loading ? 'Buscando...' : 'Buscar'}
              </button>
            </div>
          </Card>

          {results && (
            <Card title={`Moleculas similares a "${results.query.name}" (${results.total_compared} comparadas)`}>
              <div className="space-y-2">
                {results.similar.map((s, i) => (
                  <div key={s.id} className="flex items-center gap-4 p-3 bg-navy-700/30 rounded-lg border border-navy-600/20">
                    <span className="text-gray-500 text-sm w-6">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm font-medium">{s.name}</p>
                      <p className="text-xs text-gray-500 truncate" title={s.smiles}>{s.smiles}</p>
                    </div>
                    <div className="w-32">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-500">{s.classification}</span>
                        <span className="text-white font-mono font-bold">{(s.similarity * 100).toFixed(1)}%</span>
                      </div>
                      <div className="h-1.5 bg-navy-700 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${simBar(s.similarity)}`} style={{ width: `${s.similarity * 100}%` }} />
                      </div>
                    </div>
                  </div>
                ))}
                {results.similar.length === 0 && (
                  <p className="text-gray-500 text-sm">Nenhuma molecula similar encontrada.</p>
                )}
              </div>
            </Card>
          )}
        </div>
      )}

      {tab === 'matrix' && (
        <div className="space-y-4">
          <Card title="Matriz de Similaridade Tanimoto" actions={
            <button onClick={loadMatrix} disabled={loading}
              className="bg-gradient-to-r from-accent-cyan to-accent-teal text-navy-950 px-4 py-1.5 rounded-lg font-semibold text-xs hover:opacity-90 disabled:opacity-50">
              {loading ? 'Calculando...' : 'Gerar Matriz'}
            </button>
          }>
            {matrix ? (
              <div className="overflow-x-auto">
                <table className="text-xs">
                  <thead>
                    <tr>
                      <th className="p-1 text-gray-500 text-left min-w-[80px]"></th>
                      {matrix.names.map((name, i) => (
                        <th key={i} className="p-1 text-gray-400 font-normal" style={{ writingMode: 'vertical-lr', maxHeight: 100 }}>
                          <span className="truncate block max-w-[80px]" title={name}>{name}</span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {matrix.matrix.map((row, i) => (
                      <tr key={i}>
                        <td className="p-1 text-gray-400 truncate max-w-[100px]" title={matrix.names[i]}>{matrix.names[i]}</td>
                        {row.map((val, j) => (
                          <td key={j} className={`p-1 text-center font-mono ${i === j ? 'bg-navy-600/30 text-gray-500' : simColor(val)}`}
                            style={{ minWidth: 36, fontSize: 10 }}>
                            {i === j ? '-' : val.toFixed(2)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">Clique em "Gerar Matriz" para calcular a similaridade entre todas as moleculas.</p>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
