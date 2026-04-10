import { useState, useEffect } from "react"
import api from "../utils/api"

function timeAgo(dateStr) {
  if (!dateStr) return ""
  const now = new Date()
  const date = new Date(dateStr)
  const seconds = Math.floor((now - date) / 1000)
  if (seconds < 60) return "just now"
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function SessionSidebar({ onLoadSession, onNewResearch, activeSessionId, status }) {
  const [sessions, setSessions] = useState([])
  const [hoveredId, setHoveredId] = useState(null)

  const fetchSessions = async () => {
    try {
      const { data } = await api.get("/api/sessions")
      setSessions(data)
    } catch (err) {
      console.error("Failed to fetch sessions:", err)
    }
  }

  useEffect(() => {
    fetchSessions()
  }, [])

  // Refresh when a research completes
  useEffect(() => {
    if (status === "complete") {
      fetchSessions()
    }
  }, [status])

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    try {
      await api.delete(`/api/sessions/${id}`)
      setSessions((prev) => prev.filter((s) => s.id !== id))
    } catch (err) {
      console.error("Failed to delete session:", err)
    }
  }

  return (
    <aside className="flex h-full w-64 flex-col border-r border-gray-200 bg-gray-50">
      <div className="p-4">
        <button
          onClick={onNewResearch}
          className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors"
        >
          + New Research
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {sessions.length === 0 ? (
          <p className="px-3 py-4 text-xs text-gray-400 text-center">
            No past sessions
          </p>
        ) : (
          <div className="space-y-1">
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => onLoadSession(session.id)}
                onMouseEnter={() => setHoveredId(session.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`group relative cursor-pointer rounded-lg px-3 py-2.5 transition-colors ${
                  activeSessionId === session.id
                    ? "border-l-2 border-indigo-600 bg-indigo-50"
                    : "hover:bg-gray-100"
                }`}
              >
                <p className="text-sm font-medium text-gray-800 truncate pr-6">
                  {session.query && session.query.length > 45
                    ? session.query.slice(0, 45) + "..."
                    : session.query}
                </p>
                <div className="mt-0.5 flex items-center gap-2">
                  <span
                    className={`inline-block h-1.5 w-1.5 rounded-full ${
                      session.status === "complete"
                        ? "bg-green-400"
                        : session.status === "failed"
                        ? "bg-red-400"
                        : "bg-yellow-400"
                    }`}
                  />
                  <span className="text-xs text-gray-400">
                    {timeAgo(session.created_at)}
                  </span>
                </div>

                {/* Delete button */}
                {hoveredId === session.id && (
                  <button
                    onClick={(e) => handleDelete(e, session.id)}
                    className="absolute right-2 top-2.5 rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500 transition-colors"
                    title="Delete session"
                  >
                    <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}
