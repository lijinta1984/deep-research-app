import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Search, Zap, BarChart3, Brain } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'
import { api } from '@/api/api'
import type { ResearchDepth } from '@/types/research'

const depthOptions: { value: ResearchDepth; label: string; description: string; icon: React.ReactNode }[] = [
  { value: 1, label: 'Quick', description: '1 pass — fast overview', icon: <Zap className="h-4 w-4" /> },
  { value: 2, label: 'Standard', description: '2 passes — gap analysis', icon: <BarChart3 className="h-4 w-4" /> },
  { value: 3, label: 'Deep', description: '3 passes — comprehensive', icon: <Brain className="h-4 w-4" /> },
]

export default function Home() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [depth, setDepth] = useState<ResearchDepth>(2)
  const [maxSources, setMaxSources] = useState(10)

  const { data: history } = useQuery({
    queryKey: ['history'],
    queryFn: api.getHistory,
  })

  const startMutation = useMutation({
    mutationFn: api.startResearch,
    onSuccess: (data) => {
      navigate(`/research/${data.job_id}/progress`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim().length < 5) return
    startMutation.mutate({ query: query.trim(), depth, max_sources: maxSources })
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-start pt-20 px-4">
      <div className="w-full max-w-3xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">Deep Research</h1>
          <p className="text-muted-foreground text-lg">
            AI-powered multi-pass research engine
          </p>
        </div>

        {/* Search Form */}
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                <Input
                  placeholder="What would you like to research? (min 5 characters)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-10 h-12 text-lg"
                  minLength={5}
                  maxLength={500}
                />
              </div>

              {/* Depth Selector */}
              <div className="space-y-3">
                <label className="text-sm font-medium">Research Depth</label>
                <div className="grid grid-cols-3 gap-3">
                  {depthOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setDepth(option.value)}
                      className={`flex flex-col items-center gap-2 p-4 rounded-lg border transition-colors ${
                        depth === option.value
                          ? 'border-primary bg-primary/10 text-primary'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      {option.icon}
                      <span className="font-medium text-sm">{option.label}</span>
                      <span className="text-xs text-muted-foreground">{option.description}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Max Sources */}
              <div className="space-y-3">
                <div className="flex justify-between">
                  <label className="text-sm font-medium">Max Sources</label>
                  <span className="text-sm text-muted-foreground">{maxSources}</span>
                </div>
                <Slider
                  value={[maxSources]}
                  onValueChange={(v) => setMaxSources(v[0] ?? 10)}
                  min={5}
                  max={20}
                  step={1}
                />
              </div>

              <Button
                type="submit"
                className="w-full h-12 text-lg"
                disabled={query.trim().length < 5 || startMutation.isPending}
              >
                {startMutation.isPending ? 'Starting Research...' : 'Start Research'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Recent Searches */}
        {history && history.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Research</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {history.slice(0, 10).map((item) => (
                <button
                  key={item.job_id}
                  onClick={() => {
                    if (item.status === 'complete') {
                      navigate(`/research/${item.job_id}/result`)
                    } else if (item.status === 'running' || item.status === 'queued') {
                      navigate(`/research/${item.job_id}/progress`)
                    }
                  }}
                  className="w-full flex items-center justify-between p-3 rounded-lg border border-border hover:bg-accent transition-colors text-left"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{item.query}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(item.created_at).toLocaleDateString()} · Depth {item.depth}
                    </p>
                  </div>
                  <Badge
                    variant={
                      item.status === 'complete' ? 'high' :
                      item.status === 'failed' ? 'low' :
                      item.status === 'running' ? 'medium' : 'outline'
                    }
                  >
                    {item.status}
                  </Badge>
                </button>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
