export default function Navbar({ activeSection, setActiveSection }) {
  const links = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'upload',    label: 'Upload Invoice' },
    { id: 'about',     label: 'Architecture' },
  ]

  return (
    <nav className="sticky top-0 z-50 bg-[#0f1729]/95 border-b border-white/5 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">

        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-sm font-bold">
            ⚡
          </div>
          <span className="font-bold text-sm tracking-tight">
            Invoice<span className="text-indigo-400">Intelligence</span>
          </span>
        </div>

        {/* Nav links */}
        <div className="hidden sm:flex items-center gap-1">
          {links.map(link => (
            <button
              key={link.id}
              onClick={() => setActiveSection(link.id)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeSection === link.id
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              {link.label}
            </button>
          ))}
        </div>

        {/* Right */}
        <div className="flex items-center gap-3">
          <span className="hidden sm:block text-xs px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            Powered by Amazon Bedrock
          </span>
          <a
            href="https://github.com/serkanhasbal/invoice-processing-pipeline"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 text-sm font-medium"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.522 2 12 2z"/>
            </svg>
            GitHub
          </a>
        </div>
      </div>
    </nav>
  )
}
