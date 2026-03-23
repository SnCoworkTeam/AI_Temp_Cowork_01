import { NextRequest, NextResponse } from 'next/server';

// 服务器端环境变量（Docker 网络内访问）
// 优先使用服务器端环境变量（用于 Docker 容器内通信）
const API_GATEWAY_URL = process.env.API_GATEWAY_URL || process.env.NEXT_PUBLIC_API_GATEWAY_URL;
const WORKFLOW_ENGINE_URL =
  process.env.WORKFLOW_ENGINE_URL ||
  process.env.NEXT_PUBLIC_WORKFLOW_ENGINE_URL ||
  'http://workflow-engine:8002';

// 构建基础 URL：如果配置了 API Gateway，使用它；否则直接使用 workflow-engine
const getBaseUrl = () => {
  if (API_GATEWAY_URL) {
    return API_GATEWAY_URL.endsWith('/api') ? API_GATEWAY_URL : `${API_GATEWAY_URL}/api`;
  }
  return `${WORKFLOW_ENGINE_URL}/api/v1`;
};

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;

    const response = await fetch(`${getBaseUrl()}/workflows/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Workflow not found' }));
      return NextResponse.json(
        { error: error.detail || 'Workflow not found' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching workflow:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;

    const response = await fetch(`${getBaseUrl()}/workflows/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to delete workflow' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to delete workflow' },
        { status: response.status }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting workflow:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
