import { Toaster } from "react-hot-toast"
import { useResearch } from "./hooks/useResearch"
import { QueryInput } from "./components/QueryInput"
import { ProgressPanel } from "./components/ProgressPanel"
import { ReportViewer } from "./components/ReportViewer"
import { SessionSidebar } from "./components/SessionSidebar"

export default function App() {
  const {
    startResearch,
    loadSession,
    resetSession,
    steps,
    report,
    sources,
    status,
    sessionId,
  } = useResearch()

  return (
    <div className="flex h-screen flex-col">
      <Toaster position="top-right" />

      {/* Header */}
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3 shadow-sm">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-gray-900">
            <span className="text-indigo-600">Deep</span> Research
          </h1>
        </div>
        <span className="text-xs text-gray-400">
          Powered by <span className="font-medium text-gray-500">Kimi K2</span>
        </span>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <SessionSidebar
          onLoadSession={loadSession}
          onNewResearch={resetSession}
          activeSessionId={sessionId}
          status={status}
        />

        {/* Main Panel */}
        <main className="flex-1 overflow-y-auto px-6 py-8">
          {/* Query Input — always visible when idle or running */}
          {(status === "idle" || status === "running") && (
            <QueryInput onSubmit={startResearch} status={status} />
          )}

          {/* Progress Panel — visible while running or on error */}
          <ProgressPanel steps={steps} status={status} />

          {/* Report Viewer — visible when complete */}
          {status === "complete" && report && (
            <ReportViewer report={report} sources={sources} />
          )}

          {/* Error state */}
          {status === "error" && steps.length > 0 && (
            <div className="mt-6 w-full max-w-3xl mx-auto rounded-xl border border-red-200 bg-red-50 p-5">
              <p className="text-sm text-red-700">
                {steps[steps.length - 1]?.message || "An error occurred during research."}
              </p>
              <button
                onClick={resetSession}
                className="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Empty state */}
          {status === "idle" && (
            <div className="mt-16 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50">
                <svg className="h-8 w-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-gray-700">
                Start a deep research session
              </h2>
              <p className="mt-1 text-sm text-gray-400 max-w-md mx-auto">
                Enter a topic or question above. The agent will decompose it, search the web,
                and synthesize a structured report with citations.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
