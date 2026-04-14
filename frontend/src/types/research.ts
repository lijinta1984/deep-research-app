export type ConfidenceLevel = 'high' | 'medium' | 'low';
export type Priority = 'high' | 'medium' | 'low';
export type ResearchDepth = 1 | 2 | 3;
export type JobStatus = 'queued' | 'running' | 'complete' | 'failed';

// ── Pass 1 ──────────────────────────────────────────────────────────

export interface KeyFinding {
  claim: string;
  confidence: ConfidenceLevel;
  source_urls: string[];
}

export interface KeyFindingWithMeta extends KeyFinding {
  is_new: boolean;
  resolves_gap: string | null;
}

export interface Contradiction {
  point: string;
  source_a: string;
  source_b: string;
  resolved: boolean;
  resolution: string | null;
}

export interface KnowledgeGap {
  question: string;
  priority: Priority;
  reason: string;
}

export interface Pass1Synthesis {
  overview: string;
  key_findings: KeyFinding[];
  themes: string[];
  contradictions: Contradiction[];
}

export interface Pass1Output {
  synthesis: Pass1Synthesis;
  gaps: KnowledgeGap[];
  pass_complete: boolean;
}

// ── Pass 2 ──────────────────────────────────────────────────────────

export interface ResolvedGap {
  question: string;
  resolution_summary: string;
  confidence: ConfidenceLevel;
}

export interface Pass2Synthesis {
  overview: string;
  key_findings: KeyFindingWithMeta[];
  themes: string[];
  contradictions: Contradiction[];
}

export interface Pass2Output {
  updated_synthesis: Pass2Synthesis;
  gaps_resolved: ResolvedGap[];
  remaining_gaps: KnowledgeGap[];
  pass_complete: boolean;
}

// ── Pass 3 ──────────────────────────────────────────────────────────

export interface ReportSection {
  title: string;
  content: string;
  confidence: ConfidenceLevel;
  confidence_rationale: string;
}

export interface KeyConclusion {
  conclusion: string;
  confidence: ConfidenceLevel;
}

export interface OpenQuestion {
  question: string;
  why_it_matters: string;
}

export interface SourceRecord {
  url: string;
  title: string;
  relevance: ConfidenceLevel;
  found_in_pass: 1 | 2 | 3;
}

export interface ResearchMetadata {
  total_passes: number;
  total_sources_scraped: number;
  total_gaps_identified: number;
  total_gaps_resolved: number;
  research_confidence_overall: ConfidenceLevel;
}

export interface FinalReport {
  executive_summary: string;
  sections: ReportSection[];
  key_conclusions: KeyConclusion[];
  open_questions: OpenQuestion[];
}

export interface Pass3Output {
  report: FinalReport;
  sources: SourceRecord[];
  metadata: ResearchMetadata;
  pass_complete: boolean;
}

// ── Job lifecycle ────────────────────────────────────────────────────

export interface ResearchJobCreate {
  query: string;
  depth: ResearchDepth;
  max_sources: number;
}

export interface ResearchJobResponse {
  job_id: string;
  query: string;
  depth: ResearchDepth;
  max_sources: number;
  status: JobStatus;
  created_at: string;
}

export interface ResearchProgress {
  job_id: string;
  status: JobStatus;
  depth: ResearchDepth;
  progress: number;
  current_pass: number;
  sources_scraped: number;
  gaps_found: number;
  partial_synthesis: string | null;
  error_message: string | null;
}

export interface ScrapedSource {
  url: string;
  title: string;
  markdown_content: string;
  scraped_at: string;
  pass_number: 1 | 2 | 3;
  word_count: number;
  scrape_success: boolean;
}

export interface ResearchJob {
  job_id: string;
  query: string;
  depth: ResearchDepth;
  max_sources: number;
  status: JobStatus;
  created_at: string;
  completed_at: string | null;
  sources: ScrapedSource[];
  pass_1_output: Pass1Output | null;
  pass_2_output: Pass2Output | null;
  pass_3_output: Pass3Output | null;
  error_message: string | null;
}

export interface SearchTreeNode {
  id: string;
  label: string;
  node_type: 'root' | 'query' | 'gap' | 'source';
  pass_number: 1 | 2 | 3;
  parent_id: string | null;
  url: string | null;
  confidence: ConfidenceLevel | null;
  children: SearchTreeNode[];
}

export interface ExportRequest {
  job_id: string;
  format: 'docx' | 'markdown';
  include_sources: boolean;
  include_open_questions: boolean;
}
