import { useState, useEffect } from 'react'
import { moleculeApi, proteinApi, analysisApi } from '../services/api'
import Card from '../components/Card'
import StatusBadge from '../components/StatusBadge'

export default function Analysis() {
  const [molecules, setMolecules] = useState([])
  const [proteins, setProteins] = useState([])
  const [analyses, setAnalyses] = useState([])
  const [selectedMol, setSelectedMol] = useState('')
  const [selectedProt, setSelectedProt] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [tab, setTab] = useState('pipeline')

  useEffect(() => { loadData() }, [])

  async function loadData() {
    try {
      const [mols, prots, anals] = await Promise.all([
        moleculeApi.list(), proteinApi.list(), analysisApi.list()
      ])
      setMolecules(mols.data)
      setProteins(prots.data)
      setAnalyses(anals.data)
    } catch (e) { console.error(e) }
  }

  async function runPipeline() {
    if (!selectedMol) return
    setLoading(true)
    setResults(null)
    try {
      const res = await analysisApi.pipeline(parseInt(selectedMol), selectedProt ? parseInt(selectedProt) : null)
      setResults(res.data)
      loadData()
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  async function runAdme() {
    if (!selectedMol) return
    setLoading(true)
    try {
      const res = await analysisApi.adme(parseInt(selectedMol))
      setResults({ adme: res.data.results })
      loadData()
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  async function runDocking() {
    if (!selectedMol || !selectedProt) return
    setLoading(true)
    try {
      const res = await analysisApi.docking({ molecule_id: parseInt(selectedMol), protein_id: parseInt(selectedProt) })
      setResults({ docking: res.data.results })
      loadData()
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const inputCls = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent'
  const btnCls = 'bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analises</h1>
        <div className="flex gap-2">
          {['pipeline', 'history'].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded-lg text-sm ${tab === t ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
              {{ pipeline: 'Pipeline', history: 'Historico' }[t]}
            </button>
          ))}
        </div>
      </div>

      {tab === 'pipeline' && (
        <div className="space-y-6">
          <Card title="Executar Analise">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Molecula</label>
                <select className={inputCls} value={selectedMol} onChange={e => setSelectedMol(e.target.value)}>
                  <option value="">Selecione...</option>
                  {molecules.map(m => <option key={m.id} value={m.id}>{m.name} ({m.smiles.substring(0, 30)}...)</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Proteina (para docking)</label>
                <select className={inputCls} value={selectedProt} onChange={e => setSelectedProt(e.target.value)}>
                  <option value="">Nenhuma</option>
                  {proteins.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="flex items-end gap-2">
                <button onClick={runPipeline} disabled={loading || !selectedMol} className={btnCls}>
                  {loading ? 'Executando...' : 'Pipeline Completo'}
                </button>
                <button onClick={runAdme} disabled={loading || !selectedMol}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm">ADME</button>
                <button onClick={runDocking} disabled={loading || !selectedMol || !selectedProt}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm">Docking</button>
              </div>
            </div>
          </Card>

          {results && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {results.validation && (
                <Card title="Validacao RDKit">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Valido</span>
                      <StatusBadge status={results.validation.valid ? 'valid' : 'invalid'} />
                    </div>
                    <div className="flex justify-between"><span className="text-gray-500">Peso Molecular</span><span>{results.validation.molecular_weight}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">LogP</span><span>{results.validation.logp}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">TPSA</span><span>{results.validation.tpsa}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">HBD / HBA</span><span>{results.validation.hbd} / {results.validation.hba}</span></div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Lipinski</span>
                      <StatusBadge status={results.validation.lipinski_pass ? 'valid' : 'warning'} />
                    </div>
                    <div className="flex justify-between"><span className="text-gray-500">Violacoes Lipinski</span><span>{results.validation.lipinski_violations}</span></div>
                  </div>
                </Card>
              )}

              {results.adme && (
                <Card title="Avaliacao ADME">
                  {results.adme.success !== false ? (
                    <div className="space-y-4 text-sm">
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Solubilidade</h4>
                        <div className="flex justify-between"><span className="text-gray-500">Log S</span><span>{results.adme.solubility?.log_s}</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">Classe</span><span>{results.adme.solubility?.class}</span></div>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Permeabilidade</h4>
                        <div className="flex justify-between"><span className="text-gray-500">Absorcao GI</span><span>{results.adme.permeability?.gi_absorption}</span></div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">BBB</span>
                          <StatusBadge status={results.adme.permeability?.bbb_permeant ? 'valid' : 'warning'} />
                        </div>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Drug-likeness</h4>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Lipinski</span>
                          <StatusBadge status={results.adme.druglikeness?.lipinski_pass ? 'valid' : 'warning'} />
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Veber</span>
                          <StatusBadge status={results.adme.druglikeness?.veber_pass ? 'valid' : 'warning'} />
                        </div>
                        <div className="flex justify-between"><span className="text-gray-500">Bioavailability</span><span>{results.adme.druglikeness?.bioavailability_score}</span></div>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Alertas</h4>
                        <div className="flex justify-between">
                          <span className="text-gray-500">PAINS</span>
                          <StatusBadge status={results.adme.alerts?.pains ? 'invalid' : 'valid'} />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-red-500 text-sm">{results.adme.error}</p>
                  )}
                </Card>
              )}

              {results.docking && (
                <Card title="Docking Molecular" className="lg:col-span-2">
                  {results.docking.success !== false ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-3 text-sm">
                        <div className="p-4 rounded-lg bg-gray-50">
                          <p className="text-gray-500 text-xs">Binding Affinity</p>
                          <p className="text-3xl font-bold text-primary-700">{results.docking.binding_affinity} <span className="text-sm font-normal">kcal/mol</span></p>
                          <StatusBadge status={results.docking.status} />
                          <p className="text-xs text-gray-400 mt-1">{results.docking.classification}</p>
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Proteina Alvo</h4>
                          <p>{results.docking.protein}</p>
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Propriedades do Ligante</h4>
                          {results.docking.ligand_properties && Object.entries(results.docking.ligand_properties).map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                              <span className="text-gray-500">{k}</span><span>{v}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="space-y-3 text-sm">
                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Interacoes Moleculares</h4>
                          {results.docking.interactions?.map((inter, i) => (
                            <div key={i} className="p-2 bg-gray-50 rounded mb-1">
                              <p className="font-medium">{inter.type}</p>
                              <p className="text-xs text-gray-400">Quantidade: {inter.count} | Forca: {inter.strength}</p>
                            </div>
                          ))}
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Sitios Ativos</h4>
                          {results.docking.active_sites?.map((site, i) => (
                            <div key={i} className="p-2 bg-gray-50 rounded mb-1">
                              <p className="text-xs font-medium">Sitio {site.site_id} - Centro: ({site.center.x}, {site.center.y}, {site.center.z})</p>
                              <p className="text-xs text-gray-400">
                                Residuos: {site.residues?.map(r => `${r.residue}${r.number}`).join(', ')}
                              </p>
                            </div>
                          ))}
                        </div>
                        <p className="text-xs text-gray-400 italic">{results.docking.note}</p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-red-500 text-sm">{results.docking.error}</p>
                  )}
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      {tab === 'history' && (
        <Card title={`Historico de Analises (${analyses.length})`}>
          {analyses.length === 0 ? (
            <p className="text-gray-400 text-sm">Nenhuma analise realizada ainda.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="pb-2">ID</th>
                    <th className="pb-2">Tipo</th>
                    <th className="pb-2">Molecula</th>
                    <th className="pb-2">Binding Affinity</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {analyses.map(a => (
                    <tr key={a.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2">{a.id}</td>
                      <td className="py-2">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          a.analysis_type === 'validation' ? 'bg-blue-100 text-blue-700' :
                          a.analysis_type === 'adme' ? 'bg-green-100 text-green-700' :
                          'bg-purple-100 text-purple-700'
                        }`}>{a.analysis_type}</span>
                      </td>
                      <td className="py-2">#{a.molecule_id}</td>
                      <td className="py-2">{a.binding_affinity ? `${a.binding_affinity} kcal/mol` : '-'}</td>
                      <td className="py-2"><StatusBadge status={a.status === 'completed' ? 'valid' : 'pending'} /></td>
                      <td className="py-2 text-xs text-gray-400">{a.created_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
