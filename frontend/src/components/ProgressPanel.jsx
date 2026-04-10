import { useEffect, useRef } from "react"

const STEP_ICONS = {
  decompose: "\ud83d\udd0d",
  search: "\ud83c\udf10",
  scrape: "\ud83d\udcc4",
  synthesize: "\ud83e\udde0",
  complete: "\u2705",
  error: "\u274c",
}

export function ProgressPanel({ steps, status }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [steps])

  if (status !== "running" && status !== "error") return null

  return (
    <div className="progress-panel mt-6 w-full max-w-3xl mx-auto">
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm max-h-96 overflow-y-auto">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Research Progress
        </h3>
        <div className="space-y-3">
          {steps.map((step, idx) => (
            <div key={idx} className="flex gap-3">
              <span className="flex-shrink-0 mt-0.5 text-lg">
                {STEP_ICONS[step.type] || "\u2022"}
              </span>
              <div className="min-w-0">
                <p className="text-sm text-gray-800">{step.message}</p>

                {/* Render sub-questions list */}
                {step.data?.subquestions && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {step.data.subquestions.map((q, i) => (
                      <span
                        key={i}
                        className="inline-block rounded-full bg-indigo-50 px-3 py-1 text-xs text-indigo-700"
                      >
                        {q}
                      </span>
                    ))}
                  </div>
                )}

                {/* Render sources list */}
                {step.data?.sources && step.data.sources.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {step.data.sources.map((s, i) => (
                      <a
                        key={i}
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-xs text-indigo-600 hover:text-indigo-800 hover:underline truncate"
                      >
                        &middot; {s.title || s.url}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Spinner for running state */}
          {status === "running" && (
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Working...
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
