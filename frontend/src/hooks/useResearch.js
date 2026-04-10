import { useState } from "react"
import api from "../utils/api"

export function useResearch() {
  const [sessionId, setSessionId] = useState(null)
  const [steps, setSteps] = useState([])
  const [report, setReport] = useState("")
  const [sources, setSources] = useState([])
  const [status, setStatus] = useState("idle") // idle | running | complete | error

  const startResearch = async (query, depth) => {
    setStatus("running")
    setSteps([])
    setReport("")
    setSources([])

    try {
      // Create session and get session_id
      const { data } = await api.post("/api/research", { query, depth })
      const id = data.session_id
      setSessionId(id)

      // Open SSE stream
      const es = new EventSource(`/api/research/${id}/stream`)

      es.onmessage = (event) => {
        const step = JSON.parse(event.data)
        if (step.type === "ping") return

        setSteps((prev) => [...prev, step])

        if (step.type === "complete") {
          setReport(step.data.report)
          setSources(step.data.sources || [])
          setStatus("complete")
          es.close()
        }

        if (step.type === "error") {
          setStatus("error")
          es.close()
        }
      }

      es.onerror = () => {
        setStatus("error")
        es.close()
      }
    } catch (err) {
      setSteps((prev) => [
        ...prev,
        { type: "error", message: err.message || "Failed to start research session" },
      ])
      setStatus("error")
    }
  }

  const loadSession = async (id) => {
    const { data } = await api.get(`/api/sessions/${id}`)
    setReport(data.report || "")
    setSources(JSON.parse(data.sources_json || "[]"))
    setStatus(data.status === "failed" ? "error" : data.status === "complete" ? "complete" : "idle")
    setSteps(data.status === "failed" ? [{ type: "error", message: "This research session failed." }] : [])
    setSessionId(id)
  }

  const resetSession = () => {
    setStatus("idle")
    setSteps([])
    setReport("")
    setSources([])
    setSessionId(null)
  }

  return {
    startResearch,
    loadSession,
    resetSession,
    steps,
    report,
    sources,
    status,
    sessionId,
  }
}
