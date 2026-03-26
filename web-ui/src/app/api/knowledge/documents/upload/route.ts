import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL =
  process.env.API_GATEWAY_URL || process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
const KNOWLEDGE_BASE_URL =
  process.env.KNOWLEDGE_BASE_URL ||
  process.env.NEXT_PUBLIC_KNOWLEDGE_BASE_URL ||
  'http://localhost:8004';

const getBaseUrl = () => {
  if (API_GATEWAY_URL) {
    return `${API_GATEWAY_URL}/api/knowledge`;
  }
  return `${KNOWLEDGE_BASE_URL}/api`;
};

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const knowledge_base_id = formData.get('knowledge_base_id') as string | null;
    const tags = formData.get('tags') as string | null;
    const process_async = formData.get('process_async') as string | null;

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    // 构建后端API URL
    let url = `${getBaseUrl()}/documents/upload`;
    const queryParams = new URLSearchParams();
    if (knowledge_base_id) {
      queryParams.append('knowledge_base_id', knowledge_base_id);
    }
    if (tags) {
      queryParams.append('tags', tags);
    }
    if (process_async !== null) {
      queryParams.append('process_async', process_async || 'true');
    }
    if (queryParams.toString()) {
      url += `?${queryParams.toString()}`;
    }

    // 创建新的FormData用于转发
    const uploadFormData = new FormData();
    uploadFormData.append('file', file);

    const response = await fetch(url, {
      method: 'POST',
      body: uploadFormData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to upload document' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to upload document' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error uploading document:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
