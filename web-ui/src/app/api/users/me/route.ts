import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL =
  process.env.API_GATEWAY_URL || process.env.NEXT_PUBLIC_API_GATEWAY_URL || '';
const AUTH_SERVICE_URL =
  process.env.AUTH_SERVICE_URL || process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://localhost:8003';

const trimTrailingSlash = (url: string) => url.replace(/\/+$/, '');

const resolveUsersMeUrl = () => {
  // 网关鉴权用户接口：/api/users/me
  // （网关内部会转发到 auth-service: /users/me）
  if (API_GATEWAY_URL) {
    return `${trimTrailingSlash(API_GATEWAY_URL)}/api/users/me`;
  }

  const authBase = trimTrailingSlash(AUTH_SERVICE_URL);
  // auth-service 路由前缀是：/users/me（不需要额外拼 /auth）
  if (authBase.endsWith('/auth')) return `${authBase}/users/me`;
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
