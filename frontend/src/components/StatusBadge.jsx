export default function StatusBadge({ status }) {
  const config = {
    valid: { text: 'Valido', bg: 'bg-green-100 text-green-800', icon: '\u2714' },
    warning: { text: 'Atencao', bg: 'bg-yellow-100 text-yellow-800', icon: '\u26A0' },
    invalid: { text: 'Invalido', bg: 'bg-red-100 text-red-800', icon: '\u2718' },
    pending: { text: 'Pendente', bg: 'bg-gray-100 text-gray-600', icon: '\u25CB' },
  }

  const c = config[status] || config.pending
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${c.bg}`}>
      {c.icon} {c.text}
    </span>
  )
}
