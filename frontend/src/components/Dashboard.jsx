import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from 'recharts'

const COLORS = ['#6366f1','#38bdf8','#10b981','#f59e0b','#ec4899','#8b5cf6']

function Card({ children, className = '' }) {
  return (
    <div className={`bg-[#0f1729] border border-white/5 rounded-2xl p-6 ${className}`}>
      {children}
    </div>
  )
}

function CardTitle({ title, subtitle }) {
  return (
    <div className="mb-5">
      <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
    </div>
  )
}

function KpiCard({ icon, label, value, sub, color, badge, badgeColor }) {
  const colorMap = {
    indigo: 'from-indigo-500 to-violet-600',
    blue:   'from-sky-400 to-blue-500',
    green:  'from-emerald-400 to-teal-500',
    amber:  'from-amber-400 to-orange-500',
  }
  const borderMap = {
    indigo: 'before:from-indigo-500 before:to-violet-600',
    blue:   'before:from-sky-400 before:to-blue-500',
    green:  'before:from-emerald-400 before:to-teal-500',
    amber:  'before:from-amber-400 before:to-orange-500',
  }
  const iconBg = {
    indigo: 'bg-indigo-500/15',
    blue:   'bg-sky-400/15',
    green:  'bg-emerald-400/15',
    amber:  'bg-amber-400/15',
  }

  return (
    <div className="relative bg-[#0f1729] border border-white/5 rounded-2xl p-6 overflow-hidden">
      {/* top accent bar */}
      <div className={`absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r ${colorMap[color]}`} />
      <div className={`w-10 h-10 rounded-xl ${iconBg[color]} flex items-center justify-center text-xl mb-4`}>
        {icon}
      </div>
      <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-3xl font-bold tracking-tight text-slate-100">{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
      {badge && (
        <div className={`absolute top-5 right-5 text-xs font-semibold px-2 py-0.5 rounded-md ${badgeColor}`}>
          {badge}
        </div>
      )}
    </div>
  )
}

function CustomTooltip({ active, payload, label, prefix = '' }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#1e2a3a] border border-white/10 rounded-xl px-4 py-3 text-xs shadow-xl">
      <div className="text-slate-400 mb-1">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="text-slate-100 font-semibold">
          {prefix}{typeof p.value === 'number' ? p.value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : p.value}
        </div>
      ))}
    </div>
  )
}

export default function Dashboard({ stats, loading }) {
  const byVendor   = stats.by_vendor   || []
  const byPeriod   = stats.by_period   || []
  const byCurrency = stats.by_currency || []

  const fmtUSD = v => v >= 1000 ? `$${(v/1000).toFixed(0)}K` : `$${v}`

  return (
    <div className="space-y-6 mb-8">
      {/* Section title */}
      <div className="text-xs font-semibold text-indigo-400 uppercase tracking-widest">
        📊 Analytics Overview
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon="💰" color="indigo" label="Total Spend"
          value={loading ? '...' : stats.total_spend_usd
          ? stats.total_spend_usd >= 1_000_000
            ? `$${(stats.total_spend_usd/1_000_000).toFixed(2)}M`
            : `$${(stats.total_spend_usd/1_000).toLocaleString(undefined, {maximumFractionDigits: 1})}K`
          : '—'}
          sub="USD normalised"
        />
        <KpiCard
          icon="⚡" color="blue" label="Energy Consumed"
          value={loading ? '...' : stats.total_kwh ? `${(stats.total_kwh/1_000_000).toFixed(2)}M` : '—'}
          sub="kWh total"
        />
        <KpiCard
          icon="📉" color="green" label="Average PUE"
          value={loading ? '...' : stats.avg_pue?.toFixed(3) ?? '—'}
          sub="Across all sites"
          badge={stats.avg_pue && stats.avg_pue < 1.5 ? '✓ Under 1.5' : null}
          badgeColor="bg-emerald-500/15 text-emerald-400"
        />
        <KpiCard
          icon="🔋" color="amber" label="Cost per kWh"
          value={loading ? '...' : stats.effective_usd_per_kwh ? `$${stats.effective_usd_per_kwh.toFixed(3)}` : '—'}
          sub="Effective USD rate"
        />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Spend by vendor */}
        <Card className="lg:col-span-2">
          <CardTitle title="Spend by Vendor" subtitle="Total USD · All periods" />
          {loading || !byVendor.length ? (
            <div className="h-48 flex items-center justify-center text-slate-600 text-sm">
              {loading ? 'Loading...' : 'No data yet'}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={byVendor} margin={{ top: 0, right: 8, left: 0, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="vendor"
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  angle={-30} textAnchor="end" interval={0}
                  tickFormatter={v => v.split(' ')[0]}
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  tickFormatter={fmtUSD}
                  width={48}
                />
                <Tooltip content={<CustomTooltip prefix="$" />} />
                <Bar dataKey="total_usd" radius={[4,4,0,0]}>
                  {byVendor.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Currency mix */}
        <Card>
          <CardTitle title="Currency Mix" subtitle="By USD spend" />
          {loading || !byCurrency.length ? (
            <div className="h-48 flex items-center justify-center text-slate-600 text-sm">
              {loading ? 'Loading...' : 'No data yet'}
            </div>
          ) : (
            <div className="flex flex-col gap-3 justify-center h-48">
              {byCurrency.map((c, i) => {
                const total = byCurrency.reduce((s, x) => s + x.total_usd, 0)
                const pct   = total > 0 ? (c.total_usd / total * 100).toFixed(0) : 0
                return (
                  <div key={c.currency} className="flex items-center gap-3">
                    <div className="text-xs text-slate-400 w-8">{c.currency}</div>
                    <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${pct}%`, background: COLORS[i % COLORS.length] }}
                      />
                    </div>
                    <div className="text-xs text-slate-300 font-semibold w-16 text-right">
                      ${(c.total_usd/1000).toFixed(0)}K
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </Card>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 gap-4">
        <Card>
          <CardTitle title="Monthly Spend Trend" subtitle="Total USD by billing period" />
          {loading || !byPeriod.length ? (
            <div className="h-40 flex items-center justify-center text-slate-600 text-sm">
              {loading ? 'Loading...' : 'No data yet — upload invoices to see trends'}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={byPeriod} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="period" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={fmtUSD} width={52} />
                <Tooltip content={<CustomTooltip prefix="$" />} />
                <Line
                  type="monotone" dataKey="total_usd"
                  stroke="#6366f1" strokeWidth={2.5}
                  dot={{ fill: '#6366f1', r: 4, strokeWidth: 0 }}
                  activeDot={{ r: 6, fill: '#818cf8' }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>
    </div>
  )
}
