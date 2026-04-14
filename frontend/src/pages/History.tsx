import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Trash2, Search, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { api } from '@/api/api'
import type { ResearchDepth, JobStatus } from '@/types/research'

export default function History() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [depthFilter, setDepthFilter] = useState<ResearchDepth | 'all'>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const { data: history, isLoading } = useQuery({
    queryKey: ['history'],
    queryFn: api.getHistory,
  })

  const deleteMutation = useMutation({
    mutationFn: api.deleteJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history'] })
    },
  })

  const filteredHistory = (history ?? []).filter((item) => {
    if (depthFilter !== 'all' && item.depth !== depthFilter) return false
    if (searchTerm && !item.query.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  const statusVariant = (status: JobStatus): 'high' | 'medium' | 'low' | 'outline' => {
    if (status === 'complete') return 'high'
    if (status === 'failed') return 'low'
    if (status === 'running') return 'medium'
    return 'outline'
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen px-4 py-8">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h1 className="text-2xl font-bold">Research History</h1>
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search queries..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
              <div className="flex gap-2">
                {(['all', 1, 2, 3] as const).map((d) => (
                  <Button
                    key={String(d)}
                    variant={depthFilter === d ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setDepthFilter(d)}
                  >
                    {d === 'all' ? 'All' : `Depth ${d}`}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Table */}
        <Card>
          <CardContent className="pt-6">
            {filteredHistory.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No research jobs found
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b text-left text-sm text-muted-foreground">
                      <th className="pb-3 font-medium">Query</th>
                      <th className="pb-3 font-medium">Depth</th>
                      <th className="pb-3 font-medium">Status</th>
                      <th className="pb-3 font-medium">Date</th>
                      <th className="pb-3 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filteredHistory.map((item) => (
                      <tr
                        key={item.job_id}
                        className="hover:bg-accent/50 cursor-pointer transition-colors"
                        onClick={() => {
                          if (item.status === 'complete') {
                            navigate(`/research/${item.job_id}/result`)
                          } else if (item.status === 'running' || item.status === 'queued') {
                            navigate(`/research/${item.job_id}/progress`)
                          }
                        }}
                      >
                        <td className="py-3 pr-4 max-w-xs">
                          <p className="font-medium truncate">{item.query}</p>
                        </td>
                        <td className="py-3 pr-4">
                          <span className="text-sm">{item.depth}</span>
                        </td>
                        <td className="py-3 pr-4">
                          <Badge variant={statusVariant(item.status)}>
                            {item.status}
                          </Badge>
                        </td>
                        <td className="py-3 pr-4">
                          <span className="text-sm text-muted-foreground">
                            {new Date(item.created_at).toLocaleDateString()}
                          </span>
                        </td>
                        <td className="py-3 text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteMutation.mutate(item.job_id)
                            }}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
