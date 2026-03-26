import { NextRequest, NextResponse } from 'next/server';

// 服务器端环境变量（Docker 网络内访问）
const API_GATEWAY_URL =
  process.env.API_GATEWAY_URL || process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
const KNOWLEDGE_BASE_URL =
  process.env.KNOWLEDGE_BASE_URL ||
  process.env.NEXT_PUBLIC_KNOWLEDGE_BASE_URL ||
  'http://localhost:8004';

// 构建基础 URL：如果配置了 API Gateway，使用它；否则直接使用 knowledge-base
const getBaseUrl = () => {
  if (API_GATEWAY_URL) {
    return `${API_GATEWAY_URL}/api/knowledge`;
  }
  return `${KNOWLEDGE_BASE_URL}/api`;
};

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;

    // 构建后端API URL
    const url = `${getBaseUrl()}/knowledge-bases/${id}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: 'Failed to fetch knowledge base' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to fetch knowledge base' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching knowledge base:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;
    const body = await request.json();

    // 构建后端API URL
    const url = `${getBaseUrl()}/knowledge-bases/${id}`;

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: 'Failed to update knowledge base' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to update knowledge base' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error updating knowledge base:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;
    const body = await request.json();

    // 构建后端API URL
    const url = `${getBaseUrl()}/knowledge-bases/${id}`;

    const response = await fetch(url, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: 'Failed to update knowledge base' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to update knowledge base' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error patching knowledge base:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;

    // 构建后端API URL
    const url = `${getBaseUrl()}/knowledge-bases/${id}`;

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: 'Failed to delete knowledge base' }));
      return NextResponse.json(
        { error: error.detail || 'Failed to delete knowledge base' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error deleting knowledge base:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
