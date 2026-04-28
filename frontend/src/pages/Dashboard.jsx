import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { proteinApi, moleculeApi, analysisApi } from '../services/api'
import Card, { StatCard } from '../components/Card'

export default function Dashboard() {
  const [stats, setStats] = useState({ proteins: 0, molecules: 0, analyses: 0, valid: 0, invalid: 0 })
  const [loading, setLoading] = useState(true)
  const [seeding, setSeeding] = useState(false)

  useEffect(() => { loadStats() }, [])

  async function loadStats() {
    try {
      const [proteins, molecules, analyses] = await Promise.all([
        proteinApi.list(),
        moleculeApi.list(),
        analysisApi.list(),
      ])
      const mols = molecules.data
      setStats({
        proteins: proteins.data.length,
        molecules: mols.length,
        analyses: analyses.data.length,
        valid: mols.filter(m => m.is_valid === true).length,
        invalid: mols.filter(m => m.is_valid === false).length,
      })
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  async function seedData() {
    setSeeding(true)
    try {
      await Promise.all([proteinApi.seedLeishmania(), moleculeApi.seed()])
      await loadStats()
    } catch (e) {
      console.error(e)
    }
    setSeeding(false)
  }

  if (loading) return <p className="text-center py-10 text-gray-400">Carregando...</p>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Plataforma de descoberta de farmacos - Leishmaniose</p>
        </div>
        {stats.proteins === 0 && stats.molecules === 0 && (
          <button
            onClick={seedData}
            disabled={seeding}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {seeding ? 'Populando...' : 'Inicializar Banco de Dados'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="Proteinas" value={stats.proteins} color="primary" />
        <StatCard label="Moleculas" value={stats.molecules} color="primary" />
        <StatCard label="Analises" value={stats.analyses} color="primary" />
        <StatCard label="Validas" value={stats.valid} color="green" />
        <StatCard label="Invalidas" value={stats.invalid} color="red" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Pipeline de Descoberta">
          <div className="space-y-3">
            {[
              { step: '1', label: 'Input de proteina (PDB/FASTA)', desc: 'Upload ou AlphaFold' },
              { step: '2', label: 'Input de moleculas (SMILES)', desc: 'Manual, CSV ou banco' },
              { step: '3', label: 'Geracao de novas moleculas (IA)', desc: 'Mutacao, fusao, scaffold hop' },
              { step: '4', label: 'Validacao quimica (RDKit)', desc: 'Lipinski, peso molecular, logP' },
              { step: '5', label: 'Avaliacao ADME', desc: 'Solubilidade, permeabilidade, drug-likeness' },
              { step: '6', label: 'Docking molecular', desc: 'Binding affinity, interacoes' },
            ].map(item => (
              <div key={item.step} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-7 h-7 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">
                  {item.step}
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-800">{item.label}</p>
                  <p className="text-xs text-gray-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Acoes Rapidas">
          <div className="grid grid-cols-2 gap-3">
            <Link to="/proteins" className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors text-center">
              <p className="font-medium text-gray-700">Proteinas</p>
              <p className="text-xs text-gray-400 mt-1">Upload PDB / FASTA</p>
            </Link>
            <Link to="/molecules" className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors text-center">
              <p className="font-medium text-gray-700">Moleculas</p>
              <p className="text-xs text-gray-400 mt-1">SMILES / Gerar IA</p>
            </Link>
            <Link to="/analysis" className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors text-center">
              <p className="font-medium text-gray-700">Validacao</p>
              <p className="text-xs text-gray-400 mt-1">RDKit + ADME</p>
            </Link>
            <Link to="/analysis" className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors text-center">
              <p className="font-medium text-gray-700">Docking</p>
              <p className="text-xs text-gray-400 mt-1">Interacao molecular</p>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  )
}
