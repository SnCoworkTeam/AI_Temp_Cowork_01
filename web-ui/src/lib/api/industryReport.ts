import { ApiClient } from './client';

const API_BASE =
  process.env.NEXT_PUBLIC_INDUSTRY_REPORT_API_BASE || 'http://localhost:8021/api';

const client = new ApiClient(API_BASE);

export interface Report {
  id: string;
  title: string;
  period_start: string;
  period_end: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  total_rows?: number;
  processed_rows?: number;
  html_content?: string | null;
  file_path?: string | null;
}

export interface GenerateReportRequest {
  title: string;
  period_start: string;
  period_end: string;
  custom_prompt?: string;
}

export async function uploadFile(file: File, type: string): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', type);

  await fetch(`${API_BASE}/upload/`, {
    method: 'POST',
    body: formData,
  }).then(async (res) => {
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(text || `上传失败 (${res.status})`);
    }
  });
}

export async function generateReport(body: GenerateReportRequest): Promise<Report> {
  return client.post<Report>('/reports/generate', body);
}

export async function getReport(id: string): Promise<Report> {
  return client.get<Report>(`/reports/${id}`);
}

