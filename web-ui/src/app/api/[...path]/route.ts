import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL =
  process.env.API_GATEWAY_URL || process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';

const trimTrailingSlash = (url: string) => url.replace(/\/+$/, '');

const buildTargetUrl = (pathSegments: string[], search: string) => {
  const base = trimTrailingSlash(API_GATEWAY_URL);
  const encodedPath = pathSegments.map((segment) => encodeURIComponent(segment)).join('/');
  const suffix = encodedPath ? `/${encodedPath}` : '';
  return `${base}/api${suffix}${search}`;
};

const hasRequestBody = (method: string) => !['GET', 'HEAD'].includes(method);

const proxy = async (request: NextRequest, pathSegments: string[]) => {
  const targetUrl = buildTargetUrl(pathSegments, request.nextUrl.search);
  const headers = new Headers(request.headers);
  headers.delete('host');

  const init: RequestInit = { method: request.method, headers };

  if (hasRequestBody(request.method)) {
    const body = await request.arrayBuffer();
    if (body.byteLength > 0) {
      init.body = body;
    }
  }

  const response = await fetch(targetUrl, init);
  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    const responseText = await response.text();
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

  const responseBody = await response.arrayBuffer();
  return new NextResponse(responseBody, {
    status: response.status,
    headers: {
      'content-type': contentType || 'application/octet-stream',
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

export async function PUT(
  request: NextRequest,
  { params }: { params: { path?: string[] } }
) {
  return proxy(request, params.path ?? []);
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { path?: string[] } }
) {
  return proxy(request, params.path ?? []);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path?: string[] } }
) {
  return proxy(request, params.path ?? []);
}

export async function OPTIONS(
  request: NextRequest,
  { params }: { params: { path?: string[] } }
) {
  return proxy(request, params.path ?? []);
}
