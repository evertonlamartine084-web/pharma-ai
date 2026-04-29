export default function Card({ title, children, className = '', actions }) {
  return (
    <div className={`bg-navy-800 rounded-xl border border-navy-600/50 ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-navy-600/50">
          {title && <h3 className="font-semibold text-white text-sm">{title}</h3>}
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  )
}

export function StatCard({ label, value, sub, color = 'cyan' }) {
  const colors = {
    cyan: 'text-accent-cyan',
    green: 'text-accent-green',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
  }
  return (
    <div className="bg-navy-800 rounded-xl border border-navy-600/50 p-5">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${colors[color]}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-600 mt-1">{sub}</p>}
    </div>
  )
}
