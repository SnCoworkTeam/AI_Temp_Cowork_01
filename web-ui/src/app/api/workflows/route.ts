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

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const status = searchParams.get('status');

    // 构建后端API URL
    let url = `${getBaseUrl()}/workflows`;
    if (status) {
      url += `?status=${status}`;
    }

    // 调试日志
    console.log('[Workflow API] Request URL:', url);
    console.log('[Workflow API] API_GATEWAY_URL:', process.env.API_GATEWAY_URL);
    console.log('[Workflow API] WORKFLOW_ENGINE_URL:', process.env.WORKFLOW_ENGINE_URL);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch workflows' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to fetch workflows' },
        { status: response.status }
      );
    }

    const data = await response.json();

    // 转换数据格式以匹配前端期望
    // WorkflowListResponse 格式: { workflows: [], total: 0, page: 1, page_size: 20 }
    // 前端期望: { workflows: [] }
    if (data.workflows) {
      return NextResponse.json({
        workflows: data.workflows,
      });
    }

    // 兼容旧格式（直接返回数组）
    return NextResponse.json({
      workflows: Array.isArray(data) ? data : [],
    });
  } catch (error) {
    console.error('Error fetching workflows:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${getBaseUrl()}/workflows`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to create workflow' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to create workflow' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error creating workflow:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
