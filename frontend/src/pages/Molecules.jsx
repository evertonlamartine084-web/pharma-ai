import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { moleculeApi, proteinApi } from '../services/api'
import Card from '../components/Card'
import StatusBadge from '../components/StatusBadge'
import { inputCls, btnCls, btnSecondary, tabCls } from '../styles'

export default function Molecules() {
  const [searchParams] = useSearchParams()
  const [molecules, setMolecules] = useState([])
  const [proteins, setProteins] = useState([])
  const [tab, setTab] = useState(searchParams.get('tab') === 'generate' ? 'generate' : 'list')
  const [form, setForm] = useState({ name: '', smiles: '', target_protein_id: '' })
  const [genForm, setGenForm] = useState({ seed_smiles: '', n_molecules: 10, target_protein_id: '' })
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')
  const [genResults, setGenResults] = useState(null)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    try {
      const [mols, prots] = await Promise.all([moleculeApi.list(), proteinApi.list()])
      setMolecules(mols.data); setProteins(prots.data)
    } catch (e) { console.error(e) }
  }

  async function addSmiles(e) {
    e.preventDefault(); setLoading(true)
    try {
      const data = { ...form, target_protein_id: form.target_protein_id ? parseInt(form.target_protein_id) : null }
      await moleculeApi.add(data); setMsg('Molecula adicionada'); setForm({ name: '', smiles: '', target_protein_id: '' }); loadData()
    } catch (e) { setMsg('Erro: ' + (e.response?.data?.detail || e.message)) }
    setLoading(false)
  }

  async function uploadCsv(e) {
    e.preventDefault()
    const fileInput = document.getElementById('csv-file')
    if (!fileInput.files[0]) return
    setLoading(true)
    try { const res = await moleculeApi.uploadCsv(fileInput.files[0]); setMsg(`${res.data.count} moleculas importadas`); setTab('list'); loadData() }
    catch (e) { setMsg('Erro: ' + (e.response?.data?.detail || e.message)) }
    setLoading(false)
  }

  async function generateMolecules(e) {
    e.preventDefault(); setLoading(true); setGenResults(null)
    try {
      const data = { seed_smiles: genForm.seed_smiles, n_molecules: parseInt(genForm.n_molecules), target_protein_id: genForm.target_protein_id ? parseInt(genForm.target_protein_id) : null }
      const res = await moleculeApi.generate(data); setGenResults(res.data); setMsg(`${res.data.count} moleculas geradas por IA + SwissADME`); loadData()
    } catch (e) { setMsg('Erro: ' + (e.response?.data?.detail || e.message)) }
    setLoading(false)
  }

  async function exportData(format) {
    try {
      const res = await moleculeApi.export(format)
      const blob = new Blob([format === 'csv' ? res.data : JSON.stringify(res.data, null, 2)], { type: format === 'csv' ? 'text/csv' : 'application/json' })
      const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `molecules.${format}`; a.click(); URL.revokeObjectURL(url)
    } catch (e) { console.error(e) }
  }

  function getStatus(mol) {
    if (mol.is_valid === null) return 'pending'
    if (!mol.is_valid) return 'invalid'
    if (mol.lipinski_pass === false) return 'warning'
    return 'valid'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Gerar Moleculas</h1>
        <div className="flex gap-2">
          {['list', 'add', 'csv', 'generate'].map(t => (
            <button key={t} onClick={() => { setTab(t); setMsg('') }} className={tabCls(tab === t)}>
              {{ list: 'Lista', add: 'Adicionar SMILES', csv: 'Upload CSV', generate: 'Gerar (IA)' }[t]}
            </button>
          ))}
        </div>
      </div>

      {msg && <div className="bg-accent-cyan/10 text-accent-cyan px-4 py-2 rounded-lg text-sm border border-accent-cyan/20">{msg}</div>}

      {tab === 'list' && (
        <Card title={`Moleculas (${molecules.length})`} actions={
          <div className="flex gap-2">
            <button onClick={() => exportData('json')} className={btnSecondary + ' !py-1 !px-3 !text-xs'}>JSON</button>
            <button onClick={() => exportData('csv')} className={btnSecondary + ' !py-1 !px-3 !text-xs'}>CSV</button>
          </div>
        }>
          {molecules.length === 0 ? (
            <p className="text-gray-500 text-sm">Nenhuma molecula. Use "Inicializar Banco" no Dashboard.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left text-gray-500 border-b border-navy-600/50">
                  <th className="pb-2">Nome</th><th className="pb-2">SMILES</th><th className="pb-2">MW</th><th className="pb-2">LogP</th><th className="pb-2">Lipinski</th><th className="pb-2">Fonte</th><th className="pb-2">Status</th>
                </tr></thead>
                <tbody>
                  {molecules.map(m => (
                    <tr key={m.id} className="border-b border-navy-600/20 hover:bg-navy-700/30">
                      <td className="py-2 text-white font-medium">{m.name}</td>
                      <td className="py-2 text-xs text-gray-500 max-w-[200px] truncate" title={m.smiles}>{m.smiles}</td>
                      <td className="py-2 text-gray-300">{m.molecular_weight?.toFixed(1) || '-'}</td>
                      <td className="py-2 text-gray-300">{m.logp?.toFixed(2) || '-'}</td>
                      <td className="py-2">{m.lipinski_pass === true ? <span className="text-accent-green">\u2714</span> : m.lipinski_pass === false ? <span className="text-red-400">\u2718</span> : '-'}</td>
                      <td className="py-2 text-xs text-gray-500">{m.source}</td>
                      <td className="py-2"><StatusBadge status={getStatus(m)} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {tab === 'add' && (
        <Card title="Adicionar Molecula (SMILES)">
          <form onSubmit={addSmiles} className="space-y-4 max-w-lg">
            <div><label className="block text-sm text-gray-400 mb-1">Nome</label><input className={inputCls} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /></div>
            <div><label className="block text-sm text-gray-400 mb-1">SMILES</label><input className={inputCls} placeholder="Ex: c1ccc2ncccc2c1" value={form.smiles} onChange={e => setForm({ ...form, smiles: e.target.value })} required /></div>
            <div><label className="block text-sm text-gray-400 mb-1">Proteina Alvo</label>
              <select className={inputCls} value={form.target_protein_id} onChange={e => setForm({ ...form, target_protein_id: e.target.value })}>
                <option value="">Nenhuma</option>{proteins.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <button type="submit" disabled={loading} className={btnCls}>{loading ? 'Salvando...' : 'Adicionar'}</button>
          </form>
        </Card>
      )}

      {tab === 'csv' && (
        <Card title="Importar CSV">
          <form onSubmit={uploadCsv} className="space-y-4 max-w-lg">
            <div><label className="block text-sm text-gray-400 mb-1">Arquivo CSV</label><input id="csv-file" type="file" accept=".csv" className={inputCls} required />
              <p className="text-xs text-gray-600 mt-1">Colunas: name/nome, smiles/SMILES</p></div>
            <button type="submit" disabled={loading} className={btnCls}>{loading ? 'Importando...' : 'Importar'}</button>
          </form>
        </Card>
      )}

      {tab === 'generate' && (
        <div className="space-y-6">
          <Card title="Gerar Novas Moleculas com IA">
            <form onSubmit={generateMolecules} className="space-y-4 max-w-lg">
              <div><label className="block text-sm text-gray-400 mb-1">SMILES Semente</label>
                <input className={inputCls} placeholder="Ex: COc1cc(NC(C)CCCN(CC)CC)c2ncccc2c1" value={genForm.seed_smiles} onChange={e => setGenForm({ ...genForm, seed_smiles: e.target.value })} required />
                <p className="text-xs text-gray-600 mt-1">Molecula base para geracao de analogos</p></div>
              <div><label className="block text-sm text-gray-400 mb-1">Quantidade</label>
                <input type="number" min="1" max="50" className={inputCls} value={genForm.n_molecules} onChange={e => setGenForm({ ...genForm, n_molecules: e.target.value })} /></div>
              <div><label className="block text-sm text-gray-400 mb-1">Proteina Alvo</label>
                <select className={inputCls} value={genForm.target_protein_id} onChange={e => setGenForm({ ...genForm, target_protein_id: e.target.value })}>
                  <option value="">Nenhuma</option>{proteins.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select></div>
              <button type="submit" disabled={loading} className={btnCls}>{loading ? 'Gerando (SwissADME)...' : 'Gerar Moleculas'}</button>
            </form>
          </Card>
          {genResults && (
            <Card title={`Moleculas Geradas (${genResults.count})`}>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="text-left text-gray-500 border-b border-navy-600/50">
                    <th className="pb-2">#</th><th className="pb-2">SMILES</th><th className="pb-2">Estrategia</th><th className="pb-2">MW</th><th className="pb-2">LogP</th><th className="pb-2">Lipinski</th><th className="pb-2">SwissADME</th>
                  </tr></thead>
                  <tbody>{genResults.molecules.map((m, i) => (
                    <tr key={i} className="border-b border-navy-600/20">
                      <td className="py-2 text-gray-400">{i + 1}</td>
                      <td className="py-2 text-xs text-gray-300 max-w-[300px] truncate" title={m.smiles}>{m.smiles}</td>
                      <td className="py-2 text-xs text-gray-500">{m.strategy}</td>
                      <td className="py-2 text-gray-300">{m.validation?.molecular_weight?.toFixed(1) || '-'}</td>
                      <td className="py-2 text-gray-300">{m.validation?.logp?.toFixed(2) || '-'}</td>
                      <td className="py-2">{m.validation?.lipinski_pass ? <span className="text-accent-green">\u2714</span> : <span className="text-red-400">\u2718</span>}</td>
                      <td className="py-2">{m.swissadme?.success ? <span className="text-accent-cyan text-xs">\u2714 Verificado</span> : <span className="text-gray-600 text-xs">Local</span>}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
