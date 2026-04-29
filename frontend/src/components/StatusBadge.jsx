export default function StatusBadge({ status }) {
  const config = {
    valid: { text: 'Valido', bg: 'bg-accent-green/15 text-accent-green border-accent-green/20', icon: '\u2714' },
    warning: { text: 'Atencao', bg: 'bg-yellow-400/15 text-yellow-400 border-yellow-400/20', icon: '\u26A0' },
    invalid: { text: 'Invalido', bg: 'bg-red-400/15 text-red-400 border-red-400/20', icon: '\u2718' },
    pending: { text: 'Pendente', bg: 'bg-gray-500/15 text-gray-400 border-gray-500/20', icon: '\u25CB' },
  }

  const c = config[status] || config.pending
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${c.bg}`}>
      {c.icon} {c.text}
    </span>
  )
}
