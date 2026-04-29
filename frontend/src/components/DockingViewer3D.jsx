import { useEffect, useRef, useState } from 'react'
import { createViewer, SurfaceType } from '3dmol/build/3Dmol.es6.js'

export default function DockingViewer3D({ proteinPdb, ligandSdf, activeSiteResidues = [], height = 500 }) {
  const containerRef = useRef(null)
  const viewerRef = useRef(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!containerRef.current) return
    if (!proteinPdb && !ligandSdf) return

    const el = containerRef.current
    el.innerHTML = ''

    try {
      const viewer = createViewer(el, {
        backgroundColor: '#0f172a',
        antialias: true,
      })
      viewerRef.current = viewer

      if (proteinPdb) {
        viewer.addModel(proteinPdb, 'pdb')

        viewer.setStyle({ model: 0 }, {
          cartoon: { color: '#64748b', opacity: 0.6 }
        })

        if (activeSiteResidues.length > 0) {
          viewer.setStyle(
            { model: 0, resi: activeSiteResidues },
            {
              cartoon: { color: '#f59e0b' },
              stick: { color: '#f59e0b', radius: 0.15 },
            }
          )

          viewer.addSurface(SurfaceType.VDW, {
            opacity: 0.15,
            color: '#fbbf24',
          }, { model: 0, resi: activeSiteResidues })
        }
      }

      if (ligandSdf) {
        viewer.addModel(ligandSdf, 'sdf')
        viewer.setStyle(
          { model: -1 },
          {
            stick: { radius: 0.25, colorscheme: 'greenCarbon' },
            sphere: { scale: 0.3, colorscheme: 'greenCarbon' },
          }
        )
      }

      viewer.zoomTo()

      if (proteinPdb && activeSiteResidues.length > 0) {
        viewer.zoomTo({ resi: activeSiteResidues })
        viewer.zoom(0.7)
      }

      viewer.render()
      setError(null)
    } catch (e) {
      console.error('Erro ao renderizar 3D:', e)
      setError('Erro ao renderizar: ' + e.message)
    }

    return () => {
      if (viewerRef.current) {
        try { viewerRef.current.clear() } catch (_) {}
        viewerRef.current = null
      }
    }
  }, [proteinPdb, ligandSdf, JSON.stringify(activeSiteResidues)])

  const hasData = proteinPdb || ligandSdf

  if (!hasData) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border-2 border-dashed border-gray-600"
        style={{ height, backgroundColor: '#0f172a' }}
      >
        <div className="text-center">
          <p className="text-gray-400">Selecione uma proteina com dados PDB para visualizar o docking</p>
          <p className="text-gray-500 text-xs mt-1">Use AlphaFold ou upload de PDB na pagina de Proteinas</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative">
      {error && (
        <div className="absolute top-2 left-2 z-10 bg-red-900/80 text-red-200 text-xs px-3 py-1 rounded">
          {error}
        </div>
      )}
      <div
        ref={containerRef}
        className="rounded-lg overflow-hidden border border-gray-700"
        style={{ height, width: '100%', position: 'relative' }}
      />
      <div className="absolute bottom-3 left-3 flex gap-2 z-10">
        {proteinPdb && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-gray-800/90 text-gray-300">
            <span className="w-2 h-2 rounded-full bg-slate-400 inline-block" /> Proteina
          </span>
        )}
        {activeSiteResidues.length > 0 && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-gray-800/90 text-gray-300">
            <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" /> Sitio Ativo ({activeSiteResidues.length} residuos)
          </span>
        )}
        {ligandSdf && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-gray-800/90 text-gray-300">
            <span className="w-2 h-2 rounded-full bg-green-400 inline-block" /> Ligante
          </span>
        )}
      </div>
    </div>
  )
}
