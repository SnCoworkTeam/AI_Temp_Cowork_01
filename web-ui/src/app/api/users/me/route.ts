import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL =
  process.env.API_GATEWAY_URL || process.env.NEXT_PUBLIC_API_GATEWAY_URL || '';
const AUTH_SERVICE_URL =
  process.env.AUTH_SERVICE_URL || process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://localhost:8003';

const trimTrailingSlash = (url: string) => url.replace(/\/+$/, '');

const resolveUsersMeUrl = () => {
  if (API_GATEWAY_URL) {
    return `${trimTrailingSlash(API_GATEWAY_URL)}/api/users/me`;
  }

  const authBase = trimTrailingSlash(AUTH_SERVICE_URL);
  if (authBase.includes('/api/auth')) {
    const gatewayBase = authBase.replace(/\/api\/auth\/?$/, '');
    return `${gatewayBase}/api/users/me`;
  }
  if (authBase.endsWith('/auth')) {
    const authRoot = authBase.replace(/\/auth\/?$/, '');
    return `${authRoot}/users/me`;
  }
  return `${authBase}/users/me`;
};

export async function GET(request: NextRequest) {
  const targetUrl = resolveUsersMeUrl();
  const headers = new Headers(request.headers);
  headers.delete('host');

  const response = await fetch(targetUrl, { headers });
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
}
