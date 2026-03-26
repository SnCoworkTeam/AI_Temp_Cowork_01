import { NextRequest, NextResponse } from 'next/server';

// 服务器端环境变量（Docker 网络内访问）
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

export async function PATCH(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;
    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status');

    if (!status) {
      return NextResponse.json({ error: 'status parameter is required' }, { status: 400 });
    }

    // 验证状态值
    const validStatuses = ['draft', 'active', 'inactive', 'archived'];
    if (!validStatuses.includes(status)) {
      return NextResponse.json(
        { error: `Invalid status. Must be one of: ${validStatuses.join(', ')}` },
        { status: 400 }
      );
    }

    const response = await fetch(`${getBaseUrl()}/workflows/${id}/status?status=${status}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: 'Failed to update workflow status' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to update workflow status' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error updating workflow status:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
