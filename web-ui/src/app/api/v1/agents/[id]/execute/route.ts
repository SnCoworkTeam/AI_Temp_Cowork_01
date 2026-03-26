import { NextRequest, NextResponse } from 'next/server';

// 在服务器端（Next.js API路由）使用Docker服务名
const getAgentServiceUrl = () => {
  if (process.env.AGENT_SERVICE_URL) {
    return process.env.AGENT_SERVICE_URL;
  }
  return 'http://agent-service:8010';
};

const AGENT_SERVICE_URL = getAgentServiceUrl();

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const body = await request.json();

    const response = await fetch(`${AGENT_SERVICE_URL}/api/v1/agents/${params.id}/execute`, {
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
    console.error('Failed to execute agent:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
