import { NextResponse } from 'next/server';
import { getProxyTTLSeconds, getProxySecret, OPENCODE_PROXY_COOKIE, signProxySession } from '@/lib/opencodeProxy';

export async function POST(request: Request) {
  const authHeader = request.headers.get('authorization') || '';
  const token = authHeader.startsWith('Bearer ') ? authHeader.slice('Bearer '.length) : '';

  if (!token) {
    return NextResponse.json({ error: 'missing_token' }, { status: 401 });
  }

  const authServiceUrl = process.env.AUTH_SERVICE_URL;
  if (!authServiceUrl) {
    return NextResponse.json({ error: 'AUTH_SERVICE_URL not configured' }, { status: 500 });
  }

  const verifyResponse = await fetch(`${authServiceUrl}/users/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: 'no-store',
  });

  if (!verifyResponse.ok) {
    return NextResponse.json({ error: 'invalid_token' }, { status: 401 });
  }

  const secret = getProxySecret();
  if (!secret) {
    return NextResponse.json({ error: 'OPENCODE_PROXY_SECRET not configured' }, { status: 500 });
  }

  const ttlSeconds = getProxyTTLSeconds();
  const expiresAt = Date.now() + ttlSeconds * 1000;
  const sessionToken = signProxySession({ exp: expiresAt });

  const response = NextResponse.json({ ok: true });
  response.cookies.set({
    name: OPENCODE_PROXY_COOKIE,
    value: sessionToken,
    httpOnly: true,
    sameSite: 'lax',
    path: '/',
    maxAge: ttlSeconds,
  });
  return response;
}
