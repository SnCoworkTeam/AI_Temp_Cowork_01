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

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const status = searchParams.get('status');
    const search = searchParams.get('search');
    const page = searchParams.get('page') || '1';
    const pageSize = searchParams.get('page_size') || '20';

    // 构建后端API URL
    let url = `${getBaseUrl()}/knowledge-bases?page=${page}&page_size=${pageSize}`;
    if (status) {
      url += `&status=${encodeURIComponent(status)}`;
    }
    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }

    // 调试日志
    console.log('[Knowledge Bases API] Request URL:', url);
    console.log('[Knowledge Bases API] API Gateway URL:', API_GATEWAY_URL);
    console.log('[Knowledge Bases API] Knowledge Base URL:', KNOWLEDGE_BASE_URL);

    // 添加超时控制
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时（与API Gateway一致）

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
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

        console.error('[Knowledge Bases API] Error response:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData,
        });

        return NextResponse.json(
          {
            error:
              errorData.detail ||
              errorData.message ||
              `Failed to fetch knowledge bases: ${response.statusText}`,
            knowledge_bases: [],
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

      // 确保返回格式包含 knowledge_bases 字段
      return NextResponse.json({
        knowledge_bases: data.knowledge_bases || [],
        total: data.total || 0,
        page: data.page || 1,
        page_size: data.page_size || 20,
        total_pages: data.total_pages || 1,
      });
    } catch (fetchError: any) {
      clearTimeout(timeoutId);

      if (fetchError.name === 'AbortError') {
        console.error('[Knowledge Bases API] Request timeout:', url);
        return NextResponse.json(
          {
            error: 'Request timeout: Backend service is not responding',
            knowledge_bases: [],
            debug: { url, timeout: true },
          },
          { status: 504 }
        );
      }

      // 网络错误或其他错误
      console.error('[Knowledge Bases API] Fetch error:', {
        error: fetchError.message,
        url,
        stack: fetchError.stack,
      });

      return NextResponse.json(
        {
          error: `Failed to connect to backend service: ${fetchError.message}`,
          knowledge_bases: [],
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
    console.error('[Knowledge Bases API] Unexpected error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        knowledge_bases: [],
        debug: { error: error?.message || String(error) },
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      name,
      description,
      embedding_model,
      chunk_strategy,
      chunk_size,
      chunk_overlap,
      settings,
    } = body;

    if (!name) {
      return NextResponse.json({ error: 'Knowledge base name is required' }, { status: 400 });
    }

    // 构建后端API URL
    const url = `${getBaseUrl()}/knowledge-bases`;

    console.log('[Knowledge Bases API] POST Request URL:', url);
    console.log('[Knowledge Bases API] POST Body:', {
      name,
      description,
      embedding_model,
      chunk_strategy,
    });

    // 添加超时控制
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时（与API Gateway一致）

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          description: description || '',
          embedding_model: embedding_model || 'default',
          chunk_strategy: chunk_strategy || 'fixed',
          chunk_size: chunk_size || 1000,
          chunk_overlap: chunk_overlap || 200,
          settings: settings || {},
        }),
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

        console.error('[Knowledge Bases API] POST Error response:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData,
        });

        return NextResponse.json(
          {
            error:
              errorData.detail ||
              errorData.message ||
              `Failed to create knowledge base: ${response.statusText}`,
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
        console.error('[Knowledge Bases API] POST Request timeout:', url);
        return NextResponse.json(
          {
            error: 'Request timeout: Backend service is not responding',
            debug: { url, timeout: true },
          },
          { status: 504 }
        );
      }

      // 网络错误或其他错误
      console.error('[Knowledge Bases API] POST Fetch error:', {
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
    console.error('[Knowledge Bases API] POST Unexpected error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        debug: { error: error?.message || String(error) },
      },
      { status: 500 }
    );
  }
}
