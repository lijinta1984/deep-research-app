import { useState, useRef } from "react"

const DEPTH_OPTIONS = [
  { value: "quick", label: "Quick", tooltip: "2–3 sub-questions · ~30 sec" },
  { value: "standard", label: "Standard", tooltip: "4–5 sub-questions · ~60 sec" },
  { value: "deep", label: "Deep", tooltip: "6 sub-questions · ~2 min" },
]

export function QueryInput({ onSubmit, status }) {
  const [query, setQuery] = useState("")
  const [depth, setDepth] = useState("standard")
  const textareaRef = useRef(null)

  const isRunning = status === "running"

  const handleInput = (e) => {
    setQuery(e.target.value)
    // Auto-resize
    e.target.style.height = "auto"
    e.target.style.height = e.target.scrollHeight + "px"
  }

  const handleSubmit = () => {
    if (!query.trim() || isRunning) return
    onSubmit(query.trim(), depth)
  }

  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="query-input w-full max-w-3xl mx-auto">
      <textarea
        ref={textareaRef}
        value={query}
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="What do you want to research?"
        rows={2}
        className="w-full resize-none rounded-xl border border-gray-300 bg-white px-4 py-3 text-base shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none transition-all"
        disabled={isRunning}
      />

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        {/* Depth selector */}
        <div className="flex gap-2">
          {DEPTH_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setDepth(opt.value)}
              title={opt.tooltip}
              disabled={isRunning}
              className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-all ${
                depth === opt.value
                  ? "bg-indigo-600 text-white shadow-md"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={isRunning || !query.trim()}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-md hover:bg-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRunning ? (
            <>
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Researching...
            </>
          ) : (
            <>
              Research
              <span className="text-indigo-200">▶</span>
            </>
          )}
        </button>
      </div>

      <p className="mt-2 text-xs text-gray-400 text-right">
        Press <kbd className="rounded bg-gray-100 px-1 py-0.5 text-gray-500">Ctrl+Enter</kbd> to submit
      </p>
    </div>
  )
}
