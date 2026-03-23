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
    const { searchParams } = new URL(request.url);
    const page = searchParams.get('page') || '1';
    const pageSize = searchParams.get('page_size') || '100';

    if (!id) {
      return NextResponse.json({ error: 'Document ID is required' }, { status: 400 });
    }

    const url = `${getBaseUrl()}/documents/${id}/chunks?page=${page}&page_size=${pageSize}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

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

        return NextResponse.json(
          {
            error:
              errorData.detail ||
              errorData.message ||
              `Failed to fetch document chunks: ${response.statusText}`,
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
          {
            error: 'Request timeout: Backend service is not responding',
            debug: { url, timeout: true },
          },
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
      {
        error: 'Internal server error',
        debug: { error: error?.message || String(error) },
      },
      { status: 500 }
    );
  }
}
