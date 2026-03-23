import { apiGatewayClient } from './client';

export type AIScenarioStatus = 'draft' | 'submitted';

export interface AIScenario {
  id: string;
  domain: string;
  categories: string[];
  app_company?: string | null;
  platform?: string | null;
  pain_points: string;
  problems_to_solve: string;
  expected_outcomes: string;
  implementation_approach: string;
  technical_route?: string | null;
  plan_schedule: string;
  status: AIScenarioStatus;
  created_by: string;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: string;
  scenario_id: string;
  file_name: string;
  content_type?: string | null;
  size: number;
  created_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateAIScenarioRequest {
  domain: string;
  categories: string[];
  app_company?: string;
  platform?: string;
  pain_points: string;
  problems_to_solve: string;
  expected_outcomes: string;
  implementation_approach: string;
  technical_route?: string;
  plan_schedule: string;
}

export type UpdateAIScenarioRequest = Partial<CreateAIScenarioRequest>;

export async function listAIScenarios(params: {
  page?: number;
  page_size?: number;
  domain?: string;
  status?: AIScenarioStatus;
  keyword?: string;
  mine?: boolean;
}): Promise<Paginated<AIScenario>> {
  const sp = new URLSearchParams();
  if (params.page) sp.set('page', String(params.page));
  if (params.page_size) sp.set('page_size', String(params.page_size));
  if (params.domain) sp.set('domain', params.domain);
  if (params.status) sp.set('status', params.status);
  if (params.keyword) sp.set('keyword', params.keyword);
  if (params.mine !== undefined) sp.set('mine', params.mine ? 'true' : 'false');
  const qs = sp.toString();
  return apiGatewayClient.get<Paginated<AIScenario>>(`/api/ai-scenarios${qs ? `?${qs}` : ''}`);
}

export async function createAIScenario(payload: CreateAIScenarioRequest): Promise<AIScenario> {
  return apiGatewayClient.post<AIScenario>('/api/ai-scenarios', payload);
}

export async function getAIScenario(id: string): Promise<AIScenario> {
  return apiGatewayClient.get<AIScenario>(`/api/ai-scenarios/${id}`);
}

export async function updateAIScenario(id: string, payload: UpdateAIScenarioRequest): Promise<AIScenario> {
  return apiGatewayClient.put<AIScenario>(`/api/ai-scenarios/${id}`, payload);
}

export async function deleteAIScenario(id: string): Promise<void> {
  await apiGatewayClient.delete<void>(`/api/ai-scenarios/${id}`);
}

export async function submitAIScenario(id: string): Promise<{ id: string; status: AIScenarioStatus }> {
  return apiGatewayClient.post<{ id: string; status: AIScenarioStatus }>(`/api/ai-scenarios/${id}/submit`);
}

export async function listAttachments(scenarioId: string): Promise<Attachment[]> {
  return apiGatewayClient.get<Attachment[]>(`/api/ai-scenarios/${scenarioId}/attachments`);
}

export async function deleteAttachment(attachmentId: string): Promise<void> {
  await apiGatewayClient.delete<void>(`/api/ai-scenarios/attachments/${attachmentId}`);
}

export async function uploadAttachments(scenarioId: string, files: File[]): Promise<Attachment[]> {
  const fd = new FormData();
  files.forEach((f) => fd.append('files', f));
  return apiGatewayClient.request<Attachment[]>(`/api/ai-scenarios/${scenarioId}/attachments`, {
    method: 'POST',
    body: fd,
  });
}

export function getAttachmentDownloadUrl(attachmentId: string): string {
  return `/api/ai-scenarios/attachments/${attachmentId}/download`;
}

