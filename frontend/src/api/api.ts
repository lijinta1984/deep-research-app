import type {
  ExportRequest,
  ResearchJob,
  ResearchJobCreate,
  ResearchJobResponse,
  ResearchProgress,
  SearchTreeNode,
} from '@/types/research';

const BASE_URL = '/api/research';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const errorBody = await response.text().catch(() => 'Unknown error');
    throw new Error(`API error ${response.status}: ${errorBody}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  startResearch: (body: ResearchJobCreate): Promise<ResearchJobResponse> =>
    fetchJSON<ResearchJobResponse>(`${BASE_URL}/start`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getStatus: (jobId: string): Promise<ResearchProgress> =>
    fetchJSON<ResearchProgress>(`${BASE_URL}/status/${jobId}`),

  getResult: (jobId: string): Promise<ResearchJob> =>
    fetchJSON<ResearchJob>(`${BASE_URL}/result/${jobId}`),

  getHistory: (): Promise<ResearchJobResponse[]> =>
    fetchJSON<ResearchJobResponse[]>(`${BASE_URL}/history`),

  deleteJob: (jobId: string): Promise<{ status: string }> =>
    fetchJSON<{ status: string }>(`${BASE_URL}/${jobId}`, {
      method: 'DELETE',
    }),

  getSearchTree: (jobId: string): Promise<SearchTreeNode> =>
    fetchJSON<SearchTreeNode>(`${BASE_URL}/tree/${jobId}`),

  exportReport: async (jobId: string, body: ExportRequest): Promise<Blob> => {
    const response = await fetch(`${BASE_URL}/export/${jobId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }
    return response.blob();
  },
};
