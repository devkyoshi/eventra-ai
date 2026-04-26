import { useState } from 'react'
import { Header } from './components/Header'
import { EventInputForm } from './components/EventInputForm'
import { PipelineProgress } from './components/PipelineProgress'
import { ClarificationView } from './components/ClarificationView'
import { RequirementsCard } from './components/RequirementsCard'
import { VenueSection } from './components/VenueSection'
import { BudgetSection } from './components/BudgetSection'
import { CommunicationsSection } from './components/CommunicationsSection'
import { planEvent } from './lib/api'
import type { PlanResponse } from './types/api'

type AppState = 'idle' | 'loading' | 'clarification' | 'results' | 'error'

export default function App() {
  const [appState, setAppState] = useState<AppState>('idle')
  const [response, setResponse] = useState<PlanResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async (userRequest: string) => {
    setAppState('loading')
    setResponse(null)
    setErrorMsg('')
    try {
      const result = await planEvent(userRequest)
      setResponse(result)
      setAppState(result.status === 'clarification_needed' ? 'clarification' : 'results')
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'An unexpected error occurred.')
      setAppState('error')
    }
  }

  const pipelineStep =
    appState === 'loading' ? 1
    : appState === 'results' ? 4
    : 0

  const showPipeline = appState !== 'idle'

  return (
    <div className="min-h-screen bg-white">
      <Header />

      <main className="mx-auto max-w-5xl px-6 pb-24">
        {/* Hero — text only, centered */}
        <div className="py-16 text-center">
          <p className="mb-3 text-[12px] font-semibold uppercase tracking-widest text-[#0071E3]">
            Powered by AI
          </p>
          <h1 className="mb-4 text-[44px] font-semibold leading-tight tracking-[-0.02em] text-[#1D1D1F] sm:text-[56px]">
            Plan your perfect event.
          </h1>
          <p className="mx-auto mb-12 max-w-lg text-[17px] leading-relaxed text-[#6E6E73]">
            Describe your event in plain English. Our AI extracts your requirements,
            finds venues, builds a budget, and drafts communications — in seconds.
          </p>
        </div>

        {/* Form + pipeline — vertically stacked and centered */}
        <div className="flex flex-col items-center gap-10">
          <div className="w-full max-w-2xl">
            <EventInputForm onSubmit={handleSubmit} isLoading={appState === 'loading'} />
          </div>

          {showPipeline && (
            <div className="w-full max-w-2xl">
              <PipelineProgress currentStep={pipelineStep} isLoading={appState === 'loading'} />
            </div>
          )}

          {appState === 'error' && (
            <div className="w-full max-w-2xl rounded-[14px] border border-red-100 bg-red-50 px-6 py-4 text-[14px] text-red-700">
              <strong>Something went wrong:</strong> {errorMsg}
            </div>
          )}

          {appState === 'clarification' && response?.clarification_needed && (
            <div className="w-full max-w-2xl">
              <ClarificationView questions={response.clarification_needed} />
            </div>
          )}

          {appState === 'results' && response && (
            <div className="w-full space-y-10">
              {response.requirements && (
                <RequirementsCard requirements={response.requirements} />
              )}
              {response.venue_options && response.venue_options.length > 0 && (
                <VenueSection venues={response.venue_options} />
              )}
              {response.budget && response.schedule && (
                <BudgetSection budget={response.budget} schedule={response.schedule} />
              )}
              {response.communications && (
                <CommunicationsSection communications={response.communications} />
              )}
            </div>
          )}
        </div>
      </main>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
