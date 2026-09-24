export default function Hero({ setActiveSection }) {
  return (
    <div className="relative py-20 px-6 text-center overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(99,102,241,0.15),transparent)]" />

      <div className="relative max-w-3xl mx-auto">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
          Serverless · AI-Powered · Real-time Analytics
        </div>

        {/* Title */}
        <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight leading-tight mb-5">
          Energy Invoice{' '}
          <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-sky-400 bg-clip-text text-transparent">
            Intelligence
          </span>
        </h1>

        <p className="text-lg text-slate-400 leading-relaxed mb-8 max-w-xl mx-auto">
          Upload energy invoices and let AI extract structured data instantly.
          Built end-to-end on AWS with Amazon Bedrock, Lambda, and Athena.
        </p>

        {/* CTAs */}
        <div className="flex gap-3 justify-center flex-wrap">
          <button
            onClick={() => setActiveSection('upload')}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 text-white font-semibold text-sm shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:scale-105 transition-all"
          >
            📄 Upload Invoice
          </button>
          <button
            onClick={() => setActiveSection('about')}
            className="px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-300 font-semibold text-sm hover:bg-white/10 hover:scale-105 transition-all"
          >
            🏗 View Architecture
          </button>
        </div>
      </div>
    </div>
  )
}
