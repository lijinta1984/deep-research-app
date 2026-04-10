export function SourceCard({ source }) {
  let domain = ""
  try {
    domain = new URL(source.url).hostname
  } catch {
    domain = source.url
  }

  const title = source.title
    ? source.title.length > 70
      ? source.title.slice(0, 70) + "..."
      : source.title
    : domain

  const snippet = source.snippet
    ? source.snippet.length > 120
      ? source.snippet.slice(0, 120) + "..."
      : source.snippet
    : ""

  return (
    <div className="flex items-start gap-3 rounded-lg border border-gray-200 bg-white p-3 hover:bg-gray-50 transition-colors">
      <img
        src={`https://www.google.com/s2/favicons?domain=${domain}&sz=16`}
        alt=""
        className="mt-1 h-4 w-4 flex-shrink-0"
      />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-900 truncate">{title}</p>
        <p className="text-xs text-gray-500 mt-0.5">
          {domain} {snippet && <>&middot; {snippet}</>}
        </p>
      </div>
      <button
        onClick={() => window.open(source.url, "_blank")}
        className="flex-shrink-0 rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 transition-colors"
      >
        Open &uarr;
      </button>
    </div>
  )
}
