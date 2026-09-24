import { useEffect } from 'react'

function Field({ label, value, mono = false }) {
  return (
    <div>
      <div className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">{label}</div>
      <div className={`text-sm text-slate-200 ${mono ? 'font-mono text-indigo-400' : ''}`}>
        {value ?? <span className="text-slate-600">—</span>}
      </div>
    </div>
  )
}

export default function InvoiceModal({ invoice: inv, onClose }) {
  // Close on Escape
  useEffect(() => {
    const handler = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-[#0f1729] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">

        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-white/5">
          <div>
            <h2 className="text-base font-bold text-slate-100">{inv.vendor || 'Invoice Detail'}</h2>
            <p className="text-xs text-indigo-400 font-mono mt-0.5">{inv.invoice_number}</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 hover:text-slate-200 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">

          {/* Core fields */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Invoice Details</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <Field label="Invoice Date"   value={inv.invoice_date} />
              <Field label="Period"         value={inv.period} />
              <Field label="Currency"       value={inv.currency} />
              <Field label="Location"       value={inv.city && inv.country ? `${inv.city}, ${inv.country}` : null} />
              <Field label="Invoice Number" value={inv.invoice_number} mono />
            </div>
          </div>

          {/* Financial */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Financial</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">Total Amount</div>
                <div className="text-lg font-bold text-slate-100">
                  {inv.total_amount?.toLocaleString(undefined, { maximumFractionDigits: 2 }) ?? '—'}
                  {inv.currency && <span className="text-sm font-normal text-slate-500 ml-1">{inv.currency}</span>}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">Total (USD)</div>
                <div className="text-lg font-bold text-emerald-400">
                  {inv.total_amount_usd ? `$${inv.total_amount_usd.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '—'}
                </div>
              </div>
              <Field label="Tax Amount"  value={inv.tax_amount?.toLocaleString()} />
              <Field label="USD Rate"    value={inv.usd_rate ? `1 USD = ${inv.usd_rate} ${inv.currency}` : null} />
            </div>
          </div>

          {/* Energy */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Energy & PUE</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <Field label="Volume (kWh)"   value={inv.total_volume_kwh?.toLocaleString()} />
              <Field label="Base Rate"      value={inv.base_rate ? `${inv.base_rate} ${inv.currency}/kWh` : null} />
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">Current PUE</div>
                <div className={`text-lg font-bold ${
                  inv.pue_cap && inv.current_pue > inv.pue_cap ? 'text-red-400' : 'text-emerald-400'
                }`}>
                  {inv.current_pue?.toFixed(3) ?? '—'}
                </div>
              </div>
              <Field label="PUE Cap"   value={inv.pue_cap?.toFixed(3)} />
              {inv.pue_cap && inv.current_pue && (
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">PUE Status</div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-md ${
                    inv.current_pue > inv.pue_cap
                      ? 'bg-red-500/15 text-red-400'
                      : 'bg-emerald-500/15 text-emerald-400'
                  }`}>
                    {inv.current_pue > inv.pue_cap ? '⚠ Exceeds Cap' : '✓ Within Cap'}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Warnings */}
          {inv.data_quality_warnings?.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-amber-500 uppercase tracking-widest mb-3">Data Quality Warnings</h3>
              <div className="space-y-2">
                {inv.data_quality_warnings.map((w, i) => (
                  <div key={i} className="flex gap-2 p-3 rounded-xl bg-amber-500/8 border border-amber-500/15 text-xs text-amber-400">
                    <span>⚠</span>
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Pipeline meta */}
          <div className="pt-4 border-t border-white/5">
            <div className="flex flex-wrap gap-4 text-xs text-slate-600">
              <span>Processed: {inv.processed_at ? new Date(inv.processed_at).toLocaleString() : '—'}</span>
              <span>Pipeline: v{inv.pipeline_version}</span>
              <span>Model: {inv.bedrock_model_used}</span>
              <span>Duration: {inv.processing_duration_ms}ms</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
