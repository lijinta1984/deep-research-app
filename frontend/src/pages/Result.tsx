import { useCallback, useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  ReactFlow,
  Controls,
  Background,
  type Node,
  type Edge,
  type NodeMouseHandler,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  Loader2,
  Download,
  Copy,
  Plus,
  ExternalLink,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/api/api'
import type { SearchTreeNode, ConfidenceLevel } from '@/types/research'

function confidenceVariant(level: ConfidenceLevel): 'high' | 'medium' | 'low' {
  return level
}

function flattenTree(
  node: SearchTreeNode,
  nodes: Node[],
  edges: Edge[],
  depth: number = 0,
  index: number = 0,
): void {
  const colorMap: Record<string, string> = {
    root: '#1e293b',
    query: '#3b82f6',
    gap: '#f59e0b',
    source: '#6b7280',
  }

  nodes.push({
    id: node.id,
    data: { label: node.label, url: node.url, nodeType: node.node_type },
    position: { x: index * 220, y: depth * 120 },
    style: {
      background: colorMap[node.node_type] ?? '#6b7280',
      color: '#fff',
      border: 'none',
      borderRadius: '8px',
      padding: '8px 12px',
      fontSize: '11px',
      maxWidth: '200px',
      whiteSpace: 'nowrap' as const,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
    },
  })

  node.children.forEach((child, i) => {
    edges.push({
      id: `${node.id}-${child.id}`,
      source: node.id,
      target: child.id,
      animated: child.node_type === 'source',
    })
    flattenTree(child, nodes, edges, depth + 1, index + i)
  })
}

export default function Result() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const [openQuestions, setOpenQuestions] = useState(false)
  const [exporting, setExporting] = useState(false)

  const { data: job, isLoading } = useQuery({
    queryKey: ['result', jobId],
    queryFn: () => api.getResult(jobId!),
    enabled: !!jobId,
  })

  const { data: tree } = useQuery({
    queryKey: ['tree', jobId],
    queryFn: () => api.getSearchTree(jobId!),
    enabled: !!jobId,
  })

  const { flowNodes, flowEdges } = useMemo(() => {
    if (!tree) return { flowNodes: [], flowEdges: [] }
    const nodes: Node[] = []
    const edges: Edge[] = []
    flattenTree(tree, nodes, edges)
    return { flowNodes: nodes, flowEdges: edges }
  }, [tree])

  const onNodeClick: NodeMouseHandler = useCallback((_event, node) => {
    const url = (node.data as { url?: string }).url
    if (url) {
      window.open(url, '_blank')
    }
  }, [])

  const handleExportDocx = async () => {
    if (!jobId) return
    setExporting(true)
    try {
      const blob = await api.exportReport(jobId, {
        job_id: jobId,
        format: 'docx',
        include_sources: true,
        include_open_questions: true,
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `research_${jobId.slice(0, 8)}.docx`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setExporting(false)
    }
  }

  const handleCopyMarkdown = async () => {
    if (!jobId) return
    try {
      const blob = await api.exportReport(jobId, {
        job_id: jobId,
        format: 'markdown',
        include_sources: true,
        include_open_questions: true,
      })
      const text = await blob.text()
      await navigator.clipboard.writeText(text)
    } catch {
      // Silently handle clipboard errors
    }
  }

  if (isLoading || !job) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const report = job.pass_3_output?.report
  const metadata = job.pass_3_output?.metadata
  const sources = job.pass_3_output?.sources ?? []

  if (!report) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <Card className="w-full max-w-lg">
          <CardContent className="pt-6 text-center">
            <p className="text-lg">Research results not available yet.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Left Column - Results */}
          <div className="flex-1 min-w-0 space-y-6">
            {/* Executive Summary */}
            <Card className="border-primary/30 bg-primary/5">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Executive Summary</CardTitle>
                  {metadata && (
                    <Badge variant={confidenceVariant(metadata.research_confidence_overall)}>
                      {metadata.research_confidence_overall.toUpperCase()} confidence
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed">{report.executive_summary}</p>
              </CardContent>
            </Card>

            {/* Report Sections */}
            {report.sections.map((section, i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{section.title}</CardTitle>
                    <Badge variant={confidenceVariant(section.confidence)}>
                      {section.confidence.toUpperCase()}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground italic">
                    {section.confidence_rationale}
                  </p>
                </CardHeader>
                <CardContent className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {section.content}
                  </ReactMarkdown>
                </CardContent>
              </Card>
            ))}

            {/* Key Conclusions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Key Conclusions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {report.key_conclusions.map((kc, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <Badge
                        variant={confidenceVariant(kc.confidence)}
                        className="mt-0.5 flex-shrink-0"
                      >
                        {kc.confidence.toUpperCase()}
                      </Badge>
                      <span className="text-sm">{kc.conclusion}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Open Questions */}
            {report.open_questions.length > 0 && (
              <Card>
                <CardHeader>
                  <button
                    onClick={() => setOpenQuestions(!openQuestions)}
                    className="flex items-center gap-2 w-full text-left"
                  >
                    {openQuestions ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                    <CardTitle className="text-lg">
                      Open Questions ({report.open_questions.length})
                    </CardTitle>
                  </button>
                </CardHeader>
                {openQuestions && (
                  <CardContent>
                    <ul className="space-y-4">
                      {report.open_questions.map((oq, i) => (
                        <li key={i} className="space-y-1">
                          <p className="text-sm font-medium">{oq.question}</p>
                          <p className="text-xs text-muted-foreground">
                            {oq.why_it_matters}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                )}
              </Card>
            )}
          </div>

          {/* Right Column - Tree + Sources */}
          <div className="w-full lg:w-96 space-y-6">
            {/* Search Tree */}
            {flowNodes.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Search Tree</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80 w-full border border-border rounded-lg overflow-hidden">
                    <ReactFlow
                      nodes={flowNodes}
                      edges={flowEdges}
                      onNodeClick={onNodeClick}
                      fitView
                      attributionPosition="bottom-left"
                      proOptions={{ hideAttribution: true }}
                    >
                      <Controls />
                      <Background />
                    </ReactFlow>
                  </div>
                  <div className="flex gap-3 mt-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded bg-[#1e293b]" />
                      Root
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded bg-[#3b82f6]" />
                      Query
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded bg-[#f59e0b]" />
                      Gap
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded bg-[#6b7280]" />
                      Source
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Sources List */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  Sources ({sources.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {sources.map((src, i) => (
                  <a
                    key={i}
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start gap-3 p-3 rounded-lg border border-border hover:bg-accent transition-colors"
                  >
                    <img
                      src={`https://www.google.com/s2/favicons?domain=${new URL(src.url).hostname}&sz=16`}
                      alt=""
                      className="w-4 h-4 mt-0.5 flex-shrink-0"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{src.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{src.url}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={confidenceVariant(src.relevance)} className="text-[10px]">
                          {src.relevance}
                        </Badge>
                        <span className="text-[10px] text-muted-foreground">
                          Pass {src.found_in_pass}
                        </span>
                      </div>
                    </div>
                    <ExternalLink className="h-3 w-3 text-muted-foreground flex-shrink-0 mt-1" />
                  </a>
                ))}
              </CardContent>
            </Card>

            {/* Metadata */}
            {metadata && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Research Metadata</CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-1 text-muted-foreground">
                  <p>Total Passes: {metadata.total_passes}</p>
                  <p>Sources Scraped: {metadata.total_sources_scraped}</p>
                  <p>Gaps Identified: {metadata.total_gaps_identified}</p>
                  <p>Gaps Resolved: {metadata.total_gaps_resolved}</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Export Bar */}
      <div className="sticky bottom-0 border-t bg-background/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <Button onClick={handleExportDocx} disabled={exporting}>
            <Download className="h-4 w-4 mr-2" />
            {exporting ? 'Exporting...' : 'Download DOCX'}
          </Button>
          <Button variant="outline" onClick={handleCopyMarkdown}>
            <Copy className="h-4 w-4 mr-2" />
            Copy Markdown
          </Button>
          <Button variant="secondary" onClick={() => navigate('/')}>
            <Plus className="h-4 w-4 mr-2" />
            New Research
          </Button>
        </div>
      </div>
    </div>
  )
}
