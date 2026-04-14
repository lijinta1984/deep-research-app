import { Routes, Route } from 'react-router-dom'
import Home from '@/pages/Home'
import Progress from '@/pages/Progress'
import Result from '@/pages/Result'
import History from '@/pages/History'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/research/:jobId/progress" element={<Progress />} />
      <Route path="/research/:jobId/result" element={<Result />} />
      <Route path="/history" element={<History />} />
    </Routes>
  )
}
