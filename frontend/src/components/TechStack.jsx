const ARCHITECTURE = [
  {
    step: '01', title: 'Ingest', icon: '📄',
    description: 'PDF or image invoice uploaded to Amazon S3 raw/invoices/ prefix.',
    services: ['Amazon S3'],
    color: 'indigo',
  },
  {
    step: '02', title: 'Trigger', icon: '⚡',
    description: 'S3 ObjectCreated event automatically triggers the processing Lambda.',
    services: ['AWS Lambda', 'S3 Event Notification'],
    color: 'blue',
  },
  {
    step: '03', title: 'Configure', icon: '⚙️',
    description: 'Lambda reads runtime config (model ID, prompt version, exchange rates) from AppConfig — no redeployment needed to change them.',
    services: ['AWS AppConfig'],
    color: 'violet',
  },
  {
    step: '04', title: 'Extract', icon: '🤖',
    description: 'Amazon Bedrock (Nova Pro) reads the invoice and returns structured JSON with vendor, amounts, kWh, PUE, and more.',
    services: ['Amazon Bedrock', 'Nova Pro'],
    color: 'purple',
  },
  {
    step: '05', title: 'Validate', icon: '✅',
    description: 'Lambda validates and normalises the Bedrock output, applies USD conversion from AppConfig exchange rates, and flags any anomalies.',
    services: ['Python', 'AWS Lambda'],
    color: 'green',
  },
  {
    step: '06', title: 'Store', icon: '🗄️',
    description: 'Processed JSON is written to S3 processed/invoices/. Glue Data Catalog maps the schema for Athena queries.',
    services: ['Amazon S3', 'AWS Glue'],
    color: 'emerald',
  },
  {
    step: '07', title: 'Analyse', icon: '📊',
    description: 'Amazon Athena queries the processed data using standard SQL. This frontend fetches results via API Gateway + Lambda.',
    services: ['Amazon Athena', 'API Gateway'],
    color: 'amber',
  },
]

const COLOR_MAP = {
  indigo:  { bg: 'bg-indigo-500/10',  border: 'border-indigo-500/20',  text: 'text-indigo-400',  num: 'bg-indigo-500/20 text-indigo-300' },
  blue:    { bg: 'bg-sky-500/10',     border: 'border-sky-500/20',     text: 'text-sky-400',     num: 'bg-sky-500/20 text-sky-300' },
  violet:  { bg: 'bg-violet-500/10',  border: 'border-violet-500/20',  text: 'text-violet-400',  num: 'bg-violet-500/20 text-violet-300' },
  purple:  { bg: 'bg-purple-500/10',  border: 'border-purple-500/20',  text: 'text-purple-400',  num: 'bg-purple-500/20 text-purple-300' },
  green:   { bg: 'bg-green-500/10',   border: 'border-green-500/20',   text: 'text-green-400',   num: 'bg-green-500/20 text-green-300' },
  emerald: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', num: 'bg-emerald-500/20 text-emerald-300' },
  amber:   { bg: 'bg-amber-500/10',   border: 'border-amber-500/20',   text: 'text-amber-400',   num: 'bg-amber-500/20 text-amber-300' },
}

const TECH_PILLS = [
  '☁️ Amazon S3', 'λ AWS Lambda', '🤖 Amazon Bedrock', '⚙️ AWS AppConfig',
  '📊 Amazon Athena', '🗂️ AWS Glue', '🌐 API Gateway', '🏗️ AWS CDK v2',
  '🐍 Python 3.12', '⚛️ React + Vite', '💨 Tailwind CSS', '📈 Recharts',
]

export default function TechStack() {
  return (
    <div className="max-w-5xl mx-auto space-y-10">

      <div className="text-center">
        <div className="text-xs font-semibold text-indigo-400 uppercase tracking-widest mb-3">Architecture</div>
        <h2 className="text-3xl font-bold tracking-tight mb-3">
          Production-grade{' '}
          <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
            AWS Pipeline
          </span>
        </h2>
        <p className="text-slate-500 text-sm max-w-xl mx-auto">
          Fully serverless, event-driven, and defined as Infrastructure as Code with AWS CDK v2.
          Every component is observable, cost-efficient, and independently deployable.
        </p>
      </div>

      {/* Pipeline steps */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {ARCHITECTURE.map(step => {
          const c = COLOR_MAP[step.color]
          return (
            <div key={step.step} className={`${c.bg} border ${c.border} rounded-2xl p-5`}>
              <div className="flex items-center gap-3 mb-3">
                <span className={`w-7 h-7 rounded-lg text-xs font-bold flex items-center justify-center ${c.num}`}>
                  {step.step}
                </span>
                <span className="text-lg">{step.icon}</span>
                <span className={`text-sm font-semibold ${c.text}`}>{step.title}</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">{step.description}</p>
              <div className="flex flex-wrap gap-1">
                {step.services.map(s => (
                  <span key={s} className="px-2 py-0.5 rounded-md bg-black/20 text-xs text-slate-500">{s}</span>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Tech pills */}
      <div className="bg-[#0f1729] border border-white/5 rounded-2xl p-8 text-center">
        <div className="text-sm font-semibold text-slate-300 mb-5">Built With</div>
        <div className="flex flex-wrap justify-center gap-2">
          {TECH_PILLS.map(pill => (
            <span key={pill} className="px-3 py-1.5 rounded-xl bg-white/4 border border-white/8 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/8 transition-colors">
              {pill}
            </span>
          ))}
        </div>
      </div>

    </div>
  )
}
