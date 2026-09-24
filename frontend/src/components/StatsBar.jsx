function fmt(n, prefix = '', suffix = '') {
  if (n == null) return '—'
  if (n >= 1_000_000) return `${prefix}${(n / 1_000_000).toFixed(2)}M${suffix}`
  if (n >= 1_000)     return `${prefix}${(n / 1_000).toFixed(1)}K${suffix}`
  return `${prefix}${n.toLocaleString()}${suffix}`
}

export default function StatsBar({ stats, loading }) {
  const items = [
    { label: 'Invoices Processed', value: loading ? '...' : (stats.total_invoices ?? '—') },
    { label: 'Total Spend (USD)',   value: loading ? '...' : fmt(stats.total_spend_usd, '$') },
    { label: 'Average PUE',         value: loading ? '...' : (stats.avg_pue?.toFixed(3) ?? '—') },
    { label: 'Energy Consumed',     value: loading ? '...' : fmt(stats.total_kwh, '', ' kWh') },
    { label: 'Currencies',          value: loading ? '...' : (stats.currencies?.length ?? '—') },
  ]

  return (
    <div className="border-y border-white/5 bg-[#0f1729]/40">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-center gap-0 divide-x divide-white/5 flex-wrap">
          {items.map((item, i) => (
            <div key={i} className="px-8 py-4 text-center">
              <div className="text-xl font-bold text-slate-100">{item.value}</div>
              <div className="text-xs text-slate-500 uppercase tracking-wide mt-0.5">{item.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
