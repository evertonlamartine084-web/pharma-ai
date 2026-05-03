import { useEffect, useRef } from 'react'
import { createViewer, SurfaceType } from '3dmol/build/3Dmol.es6.js'

export default function MolViewer3D({ pdbData, height = 400 }) {
  const containerRef = useRef(null)
  const viewerRef = useRef(null)

  useEffect(() => {
    if (!pdbData || !containerRef.current) return

    const el = containerRef.current
    el.innerHTML = ''

    try {
      const viewer = createViewer(el, {
        backgroundColor: '#0f172a',
        antialias: true,
      })
      viewerRef.current = viewer

      viewer.addModel(pdbData, 'pdb')

      const isProtein = pdbData.includes('\nATOM  ')
      if (isProtein) {
        viewer.setStyle({}, { cartoon: { color: 'spectrum' } })
        viewer.addSurface(SurfaceType.VDW, { opacity: 0.15, color: '#6366f1' })
      } else {
        viewer.setStyle({}, {
          stick: { radius: 0.2, colorscheme: 'cyanCarbon' },
          sphere: { scale: 0.3, colorscheme: 'cyanCarbon' },
        })
        viewer.addSurface(SurfaceType.VDW, { opacity: 0.15, color: '#22D3EE' })
      }
      viewer.zoomTo()
      viewer.render()
    } catch (e) {
      console.error('Erro ao renderizar 3D:', e)
    }

    return () => {
      if (viewerRef.current) {
        try { viewerRef.current.clear() } catch (_) {}
        viewerRef.current = null
      }
    }
  }, [pdbData])

  if (!pdbData) {
    return (
      <div
        className="flex items-center justify-center bg-navy-700/30 rounded-lg border-2 border-dashed border-navy-600/50"
        style={{ height }}
      >
        <p className="text-gray-600">Nenhum dado PDB disponivel para visualizacao</p>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="rounded-lg border border-navy-600/50 overflow-hidden"
      style={{ height, width: '100%', position: 'relative' }}
    />
  )
}
