import { useState } from 'react'

const CURRENCY_COLORS = {
  EUR: 'bg-indigo-500/10 text-indigo-400',
  GBP: 'bg-sky-500/10 text-sky-400',
  CHF: 'bg-emerald-500/10 text-emerald-400',
  USD: 'bg-amber-500/10 text-amber-400',
}

function PueBadge({ pue, cap }) {
  if (pue == null) return <span className="text-slate-600">—</span>
  const exceeded = cap != null && pue > cap
  return (
    <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-semibold ${
      exceeded ? 'bg-red-500/15 text-red-400' : 'bg-emerald-500/15 text-emerald-400'
    }`}>
      {pue.toFixed(3)}
    </span>
  )
}

const VENDOR_COLORS = ['#6366f1','#38bdf8','#8b5cf6','#10b981','#f59e0b','#ec4899']

export default function InvoiceTable({ invoices, loading, onSelect }) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('period')
  const [sortDir, setSortDir] = useState('desc')

  function toggleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const filtered = invoices
    .filter(inv => {
      if (!search) return true
      const q = search.toLowerCase()
      return (
        inv.vendor?.toLowerCase().includes(q) ||
        inv.invoice_number?.toLowerCase().includes(q) ||
        inv.period?.includes(q) ||
        inv.currency?.includes(q.toUpperCase())
      )
    })
    .sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      return sortDir === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av))
    })

  function SortIcon({ k }) {
    if (sortKey !== k) return <span className="text-slate-700 ml-1">↕</span>
    return <span className="text-indigo-400 ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  return (
    <div className="bg-[#0f1729] border border-white/5 rounded-2xl p-6 mb-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Invoice Records</h3>
          <p className="text-xs text-slate-500 mt-0.5">Click any row for full details</p>
        </div>
        <div className="flex items-center gap-2 bg-white/5 border border-white/8 rounded-xl px-3 py-2 w-64">
          <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            className="bg-transparent text-sm text-slate-300 placeholder-slate-600 outline-none w-full"
            placeholder="Search invoices..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="py-16 text-center text-slate-600 text-sm">Loading invoices...</div>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center text-slate-600 text-sm">
          {invoices.length === 0 ? 'No invoices processed yet. Upload one to get started.' : 'No results match your search.'}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5">
                {[
                  { key: 'vendor',           label: 'Vendor' },
                  { key: 'invoice_number',   label: 'Invoice No' },
                  { key: 'period',           label: 'Period' },
                  { key: 'currency',         label: 'Currency' },
                  { key: 'total_amount',     label: 'Amount (Local)' },
                  { key: 'total_amount_usd', label: 'Amount (USD)' },
                  { key: 'total_volume_kwh', label: 'kWh' },
                  { key: 'current_pue',      label: 'PUE' },
                ].map(col => (
                  <th
                    key={col.key}
                    className="pb-3 px-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide cursor-pointer hover:text-slate-300 whitespace-nowrap"
                    onClick={() => toggleSort(col.key)}
                  >
                    {col.label}<SortIcon k={col.key} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((inv, i) => (
                <tr
                  key={inv.invoice_number || i}
                  onClick={() => onSelect(inv)}
                  className="border-b border-white/3 hover:bg-indigo-500/5 cursor-pointer transition-colors"
                >
                  <td className="py-3.5 px-3">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ background: VENDOR_COLORS[i % VENDOR_COLORS.length] }}
                      />
                      <span className="text-slate-200 font-medium truncate max-w-[160px]">
                        {inv.vendor || '—'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-3 text-indigo-400 font-mono text-xs">
                    {inv.invoice_number || '—'}
                  </td>
                  <td className="py-3.5 px-3 text-slate-300">{inv.period || '—'}</td>
                  <td className="py-3.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${CURRENCY_COLORS[inv.currency] || 'bg-slate-500/10 text-slate-400'}`}>
                      {inv.currency || '—'}
                    </span>
                  </td>
                  <td className="py-3.5 px-3 text-slate-300">
                    {inv.total_amount != null
                      ? inv.total_amount.toLocaleString(undefined, { maximumFractionDigits: 0 })
                      : '—'}
                  </td>
                  <td className="py-3.5 px-3 text-slate-100 font-semibold">
                    {inv.total_amount_usd != null
                      ? `$${inv.total_amount_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                      : '—'}
                  </td>
                  <td className="py-3.5 px-3 text-slate-300">
                    {inv.total_volume_kwh != null
                      ? inv.total_volume_kwh.toLocaleString(undefined, { maximumFractionDigits: 0 })
                      : '—'}
                  </td>
                  <td className="py-3.5 px-3">
                    <PueBadge pue={inv.current_pue} cap={inv.pue_cap} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
