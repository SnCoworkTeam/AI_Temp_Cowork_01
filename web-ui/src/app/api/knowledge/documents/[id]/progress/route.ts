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

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;

    if (!id) {
      return NextResponse.json({ error: 'Document ID is required' }, { status: 400 });
    }

    const url = `${getBaseUrl()}/documents/${id}/progress`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // 如果404，说明进度信息不存在（可能已完成或未开始）
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Progress not found', stage: 'unknown' },
          { status: 404 }
        );
      }

      const error = await response.json().catch(() => ({ detail: 'Failed to fetch progress' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to fetch progress' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error fetching document progress:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
