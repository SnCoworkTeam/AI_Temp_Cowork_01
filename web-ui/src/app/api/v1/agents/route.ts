import { NextRequest, NextResponse } from 'next/server';

// 在服务器端（Next.js API路由）使用Docker服务名
// 优先使用环境变量，否则使用Docker服务名（在容器内访问）
const getAgentServiceUrl = () => {
  // 服务器端环境变量（Docker网络内）
  if (process.env.AGENT_SERVICE_URL) {
    return process.env.AGENT_SERVICE_URL;
  }
  // 默认使用Docker服务名（在容器内）
  return 'http://agent-service:8010';
};

const AGENT_SERVICE_URL = getAgentServiceUrl();

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const status = searchParams.get('status');
    const capability = searchParams.get('capability');
    const limit = searchParams.get('limit') || '100';
    const offset = searchParams.get('offset') || '0';

    // 构建查询参数
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (capability) params.append('capability', capability);
    params.append('limit', limit);
    params.append('offset', offset);

    const url = `${AGENT_SERVICE_URL}/api/v1/agents?${params.toString()}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error(`Agent service error: ${response.status}`);
    }

    const data = await response.json();

    // 适配前端期望的格式
    return NextResponse.json({
      agents: Array.isArray(data) ? data : [],
      total: Array.isArray(data) ? data.length : 0,
    });
  } catch (error) {
    console.error('Failed to fetch agents:', error);
    return NextResponse.json(
      {
        agents: [],
        total: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${AGENT_SERVICE_URL}/api/v1/agents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Agent service error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to create agent:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
