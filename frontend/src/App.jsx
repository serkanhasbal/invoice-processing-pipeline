import { useState } from 'react'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import StatsBar from './components/StatsBar'
import Dashboard from './components/Dashboard'
import InvoiceTable from './components/InvoiceTable'
import UploadSection from './components/UploadSection'
import TechStack from './components/TechStack'
import Footer from './components/Footer'
import InvoiceModal from './components/InvoiceModal'
import { useApi } from './hooks/useApi'

export default function App() {
  const [selectedInvoice, setSelectedInvoice] = useState(null)
  const [activeSection, setActiveSection] = useState('dashboard')

  const { data: statsData, loading: statsLoading, refetch: refetchStats } = useApi('/stats')
  const { data: invoicesData, loading: invoicesLoading, refetch: refetchInvoices } = useApi('/invoices')

  const stats    = statsData   || {}
  const invoices = invoicesData?.invoices || []

  function handleUploadComplete() {
    // Wait a few seconds for Lambda to process, then refresh
    setTimeout(() => {
      refetchStats()
      refetchInvoices()
    }, 8000)
  }

  return (
    <div className="min-h-screen bg-[#0a0f1e]">
      <Navbar activeSection={activeSection} setActiveSection={setActiveSection} />

      {activeSection === 'dashboard' && (
        <>
          <Hero setActiveSection={setActiveSection} />
          <StatsBar stats={stats} loading={statsLoading} />
          <main className="max-w-7xl mx-auto px-6 py-10">
            <Dashboard stats={stats} loading={statsLoading} />
            <InvoiceTable
              invoices={invoices}
              loading={invoicesLoading}
              onSelect={setSelectedInvoice}
            />
          </main>
        </>
      )}

      {activeSection === 'upload' && (
        <main className="max-w-7xl mx-auto px-6 py-10">
          <UploadSection onUploadComplete={handleUploadComplete} />
        </main>
      )}

      {activeSection === 'about' && (
        <main className="max-w-7xl mx-auto px-6 py-10">
          <TechStack />
        </main>
      )}

      <Footer />

      {selectedInvoice && (
        <InvoiceModal
          invoice={selectedInvoice}
          onClose={() => setSelectedInvoice(null)}
        />
      )}
    </div>
  )
}
