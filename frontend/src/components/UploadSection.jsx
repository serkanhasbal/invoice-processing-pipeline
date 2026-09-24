import { useState, useRef } from 'react'
import { uploadInvoice } from '../hooks/useApi'

const STEPS = [
  { id: 'idle',       label: 'Waiting for file...',             icon: '○' },
  { id: 'uploading',  label: 'Uploading to S3...',              icon: '⟳' },
  { id: 'processing', label: 'Bedrock extracting data...',      icon: '⚡' },
  { id: 'done',       label: 'Saved to processed/invoices/',    icon: '✓' },
  { id: 'error',      label: 'Processing failed',               icon: '✗' },
]

export default function UploadSection({ onUploadComplete }) {
  const [status,   setStatus]   = useState('idle')
  const [fileName, setFileName] = useState(null)
  const [error,    setError]    = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  async function handleFile(file) {
    if (!file) return
    const allowed = ['application/pdf', 'image/png', 'image/jpeg']
    if (!allowed.includes(file.type) && !file.name.match(/\.(pdf|png|jpe?g)$/i)) {
      setError('Unsupported format. Please use PDF, PNG, or JPG.')
      return
    }
    setFileName(file.name)
    setError(null)
    try {
      await uploadInvoice(file, setStatus)
      setStatus('done')
      onUploadComplete?.()
    } catch (err) {
      setStatus('error')
      setError(err.message)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  function reset() {
    setStatus('idle')
    setFileName(null)
    setError(null)
  }

  const stepIndex = STEPS.findIndex(s => s.id === status)

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-xs font-semibold text-indigo-400 uppercase tracking-widest mb-6">
        📄 Process New Invoice
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

        {/* Drop zone */}
        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => status === 'idle' && inputRef.current?.click()}
          className={`relative bg-[#0f1729] border-2 rounded-2xl p-10 text-center cursor-pointer transition-all ${
            dragOver
              ? 'border-indigo-400 bg-indigo-500/10 scale-[1.01]'
              : status === 'done'
              ? 'border-emerald-500/40 bg-emerald-500/5'
              : status === 'error'
              ? 'border-red-500/40 bg-red-500/5'
              : 'border-dashed border-indigo-500/30 hover:border-indigo-400/60 hover:bg-indigo-500/5'
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            className="hidden"
            onChange={e => handleFile(e.target.files[0])}
          />

          <div className="text-5xl mb-4">
            {status === 'done' ? '✅' : status === 'error' ? '❌' : status !== 'idle' ? '⏳' : '📂'}
          </div>

          {status === 'idle' ? (
            <>
              <div className="text-base font-semibold text-slate-200 mb-1">Drop invoice here</div>
              <div className="text-xs text-slate-500">or click to browse</div>
              <div className="flex gap-2 justify-center mt-4">
                {['PDF','PNG','JPG','JPEG'].map(fmt => (
                  <span key={fmt} className="px-2 py-0.5 rounded bg-white/5 border border-white/8 text-xs text-slate-500">{fmt}</span>
                ))}
              </div>
            </>
          ) : status === 'done' ? (
            <>
              <div className="text-base font-semibold text-emerald-400 mb-1">Upload complete!</div>
              <div className="text-xs text-slate-500 mb-4">{fileName}</div>
              <div className="text-xs text-slate-500">Dashboard will refresh in ~10 seconds</div>
              <button onClick={reset} className="mt-4 text-xs text-indigo-400 hover:text-indigo-300 underline">
                Upload another
              </button>
            </>
          ) : status === 'error' ? (
            <>
              <div className="text-base font-semibold text-red-400 mb-1">Upload failed</div>
              <div className="text-xs text-red-500 mb-4">{error}</div>
              <button onClick={reset} className="text-xs text-indigo-400 hover:text-indigo-300 underline">
                Try again
              </button>
            </>
          ) : (
            <>
              <div className="text-base font-semibold text-slate-200 mb-1">Processing…</div>
              <div className="text-xs text-slate-500">{fileName}</div>
            </>
          )}
        </div>

        {/* Pipeline steps */}
        <div className="bg-[#0f1729] border border-white/5 rounded-2xl p-6">
          <div className="text-sm font-semibold text-slate-200 mb-5">Processing Pipeline</div>
          <div className="space-y-0">
            {[
              { label: 'File received',           done: stepIndex >= 1, active: status === 'idle' },
              { label: 'Uploaded to S3',           done: stepIndex >= 2, active: status === 'uploading' },
              { label: 'Lambda triggered',         done: stepIndex >= 3, active: false },
              { label: 'Bedrock extracting data',  done: status === 'done', active: status === 'processing' },
              { label: 'USD conversion applied',   done: status === 'done', active: false },
              { label: 'Saved to S3 processed/',   done: status === 'done', active: false },
            ].map((step, i) => (
              <div key={i} className="flex items-center gap-3 py-3 border-b border-white/4 last:border-0">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                  step.done   ? 'bg-emerald-500/15 text-emerald-400' :
                  step.active ? 'bg-indigo-500/20 text-indigo-400 animate-pulse' :
                                'bg-white/5 text-slate-600'
                }`}>
                  {step.done ? '✓' : step.active ? '⚡' : `${i+1}`}
                </div>
                <span className={`text-xs ${step.done ? 'text-slate-300' : step.active ? 'text-indigo-300' : 'text-slate-600'}`}>
                  {step.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
