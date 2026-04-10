import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { ExportBar } from "./ExportBar"
import { SourceCard } from "./SourceCard"

export function ReportViewer({ report, sources }) {
  return (
    <div className="mt-6 w-full max-w-3xl mx-auto">
      <ExportBar report={report} />
      <article className="prose prose-slate max-w-none mt-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
      </article>
      {sources.length > 0 && (
        <div className="mt-10">
          <h3 className="text-sm font-medium text-gray-500 mb-4">
            Sources ({sources.length})
          </h3>
          <div className="grid grid-cols-1 gap-3">
            {sources.map((source, i) => (
              <SourceCard key={i} source={source} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
