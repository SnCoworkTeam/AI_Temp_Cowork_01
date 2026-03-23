import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL =
  process.env.API_GATEWAY_URL || process.env.NEXT_PUBLIC_API_GATEWAY_URL || '';
const AUTH_SERVICE_URL =
  process.env.AUTH_SERVICE_URL || process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://localhost:8003';

const trimTrailingSlash = (url: string) => url.replace(/\/+$/, '');

const resolveAuthBaseUrl = () => {
  if (API_GATEWAY_URL) {
    return `${trimTrailingSlash(API_GATEWAY_URL)}/api/auth`;
  }
  const authBase = trimTrailingSlash(AUTH_SERVICE_URL);
  if (authBase.includes('/api/auth') || authBase.endsWith('/auth')) {
    return authBase;
  }
  return `${authBase}/auth`;
};

const buildTargetUrl = (pathSegments: string[], search: string) => {
  const base = resolveAuthBaseUrl();
  const encodedPath = pathSegments.map((segment) => encodeURIComponent(segment)).join('/');
  const suffix = encodedPath ? `/${encodedPath}` : '';
  return `${base}${suffix}${search}`;
};

const hasRequestBody = (method: string) => !['GET', 'HEAD'].includes(method);

const proxy = async (request: NextRequest, pathSegments: string[]) => {
  const targetUrl = buildTargetUrl(pathSegments, request.nextUrl.search);
  const headers = new Headers(request.headers);
  headers.delete('host');

  const init: RequestInit = { method: request.method, headers };

  if (hasRequestBody(request.method)) {
    const body = await request.text();
    if (body) {
      init.body = body;
    }
  }

  const response = await fetch(targetUrl, init);
  const contentType = response.headers.get('content-type') || '';
  const responseText = await response.text();

  if (contentType.includes('application/json')) {
    let data: any = {};
    if (responseText) {
      try {
        data = JSON.parse(responseText);
      } catch {
        data = { detail: responseText };
      }
    }
    return NextResponse.json(data, { status: response.status });
  }

  return new NextResponse(responseText, {
    status: response.status,
    headers: {
      'content-type': contentType || 'text/plain',
    },
  });
};

export async function GET(
  request: NextRequest,
  { params }: { params: { path?: string[] } }
) {
  return proxy(request, params.path ?? []);
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path?: string[] } }
) {
  return proxy(request, params.path ?? []);
}
