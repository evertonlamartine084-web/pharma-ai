import { useState, useEffect } from 'react'

export default function MolStructure2D({ smiles, width = 350, height = 250 }) {
  const [svg, setSvg] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!smiles) return
    setSvg(null)
    setError(false)

    const API_URL = import.meta.env.VITE_API_URL || '/api'
    const url = `${API_URL}/molecules/render-svg?smiles=${encodeURIComponent(smiles)}&width=${width}&height=${height}`

    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error()
        return res.text()
      })
      .then(data => setSvg(data))
      .catch(() => setError(true))
  }, [smiles, width, height])

  if (!smiles) return null

  if (error) {
    return (
      <div className="flex items-center justify-center bg-navy-700/30 rounded-lg border border-navy-600/50" style={{ width, height }}>
        <p className="text-gray-600 text-xs">Erro ao renderizar estrutura</p>
      </div>
    )
  }

  if (!svg) {
    return (
      <div className="flex items-center justify-center bg-navy-700/30 rounded-lg border border-navy-600/50 animate-pulse" style={{ width, height }}>
        <p className="text-gray-600 text-xs">Renderizando...</p>
      </div>
    )
  }

  return (
    <div
      className="bg-white rounded-lg border border-navy-600/50 flex items-center justify-center"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}
