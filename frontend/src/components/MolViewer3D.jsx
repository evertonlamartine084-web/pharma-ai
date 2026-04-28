import { useEffect, useRef } from 'react'

export default function MolViewer3D({ pdbData, height = 400 }) {
  const containerRef = useRef(null)
  const viewerRef = useRef(null)

  useEffect(() => {
    if (!pdbData || !containerRef.current || !window.$3Dmol) return

    if (viewerRef.current) {
      viewerRef.current.clear()
    }

    const viewer = window.$3Dmol.createViewer(containerRef.current, {
      backgroundColor: '#f8fafc',
    })
    viewerRef.current = viewer

    viewer.addModel(pdbData, 'pdb')
    viewer.setStyle({}, { cartoon: { color: 'spectrum' } })
    viewer.addSurface(window.$3Dmol.SurfaceType.VDW, {
      opacity: 0.15,
      color: '#6366f1',
    })
    viewer.zoomTo()
    viewer.render()

    return () => {
      if (viewerRef.current) {
        viewerRef.current.clear()
        viewerRef.current = null
      }
    }
  }, [pdbData])

  if (!pdbData) {
    return (
      <div
        className="flex items-center justify-center bg-gray-100 rounded-lg border-2 border-dashed border-gray-300"
        style={{ height }}
      >
        <p className="text-gray-400">Nenhum dado PDB disponivel para visualizacao</p>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="rounded-lg border border-gray-200 overflow-hidden"
      style={{ height, position: 'relative' }}
    />
  )
}
