/**
 * Radar Chart estilo SwissADME.
 * 6 eixos: LIPO, SIZE, POLAR, INSOLU, INSATU, FLEX
 * Area rosa = zona ideal de drug-likeness
 * Area vermelha = valores da molecula
 */
export default function RadarChart({ data, size = 250 }) {
  if (!data) return null

  const axes = [
    { key: 'lipo', label: 'LIPO', min: -0.7, max: 5.0 },
    { key: 'size', label: 'SIZE', min: 150, max: 500 },
    { key: 'polar', label: 'POLAR', min: 20, max: 130 },
    { key: 'insolu', label: 'INSOLU', min: 0, max: 6 },
    { key: 'insatu', label: 'INSATU', min: 0.25, max: 1.0 },
    { key: 'flex', label: 'FLEX', min: 0, max: 9 },
  ]

  // Zona ideal (area rosa do SwissADME)
  const idealZone = [
    { lipo: [-0.7, 5.0], size: [150, 500], polar: [20, 130], insolu: [0, 6], insatu: [0.25, 1.0], flex: [0, 9] },
  ]

  const cx = size / 2
  const cy = size / 2
  const r = size * 0.35
  const n = axes.length

  function angleFor(i) {
    return (Math.PI * 2 * i) / n - Math.PI / 2
  }

  function pointAt(i, value, axis) {
    const range = axis.max - axis.min
    const norm = Math.max(0, Math.min(1, (value - axis.min) / (range || 1)))
    const angle = angleFor(i)
    return {
      x: cx + r * norm * Math.cos(angle),
      y: cy + r * norm * Math.sin(angle),
    }
  }

  // Grid circles
  const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0]

  // Pontos da molecula
  const molPoints = axes.map((axis, i) => {
    const val = data[axis.key] ?? 0
    return pointAt(i, val, axis)
  })
  const molPath = molPoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ') + ' Z'

  // Pontos da zona ideal (min e max)
  const idealMinPoints = axes.map((axis, i) => pointAt(i, axis.min, axis))
  const idealMaxPoints = axes.map((axis, i) => pointAt(i, axis.max, axis))
  const idealPath = idealMaxPoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ') + ' Z'

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background */}
        <circle cx={cx} cy={cy} r={r} fill="#1C2541" stroke="#253b5e" strokeWidth="0.5" />

        {/* Grid */}
        {gridLevels.map(level => (
          <polygon key={level}
            points={axes.map((_, i) => {
              const angle = angleFor(i)
              return `${cx + r * level * Math.cos(angle)},${cy + r * level * Math.sin(angle)}`
            }).join(' ')}
            fill="none" stroke="#253b5e" strokeWidth="0.5" />
        ))}

        {/* Axis lines */}
        {axes.map((_, i) => {
          const angle = angleFor(i)
          return (
            <line key={i}
              x1={cx} y1={cy}
              x2={cx + r * Math.cos(angle)} y2={cy + r * Math.sin(angle)}
              stroke="#253b5e" strokeWidth="0.5" />
          )
        })}

        {/* Zona ideal (area rosa) */}
        <polygon points={idealPath} fill="#f472b6" fillOpacity="0.1" stroke="#f472b6" strokeWidth="1" strokeDasharray="4,2" />

        {/* Molecula (area vermelha) */}
        <polygon points={molPoints.map(p => `${p.x},${p.y}`).join(' ')}
          fill="#ef4444" fillOpacity="0.25" stroke="#ef4444" strokeWidth="1.5" />

        {/* Pontos da molecula */}
        {molPoints.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="3" fill="#ef4444" stroke="#fff" strokeWidth="0.5" />
        ))}

        {/* Labels */}
        {axes.map((axis, i) => {
          const angle = angleFor(i)
          const lx = cx + (r + 18) * Math.cos(angle)
          const ly = cy + (r + 18) * Math.sin(angle)
          return (
            <text key={i} x={lx} y={ly}
              textAnchor="middle" dominantBaseline="middle"
              fill="#94a3b8" fontSize="9" fontWeight="500">
              {axis.label}
            </text>
          )
        })}
      </svg>
    </div>
  )
}

/**
 * Calcula os valores do radar a partir dos dados ADME
 */
export function calcRadarData(adme) {
  if (!adme) return null

  const pc = adme.physicochemical || {}
  const lp = adme.lipophilicity || {}
  const sol = adme.solubility || {}

  return {
    lipo: lp.consensus_logp ?? lp.xlogp3 ?? pc.logp ?? 0,
    size: pc.molecular_weight ?? 0,
    polar: pc.tpsa ?? 0,
    insolu: Math.abs(sol.log_s_esol ?? 0),
    insatu: pc.fraction_csp3 ?? 0.5,
    flex: pc.num_rotatable_bonds ?? 0,
  }
}
