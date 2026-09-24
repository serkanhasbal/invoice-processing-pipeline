export default function Footer() {
  return (
    <footer className="border-t border-white/5 mt-16">
      <div className="max-w-7xl mx-auto px-6 py-8 text-center space-y-2">
        <div className="text-sm text-slate-500">
          Built by{' '}
          <a
            href="https://github.com/serkanhasbal"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-400 hover:text-indigo-300"
          >
            serkanhasbal
          </a>
          {' · '}
          <a
            href="https://github.com/serkanhasbal/invoice-processing-pipeline"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-400 hover:text-indigo-300"
          >
            View on GitHub
          </a>
          {' · '}
          Powered by Amazon Bedrock Nova Pro
        </div>
        <div className="text-xs text-slate-700 max-w-2xl mx-auto">
          ⚠️ All data shown is synthetically generated for demonstration purposes only.
          No real company data, personal information, or confidential records are used.
          All company names, invoice numbers, and financial figures are entirely fictional.
        </div>
      </div>
    </footer>
  )
}
