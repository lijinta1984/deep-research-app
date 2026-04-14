import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Loader2, AlertCircle, Globe, CheckCircle2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { api } from '@/api/api'

const passLabels = [
  'Initializing',
  'Pass 1: Broad Search',
  'Pass 2: Gap Analysis',
  'Pass 3: Final Synthesis',
]

export default function ProgressPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()

  const { data: progress, error } = useQuery({
    queryKey: ['progress', jobId],
    queryFn: () => api.getStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'complete' || status === 'failed' ? false : 2000
    },
  })

  useEffect(() => {
    if (progress?.status === 'complete') {
      navigate(`/research/${jobId}/result`, { replace: true })
    }
  }, [progress?.status, jobId, navigate])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <Card className="w-full max-w-lg">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <p className="text-lg font-medium">Failed to load progress</p>
            <p className="text-muted-foreground mt-1">{String(error)}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!progress) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const currentPassLabel = passLabels[progress.current_pass] ?? 'Processing'

  return (
    <div className="min-h-screen flex flex-col items-center justify-start pt-16 px-4">
      <div className="w-full max-w-2xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">Research in Progress</h1>
          <p className="text-muted-foreground">Job: {jobId?.slice(0, 8)}...</p>
        </div>

        {/* Error State */}
        {progress.status === 'failed' && (
          <Card className="border-red-500/50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-6 w-6 text-red-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium text-red-400">Research Failed</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {progress.error_message ?? 'An unknown error occurred'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Progress Bar */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">{currentPassLabel}</CardTitle>
              <span className="text-sm text-muted-foreground">{progress.progress}%</span>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={progress.progress} />

            {/* Pass Indicator */}
            <div className="flex items-center justify-between gap-2">
              {[1, 2, 3].map((pass) => {
                const isSkipped = pass === 2 && progress.depth < 2
                const isActive = !isSkipped && progress.current_pass === pass
                const isComplete = !isSkipped && progress.current_pass > pass
                return (
                  <div
                    key={pass}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border flex-1 text-center justify-center ${
                      isSkipped
                        ? 'border-border/50 bg-muted/30 text-muted-foreground/50 line-through'
                        : isActive
                          ? 'border-primary bg-primary/10 text-primary'
                          : isComplete
                            ? 'border-green-500/30 bg-green-500/10 text-green-400'
                            : 'border-border text-muted-foreground'
                    }`}
                  >
                    {isComplete ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : isActive ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : null}
                    <span className="text-xs font-medium">Pass {pass}</span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardContent className="pt-6 text-center">
              <Globe className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
              <p className="text-2xl font-bold">{progress.sources_scraped}</p>
              <p className="text-xs text-muted-foreground">Sources Scraped</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6 text-center">
              <AlertCircle className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
              <p className="text-2xl font-bold">{progress.gaps_found}</p>
              <p className="text-xs text-muted-foreground">Gaps Identified</p>
            </CardContent>
          </Card>
        </div>

        {/* Partial Synthesis */}
        {progress.partial_synthesis && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Preliminary Findings</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{progress.partial_synthesis}</p>
            </CardContent>
          </Card>
        )}

        {/* Status Badge */}
        <div className="text-center">
          <Badge variant={progress.status === 'running' ? 'medium' : 'outline'}>
            {progress.status === 'queued' && 'Waiting in queue...'}
            {progress.status === 'running' && 'Actively researching...'}
            {progress.status === 'failed' && 'Research failed'}
          </Badge>
        </div>
      </div>
    </div>
  )
}
