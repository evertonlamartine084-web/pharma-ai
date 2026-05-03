import { useState, useEffect } from 'react'
import { proteinApi } from '../services/api'
import Card from '../components/Card'
import MolViewer3D from '../components/MolViewer3D'
import { inputCls, btnCls, tabCls } from '../styles'

export default function Proteins() {
  const [proteins, setProteins] = useState([])
  const [selected, setSelected] = useState(null)
  const [pdbData, setPdbData] = useState(null)
  const [tab, setTab] = useState('list')
  const [form, setForm] = useState({ name: '', organism: 'Leishmania', sequence: '', uniprot_id: '', pdb_code: '' })
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => { loadProteins() }, [])

  async function loadProteins() {
    try { const res = await proteinApi.list(); setProteins(res.data) } catch (e) { console.error(e) }
  }

  async function selectProtein(p) {
    setSelected(p); setPdbData(null)
    if (p.pdb_data) { setPdbData(p.pdb_data) }
    else { try { const res = await proteinApi.getPdb(p.id); setPdbData(res.data.pdb_data) } catch (_) {} }
  }

  async function uploadPdb(e) {
    e.preventDefault()
    const fileInput = document.getElementById('pdb-file')
    if (!fileInput.files[0]) return
    setLoading(true)
    try { await proteinApi.uploadPdb(fileInput.files[0], form.name, form.organism); setMsg('Proteina carregada'); setTab('list'); loadProteins() }
    catch (e) { setMsg('Erro: ' + (e.response?.data?.detail || e.message)) }
    setLoading(false)
  }

  async function addSequence(e) {
    e.preventDefault(); setLoading(true)
    try { await proteinApi.addSequence({ name: form.name, sequence: form.sequence, organism: form.organism }); setMsg('Sequencia adicionada'); setTab('list'); loadProteins() }
    catch (e) { setMsg('Erro: ' + (e.response?.data?.detail || e.message)) }
    setLoading(false)
  }

  async function fetchAlphafold(e) {
    e.preventDefault(); setLoading(true)
    try { await proteinApi.fetchAlphafold({ uniprot_id: form.uniprot_id, name: form.name }); setMsg('Estrutura AlphaFold obtida'); setTab('list'); loadProteins() }
    catch (e) { setMsg('Erro: ' + (e.response?.data?.detail || e.message)) }
    setLoading(false)
  }

  async function fetchPdbCode(e) {
    e.preventDefault(); setLoading(true)
    try { await proteinApi.fetchPdb(form.pdb_code, form.name); setMsg(`Estrutura ${form.pdb_code.toUpperCase()} obtida do RCSB PDB`); setTab('list'); loadProteins() }
    catch (e) { setMsg('Erro: ' + (e.response?.data?.detail || e.message)) }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Alvo Molecular</h1>
        <div className="flex gap-2">
          {['list', 'upload', 'pdbfetch', 'alphafold'].map(t => (
            <button key={t} onClick={() => { setTab(t); setMsg('') }} className={tabCls(tab === t)}>
              {{ list: 'Lista', upload: 'Upload PDB', pdbfetch: 'Buscar PDB', alphafold: 'AlphaFold' }[t]}
            </button>
          ))}
        </div>
      </div>

      {msg && <div className="bg-accent-cyan/10 text-accent-cyan px-4 py-2 rounded-lg text-sm border border-accent-cyan/20">{msg}</div>}

      {tab === 'list' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title={`Proteinas (${proteins.length})`}>
            {proteins.length === 0 ? (
              <p className="text-gray-500 text-sm">Nenhuma proteina. Use "Inicializar Banco" no Dashboard.</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {proteins.map(p => (
                  <button key={p.id} onClick={() => selectProtein(p)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${selected?.id === p.id ? 'border-accent-cyan/40 bg-accent-cyan/5' : 'border-navy-600/30 hover:border-navy-500 bg-navy-700/30'}`}>
                    <p className="font-medium text-sm text-white">{p.name}</p>
                    <p className="text-xs text-gray-500">{p.organism} | Fonte: {p.source}</p>
                  </button>
                ))}
              </div>
            )}
          </Card>
          <Card title={selected ? selected.name : 'Visualizacao 3D'}>
            <MolViewer3D pdbData={pdbData} />
            {selected && (
              <div className="mt-4 text-sm text-gray-400 space-y-1">
                <p><span className="text-gray-300 font-medium">Organismo:</span> {selected.organism}</p>
                <p><span className="text-gray-300 font-medium">Fonte:</span> {selected.source}</p>
                {selected.sequence && <p><span className="text-gray-300 font-medium">Sequencia:</span> {selected.sequence.substring(0, 80)}...</p>}
              </div>
            )}
          </Card>
        </div>
      )}

      {tab === 'upload' && (
        <Card title="Upload de Arquivo PDB">
          <form onSubmit={uploadPdb} className="space-y-4 max-w-lg">
            <div><label className="block text-sm text-gray-400 mb-1">Nome</label><input className={inputCls} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /></div>
            <div><label className="block text-sm text-gray-400 mb-1">Organismo</label><input className={inputCls} value={form.organism} onChange={e => setForm({ ...form, organism: e.target.value })} /></div>
            <div><label className="block text-sm text-gray-400 mb-1">Arquivo PDB</label><input id="pdb-file" type="file" accept=".pdb" className={inputCls} required /></div>
            <button type="submit" disabled={loading} className={btnCls}>{loading ? 'Enviando...' : 'Upload'}</button>
          </form>
        </Card>
      )}

      {tab === 'sequence' && (
        <Card title="Adicionar Sequencia FASTA">
          <form onSubmit={addSequence} className="space-y-4 max-w-lg">
            <div><label className="block text-sm text-gray-400 mb-1">Nome da Proteina</label><input className={inputCls} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /></div>
            <div><label className="block text-sm text-gray-400 mb-1">Organismo</label><input className={inputCls} value={form.organism} onChange={e => setForm({ ...form, organism: e.target.value })} /></div>
            <div><label className="block text-sm text-gray-400 mb-1">Sequencia</label><textarea className={inputCls} rows={6} placeholder="MAQYDKLVIGAGAR..." value={form.sequence} onChange={e => setForm({ ...form, sequence: e.target.value })} required /></div>
            <button type="submit" disabled={loading} className={btnCls}>{loading ? 'Salvando...' : 'Adicionar'}</button>
          </form>
        </Card>
      )}

      {tab === 'pdbfetch' && (
        <Card title="Buscar Estrutura no RCSB Protein Data Bank">
          <form onSubmit={fetchPdbCode} className="space-y-4 max-w-lg">
            <div><label className="block text-sm text-gray-400 mb-1">Codigo PDB</label>
              <input className={inputCls} placeholder="Ex: 3EDJ, 1A2B, 6LU7" value={form.pdb_code} onChange={e => setForm({ ...form, pdb_code: e.target.value })} required maxLength={4} />
              <p className="text-xs text-gray-600 mt-1">Codigo de 4 caracteres do RCSB PDB (proteinas, acidos nucleicos, complexos)</p>
            </div>
            <div><label className="block text-sm text-gray-400 mb-1">Nome (opcional)</label><input className={inputCls} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
            <button type="submit" disabled={loading} className={btnCls}>{loading ? 'Buscando...' : 'Buscar no RCSB PDB'}</button>
            <p className="text-xs text-gray-600">Busca estrutura experimental (raio-X, cryo-EM) do Protein Data Bank (rcsb.org).</p>
          </form>
        </Card>
      )}

      {tab === 'alphafold' && (
        <Card title="Buscar Estrutura no AlphaFold">
          <form onSubmit={fetchAlphafold} className="space-y-4 max-w-lg">
            <div><label className="block text-sm text-gray-400 mb-1">UniProt ID</label><input className={inputCls} placeholder="Ex: Q01782" value={form.uniprot_id} onChange={e => setForm({ ...form, uniprot_id: e.target.value })} required /></div>
            <div><label className="block text-sm text-gray-400 mb-1">Nome (opcional)</label><input className={inputCls} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
            <button type="submit" disabled={loading} className={btnCls}>{loading ? 'Buscando...' : 'Buscar AlphaFold'}</button>
            <p className="text-xs text-gray-600">Busca a estrutura predita na base de dados do AlphaFold (EBI).</p>
          </form>
        </Card>
      )}
    </div>
  )
}
