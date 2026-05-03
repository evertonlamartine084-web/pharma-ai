import { useState, useEffect } from 'react'
import { moleculeApi, proteinApi, analysisApi } from '../services/api'
import Card from '../components/Card'
import StatusBadge from '../components/StatusBadge'
import DockingViewer3D from '../components/DockingViewer3D'
import MolStructure2D from '../components/MolStructure2D'
import RadarChart, { calcRadarData } from '../components/RadarChart'
import { useToast } from '../components/Toast'
import AIAdvisor from '../components/AIAdvisor'
import { inputCls, tabCls } from '../styles'

export default function Analysis() {
  const [molecules, setMolecules] = useState([])
  const [proteins, setProteins] = useState([])
  const [analyses, setAnalyses] = useState([])
  const [selectedMol, setSelectedMol] = useState('')
  const [selectedProt, setSelectedProt] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [viewerData, setViewerData] = useState(null)
  const [tab, setTab] = useState('pipeline')
  const [admeSource, setAdmeSource] = useState('swissadme')
  const toast = useToast()

  useEffect(() => { loadData() }, [])

  async function loadData() {
    try {
      const [mols, prots, anals] = await Promise.all([moleculeApi.list(), proteinApi.list(), analysisApi.list()])
      setMolecules(mols.data); setProteins(prots.data); setAnalyses(anals.data)
    } catch (e) { console.error(e) }
  }

  async function runPipeline() {
    if (!selectedMol) return; setLoading(true); setResults(null); setViewerData(null)
    try { const res = await analysisApi.pipeline(parseInt(selectedMol), selectedProt ? parseInt(selectedProt) : null); setResults(res.data); if (res.data.viewer_data) setViewerData(res.data.viewer_data); loadData(); toast.success('Pipeline completo finalizado!') } catch (e) { console.error(e); toast.error('Erro no pipeline') }
    setLoading(false)
  }
  async function runAdme() {
    if (!selectedMol) return; setLoading(true)
    try { const res = await analysisApi.adme(parseInt(selectedMol), admeSource); setResults({ adme: res.data.results }); loadData(); toast.success(`ADME concluido (${res.data.results?.source || 'Local'})`) } catch (e) { console.error(e); toast.error('Erro na avaliacao ADME') }
    setLoading(false)
  }
  async function runDocking() {
    if (!selectedMol || !selectedProt) return; setLoading(true); setViewerData(null)
    try { const res = await analysisApi.docking({ molecule_id: parseInt(selectedMol), protein_id: parseInt(selectedProt) }); setResults({ docking: res.data.results }); if (res.data.viewer_data) setViewerData(res.data.viewer_data); loadData(); toast.success(`Docking concluido: ${res.data.results?.binding_affinity} kcal/mol`) } catch (e) { console.error(e); toast.error('Erro no docking') }
    setLoading(false)
  }

  const propLabels = {
    formula: 'Formula', molecular_weight: 'Molecular weight', num_heavy_atoms: 'Num. heavy atoms',
    num_arom_heavy_atoms: 'Num. arom. heavy atoms', fraction_csp3: 'Fraction Csp3',
    num_rotatable_bonds: 'Num. rotatable bonds', num_h_bond_acceptors: 'Num. H-bond acceptors',
    num_h_bond_donors: 'Num. H-bond donors', molar_refractivity: 'Molar Refractivity', tpsa: 'TPSA',
  }
  const propUnits = { molecular_weight: 'g/mol', tpsa: '\u00C5\u00B2' }
  const sectionHead = 'font-semibold text-white mb-2 bg-navy-700/50 px-3 py-1.5 rounded-lg text-xs border border-navy-600/30'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Avaliacoes</h1>
        <div className="flex gap-2">
          {['pipeline', 'history'].map(t => (
            <button key={t} onClick={() => setTab(t)} className={tabCls(tab === t)}>
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
                <label className="block text-sm text-gray-400 mb-1">Molecula</label>
                <select className={inputCls} value={selectedMol} onChange={e => setSelectedMol(e.target.value)}>
                  <option value="">Selecione...</option>
                  {molecules.map(m => <option key={m.id} value={m.id}>{m.name} ({m.smiles.substring(0, 30)}...)</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Proteina (para docking)</label>
                <select className={inputCls} value={selectedProt} onChange={e => setSelectedProt(e.target.value)}>
                  <option value="">Nenhuma</option>
                  {proteins.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-gray-500">ADME:</label>
                  <button onClick={() => setAdmeSource('swissadme')}
                    className={`px-2 py-1 rounded text-xs transition-colors ${admeSource === 'swissadme' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-navy-700/50 text-gray-500 border border-navy-600/30'}`}>SwissADME</button>
                  <button onClick={() => setAdmeSource('local')}
                    className={`px-2 py-1 rounded text-xs transition-colors ${admeSource === 'local' ? 'bg-accent-cyan/15 text-accent-cyan border border-accent-cyan/30' : 'bg-navy-700/50 text-gray-500 border border-navy-600/30'}`}>Local (RDKit)</button>
                </div>
                <div className="flex items-end gap-2">
                  <button onClick={runPipeline} disabled={loading || !selectedMol}
                    className="bg-gradient-to-r from-accent-cyan to-accent-teal text-navy-950 px-4 py-2 rounded-lg font-semibold text-sm hover:opacity-90 disabled:opacity-50">
                    {loading ? 'Executando...' : 'Pipeline'}
                  </button>
                  <button onClick={runAdme} disabled={loading || !selectedMol}
                    className="bg-accent-green/15 text-accent-green px-4 py-2 rounded-lg text-sm border border-accent-green/20 hover:bg-accent-green/25 disabled:opacity-50">ADME</button>
                  <button onClick={runDocking} disabled={loading || !selectedMol || !selectedProt}
                    className="bg-purple-500/15 text-purple-400 px-4 py-2 rounded-lg text-sm border border-purple-500/20 hover:bg-purple-500/25 disabled:opacity-50">Docking</button>
                </div>
              </div>
            </div>
          </Card>

          {results && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {results.validation && (
                <Card title="Validacao RDKit">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-gray-500">Valido</span><StatusBadge status={results.validation.valid ? 'valid' : 'invalid'} /></div>
                    <div className="flex justify-between"><span className="text-gray-500">Peso Molecular</span><span className="text-gray-300">{results.validation.molecular_weight}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">LogP</span><span className="text-gray-300">{results.validation.logp}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">TPSA</span><span className="text-gray-300">{results.validation.tpsa}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">HBD / HBA</span><span className="text-gray-300">{results.validation.hbd} / {results.validation.hba}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Lipinski</span><StatusBadge status={results.validation.lipinski_pass ? 'valid' : 'warning'} /></div>
                    <div className="flex justify-between"><span className="text-gray-500">Violacoes</span><span className="text-gray-300">{results.validation.lipinski_violations}</span></div>
                  </div>
                </Card>
              )}

              {results.adme && (
                <Card title={<span>Avaliacao ADME <span className={`ml-2 text-xs px-2 py-0.5 rounded ${results.adme.source === 'SwissADME' ? 'bg-red-500/15 text-red-400 border border-red-500/20' : 'bg-accent-cyan/15 text-accent-cyan border border-accent-cyan/20'}`}>{results.adme.source || 'Local (RDKit)'}</span></span>} className="lg:col-span-2">
                  {results.adme.success !== false ? (
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div className="flex flex-col items-center">
                          <MolStructure2D smiles={molecules.find(m => String(m.id) === selectedMol)?.smiles} width={250} height={200} />
                          <p className="text-xs text-gray-600 mt-2 text-center max-w-[250px] truncate">{molecules.find(m => String(m.id) === selectedMol)?.smiles}</p>
                          <div className="mt-3">
                            <RadarChart data={calcRadarData(results.adme)} size={220} />
                          </div>
                        </div>
                        <div className="text-sm">
                          <h4 className={sectionHead}>Physicochemical Properties</h4>
                          <div className="space-y-1">
                            {results.adme.physicochemical && Object.entries(results.adme.physicochemical).map(([k, v]) => (
                              <div key={k} className="flex justify-between text-xs">
                                <span className="text-gray-500">{propLabels[k] || k}</span>
                                <span className="font-mono text-gray-300">{v}{propUnits[k] ? ` ${propUnits[k]}` : ''}</span>
                              </div>
                            ))}
                          </div>
                          {results.adme.lipophilicity && (
                            <div className="mt-3">
                              <h4 className={sectionHead}>Lipophilicity</h4>
                              <div className="space-y-1">
                                {['ilogp', 'xlogp3', 'wlogp', 'mlogp', 'silicos_it'].map(k => (
                                  <div key={k} className="flex justify-between text-xs">
                                    <span className="text-gray-500">Log P ({k.toUpperCase().replace('_', '-')})</span>
                                    <span className="font-mono text-gray-300">{results.adme.lipophilicity[k]}</span>
                                  </div>
                                ))}
                                <div className="flex justify-between text-xs font-bold border-t border-navy-600/30 pt-1 mt-1">
                                  <span className="text-white">Consensus Log P</span>
                                  <span className="font-mono text-accent-cyan">{results.adme.lipophilicity.consensus_logp}</span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="text-sm">
                          <h4 className={sectionHead}>Water Solubility</h4>
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs"><span className="text-gray-500">Log S (ESOL)</span><span className="font-mono text-gray-300">{results.adme.solubility?.log_s_esol}</span></div>
                            <div className="flex justify-between text-xs"><span className="text-gray-500">Solubility</span><span className="font-mono text-gray-300">{results.adme.solubility?.solubility_mg_ml} mg/ml ; {results.adme.solubility?.solubility_mol_l} mol/l</span></div>
                            <div className="flex justify-between text-xs"><span className="text-gray-500">Class</span><span className="font-mono text-gray-300">{results.adme.solubility?.class_esol}</span></div>
                            <div className="border-t border-navy-600/30 my-1" />
                            <div className="flex justify-between text-xs"><span className="text-gray-500">Log S (Ali)</span><span className="font-mono text-gray-300">{results.adme.solubility?.log_s_ali}</span></div>
                            <div className="flex justify-between text-xs"><span className="text-gray-500">Class</span><span className="font-mono text-gray-300">{results.adme.solubility?.class_ali}</span></div>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="text-sm">
                          <h4 className={sectionHead}>Pharmacokinetics</h4>
                          {results.adme.pharmacokinetics && (
                            <div className="space-y-1">
                              {[['GI absorption', 'gi_absorption', true], ['BBB permeant', 'bbb_permeant'], ['P-gp substrate', 'pgp_substrate'],
                                ['CYP1A2 inhibitor', 'cyp1a2_inhibitor'], ['CYP2C19 inhibitor', 'cyp2c19_inhibitor'], ['CYP2C9 inhibitor', 'cyp2c9_inhibitor'],
                                ['CYP2D6 inhibitor', 'cyp2d6_inhibitor'], ['CYP3A4 inhibitor', 'cyp3a4_inhibitor']].map(([label, key, isStr]) => (
                                <div key={key} className="flex justify-between text-xs items-center">
                                  <span className="text-gray-500">{label}</span>
                                  <span className={`font-mono ${isStr ? (results.adme.pharmacokinetics[key] === 'High' ? 'text-accent-green' : 'text-red-400') : 'text-gray-300'}`}>
                                    {isStr ? results.adme.pharmacokinetics[key] : (results.adme.pharmacokinetics[key] ? 'Yes' : 'No')}
                                  </span>
                                </div>
                              ))}
                              <div className="flex justify-between text-xs"><span className="text-gray-500">Log Kp (skin)</span><span className="font-mono text-gray-300">{results.adme.pharmacokinetics.log_kp_skin} cm/s</span></div>
                            </div>
                          )}
                        </div>
                        <div className="text-sm">
                          <h4 className={sectionHead}>Druglikeness</h4>
                          <div className="space-y-1">
                            {[['Lipinski', 'lipinski'], ['Ghose', 'ghose'], ['Veber', 'veber'], ['Egan', 'egan'], ['Muegge', 'muegge']].map(([label, key]) => (
                              <div key={key} className="flex justify-between text-xs items-center">
                                <span className="text-gray-500">{label}</span>
                                <span className="font-mono text-gray-300">{results.adme.druglikeness?.[key]}</span>
                              </div>
                            ))}
                            <div className="flex justify-between text-xs items-center border-t border-navy-600/30 pt-1 mt-1">
                              <span className="text-white font-bold">Bioavailability Score</span>
                              <span className="font-mono font-bold text-accent-cyan">{results.adme.druglikeness?.bioavailability_score}</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-sm">
                          <h4 className={sectionHead}>Medicinal Chemistry</h4>
                          {results.adme.medicinal_chemistry && (
                            <div className="space-y-1">
                              {[['PAINS', 'pains_alerts'], ['Brenk', 'brenk_alerts'], ['Leadlikeness', 'leadlikeness']].map(([label, key]) => (
                                <div key={key} className="flex justify-between text-xs items-center">
                                  <span className="text-gray-500">{label}</span>
                                  <span className="font-mono text-gray-300">{results.adme.medicinal_chemistry[key]}</span>
                                </div>
                              ))}
                              <div className="flex justify-between text-xs items-center border-t border-navy-600/30 pt-1 mt-1">
                                <span className="text-white font-bold">Synth. accessibility</span>
                                <span className="font-mono font-bold text-accent-cyan">{results.adme.medicinal_chemistry.synthetic_accessibility}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-red-400 text-sm">{results.adme.error}</p>
                  )}
                </Card>
              )}

              {results.docking && (
                <Card title="Docking Molecular" className="lg:col-span-2">
                  {results.docking.success !== false ? (
                    <div className="space-y-6">
                      {viewerData && (
                        <div>
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium text-gray-300">Visualizacao 3D - Alvo + Ligante</h4>
                            <div className="flex gap-3 text-xs">
                              <span className="text-accent-cyan">Alvo: <span className="text-white font-medium">{proteins.find(p => String(p.id) === selectedProt)?.name || '-'}</span></span>
                              <span className="text-accent-green">Ligante: <span className="text-white font-medium">{molecules.find(m => String(m.id) === selectedMol)?.name || '-'}</span></span>
                            </div>
                          </div>
                          <DockingViewer3D proteinPdb={viewerData.protein_pdb} ligandSdf={viewerData.ligand_sdf} activeSiteResidues={viewerData.active_site_residues} contacts3d={viewerData.contacts_3d || []} height={500} />
                          <p className="text-[10px] text-gray-600 mt-1 font-mono">Ligante SMILES: {molecules.find(m => String(m.id) === selectedMol)?.smiles}</p>
                        </div>
                      )}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-3 text-sm">
                          <div className="p-4 rounded-lg bg-navy-700/50 border border-navy-600/30">
                            <div className="flex items-center justify-between mb-1">
                              <p className="text-gray-500 text-xs">Binding Affinity</p>
                              <span className={`text-[10px] px-2 py-0.5 rounded border ${results.docking.method?.includes('Vina') ? 'bg-accent-green/10 text-accent-green border-accent-green/20' : 'bg-navy-600/50 text-gray-400 border-navy-500/30'}`}>
                                {results.docking.method || 'Simulacao'}
                              </span>
                            </div>
                            <p className="text-3xl font-bold text-accent-cyan">{results.docking.binding_affinity} <span className="text-sm font-normal text-gray-400">kcal/mol</span></p>
                            <StatusBadge status={results.docking.status} />
                            <p className="text-xs text-gray-500 mt-1">{results.docking.classification}</p>
                          </div>
                          {results.docking.all_modes && (
                            <div>
                              <h4 className="font-medium text-gray-300 mb-2">Modos de Ligacao (Vina)</h4>
                              <div className="space-y-1">
                                {results.docking.all_modes.map((m, i) => (
                                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded bg-navy-700/30">
                                    <span className="text-gray-500">Modo {m.mode}</span>
                                    <span className="font-mono text-white">{m.affinity} kcal/mol</span>
                                    <span className="text-gray-600">RMSD: {m.rmsd_lb}/{m.rmsd_ub}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          <div>
                            <h4 className="font-medium text-gray-300 mb-2">Proteina Alvo</h4>
                            <p className="text-gray-400">{results.docking.protein}</p>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-300 mb-2">Propriedades do Ligante</h4>
                            {results.docking.ligand_properties && Object.entries(results.docking.ligand_properties).map(([k, v]) => (
                              <div key={k} className="flex justify-between text-xs"><span className="text-gray-500">{k}</span><span className="text-gray-300">{v}</span></div>
                            ))}
                          </div>
                        </div>
                        <div className="space-y-3 text-sm">
                          <div>
                            <h4 className="font-medium text-gray-300 mb-2">Interacoes Moleculares</h4>
                            {results.docking.interactions?.map((inter, i) => (
                              <div key={i} className="p-2 bg-navy-700/50 rounded-lg border border-navy-600/20 mb-1">
                                <p className="font-medium text-gray-200">{inter.type}</p>
                                <p className="text-xs text-gray-500">Quantidade: {inter.count} | Forca: {inter.strength}</p>
                              </div>
                            ))}
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-300 mb-2">Sitios Ativos</h4>
                            {results.docking.active_sites?.map((site, i) => (
                              <div key={i} className="p-2 bg-navy-700/50 rounded-lg border border-navy-600/20 mb-1">
                                <p className="text-xs font-medium text-gray-300">Sitio {site.site_id} - Centro: ({site.center.x}, {site.center.y}, {site.center.z})</p>
                                <p className="text-xs text-gray-500">Residuos: {site.residues?.map(r => `${r.residue}${r.number}`).join(', ')}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-red-400 text-sm">{results.docking.error}</p>
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
            <p className="text-gray-500 text-sm">Nenhuma analise realizada ainda.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left text-gray-500 border-b border-navy-600/50">
                  <th className="pb-2">ID</th><th className="pb-2">Tipo</th><th className="pb-2">Molecula</th><th className="pb-2">Binding Affinity</th><th className="pb-2">Status</th><th className="pb-2">Data</th>
                </tr></thead>
                <tbody>
                  {analyses.map(a => (
                    <tr key={a.id} className="border-b border-navy-600/20 hover:bg-navy-700/30">
                      <td className="py-2 text-gray-300">{a.id}</td>
                      <td className="py-2">
                        <span className={`px-2 py-0.5 rounded text-xs border ${
                          a.analysis_type === 'validation' ? 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/20' :
                          a.analysis_type === 'adme' ? 'bg-accent-green/10 text-accent-green border-accent-green/20' :
                          'bg-purple-500/10 text-purple-400 border-purple-500/20'
                        }`}>{a.analysis_type}</span>
                      </td>
                      <td className="py-2 text-gray-300">#{a.molecule_id}</td>
                      <td className="py-2 text-gray-300">{a.binding_affinity ? `${a.binding_affinity} kcal/mol` : '-'}</td>
                      <td className="py-2"><StatusBadge status={a.status === 'completed' ? 'valid' : 'pending'} /></td>
                      <td className="py-2 text-xs text-gray-500">{a.created_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
      {/* Consultor IA flutuante */}
      {selectedMol && (
        <AIAdvisor moleculeId={parseInt(selectedMol)} moleculeName={molecules.find(m => String(m.id) === selectedMol)?.name} />
      )}
    </div>
  )
}
