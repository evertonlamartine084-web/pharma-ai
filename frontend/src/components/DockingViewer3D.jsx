import { useEffect, useRef, useState } from 'react'
import { createViewer, SurfaceType } from '3dmol/build/3Dmol.es6.js'

export default function DockingViewer3D({ proteinPdb, ligandSdf, activeSiteResidues = [], contacts3d = [], height = 500 }) {
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

        // Detectar se e proteina (ATOM) ou molecula pequena (HETATM)
        const isProtein = proteinPdb.includes('\nATOM  ')

        if (isProtein) {
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
        } else {
          // Molecula pequena como alvo: mostrar como stick + surface
          viewer.setStyle({ model: 0 }, {
            stick: { radius: 0.2, colorscheme: 'cyanCarbon' },
            sphere: { scale: 0.25, colorscheme: 'cyanCarbon', opacity: 0.5 },
          })
          viewer.addSurface(SurfaceType.VDW, {
            opacity: 0.12,
            color: '#22D3EE',
          }, { model: 0 })
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

        // Labels com simbolo do elemento em cada atomo do ligante
        const ligandModel = viewer.getModel()
        if (ligandModel) {
          const atoms = ligandModel.selectedAtoms({})
          atoms.forEach(atom => {
            if (atom.elem && atom.elem !== 'H') {
              const elemColors = { C: '#a3e635', O: '#ef4444', N: '#3b82f6', S: '#eab308', F: '#22d3ee', Cl: '#22d3ee', Br: '#a855f7', P: '#f97316' }
              viewer.addLabel(atom.elem, {
                position: { x: atom.x, y: atom.y, z: atom.z },
                backgroundColor: elemColors[atom.elem] || '#a3e635',
                backgroundOpacity: 0.8,
                fontColor: '#0B132B',
                fontSize: 9,
                fontOpacity: 1,
                showBackground: true,
                alignment: 'center',
              })
            }
          })
        }
      }

      // Labels nos atomos nao-H do alvo (so para moleculas pequenas)
      if (proteinPdb && !proteinPdb.includes('\nATOM  ')) {
        const targetModel = viewer.getModel(0)
        if (targetModel) {
          const atoms = targetModel.selectedAtoms({})
          atoms.forEach(atom => {
            if (atom.elem && atom.elem !== 'H') {
              const elemColors = { C: '#22d3ee', O: '#ef4444', N: '#3b82f6', S: '#eab308' }
              viewer.addLabel(atom.elem, {
                position: { x: atom.x, y: atom.y, z: atom.z },
                backgroundColor: elemColors[atom.elem] || '#64748b',
                backgroundOpacity: 0.6,
                fontColor: '#ffffff',
                fontSize: 8,
                showBackground: true,
                alignment: 'center',
              })
            }
          })
        }
      }

      // Desenhar linhas de interacao com distancias
      if (contacts3d && contacts3d.length > 0) {
        contacts3d.forEach(contact => {
          const color = contact.type === 'Ligacao de hidrogenio' ? '#f472b6' :
                        contact.type === 'Interacao hidrofobica' ? '#fbbf24' : '#94a3b8'

          // Linha tracejada entre alvo e ligante
          viewer.addLine({
            start: contact.target_pos,
            end: contact.ligand_pos,
            color: color,
            dashed: true,
            dashLength: 0.15,
            gapLength: 0.1,
          })

          // Label com distancia
          const midX = (contact.target_pos.x + contact.ligand_pos.x) / 2
          const midY = (contact.target_pos.y + contact.ligand_pos.y) / 2
          const midZ = (contact.target_pos.z + contact.ligand_pos.z) / 2

          viewer.addLabel(`${contact.distance}\u00C5`, {
            position: { x: midX, y: midY, z: midZ },
            backgroundColor: color,
            backgroundOpacity: 0.7,
            fontColor: '#ffffff',
            fontSize: 10,
            showBackground: true,
          })
        })
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
  }, [proteinPdb, ligandSdf, JSON.stringify(activeSiteResidues), JSON.stringify(contacts3d)])

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
