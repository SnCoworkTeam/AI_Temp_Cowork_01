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

const buildForwardHeaders = (request: NextRequest) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    headers['Authorization'] = authHeader;
  }
  const cookieHeader = request.headers.get('cookie');
  if (cookieHeader) {
    headers['Cookie'] = cookieHeader;
  }
  return headers;
};

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;

    if (!id) {
      return NextResponse.json({ error: 'Document ID is required' }, { status: 400 });
    }

    const url = `${getBaseUrl()}/documents/${id}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: buildForwardHeaders(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText || `HTTP ${response.status}: ${response.statusText}` };
        }

        return NextResponse.json(
          {
            error:
              errorData.detail ||
              errorData.message ||
              `Failed to fetch document: ${response.statusText}`,
            debug: {
              url,
              status: response.status,
              statusText: response.statusText,
            },
          },
          { status: response.status }
        );
      }

      const data = await response.json();
      return NextResponse.json(data);
    } catch (fetchError: any) {
      clearTimeout(timeoutId);

      if (fetchError.name === 'AbortError') {
        return NextResponse.json(
          { error: 'Request timeout: Backend service is not responding', debug: { url, timeout: true } },
          { status: 504 }
        );
      }

      return NextResponse.json(
        {
          error: `Failed to connect to backend service: ${fetchError.message}`,
          debug: {
            url,
            error: fetchError.message,
            suggestion: 'Please check if the backend service is running',
          },
        },
        { status: 502 }
      );
    }
  } catch (error: any) {
    return NextResponse.json(
      { error: 'Internal server error', debug: { error: error?.message || String(error) } },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params;

    if (!id) {
      return NextResponse.json({ error: 'Document ID is required' }, { status: 400 });
    }

    // 构建后端API URL
    const url = `${getBaseUrl()}/documents/${id}`;

    console.log('[Delete Document API] Request URL:', url);
    console.log('[Delete Document API] Document ID:', id);
    console.log('[Delete Document API] API Gateway URL:', API_GATEWAY_URL);
    console.log('[Delete Document API] Knowledge Base URL:', KNOWLEDGE_BASE_URL);

    // 添加超时控制
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时

    try {
      const response = await fetch(url, {
        method: 'DELETE',
        headers: buildForwardHeaders(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText || `HTTP ${response.status}: ${response.statusText}` };
        }

        console.error('[Delete Document API] Error response:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData,
          url,
        });

        return NextResponse.json(
          {
            error:
              errorData.detail ||
              errorData.message ||
              `Failed to delete document: ${response.statusText}`,
            debug: {
              url,
              status: response.status,
              statusText: response.statusText,
            },
          },
          { status: response.status }
        );
      }

      const data = await response.json();
      console.log('[Delete Document API] Success:', data);
      return NextResponse.json(data);
    } catch (fetchError: any) {
      clearTimeout(timeoutId);

      if (fetchError.name === 'AbortError') {
        console.error('[Delete Document API] Request timeout:', url);
        return NextResponse.json(
          {
            error: 'Request timeout: Backend service is not responding',
            debug: { url, timeout: true },
          },
          { status: 504 }
        );
      }

      // 网络错误或其他错误
      console.error('[Delete Document API] Fetch error:', {
        error: fetchError.message,
        url,
        stack: fetchError.stack,
      });

      return NextResponse.json(
        {
          error: `Failed to connect to backend service: ${fetchError.message}`,
          debug: {
            url,
            error: fetchError.message,
            suggestion: 'Please check if the backend service is running',
          },
        },
        { status: 502 }
      );
    }
  } catch (error: any) {
    console.error('[Delete Document API] Unexpected error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        debug: { error: error?.message || String(error) },
      },
      { status: 500 }
    );
  }
}
