import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

function decodeBase64Url(input: string) {
  try {
    const normalized = input.replace(/-/g, '+').replace(/_/g, '/');
    const pad = normalized.length % 4 ? '='.repeat(4 - (normalized.length % 4)) : '';
    return Buffer.from(normalized + pad, 'base64').toString('utf8');
  } catch {
    return '';
  }
}

function looksLikePath(decoded: string) {
  if (!decoded) return false;
  if (decoded.startsWith('.') || decoded.startsWith('/') || decoded.startsWith('~')) return true;
  return decoded.includes('/') || decoded.includes('\\');
}

export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;

  if (pathname === '/' && searchParams.get('opencode') === '1') {
    const nextUrl = request.nextUrl.clone();
    nextUrl.pathname = '/opencode-proxy';
    return NextResponse.rewrite(nextUrl);
  }

  const sessionCookie = request.cookies.get('oc_proxy')?.value;
  if (sessionCookie) {
    const segment = pathname.split('/').filter(Boolean)[0];
    if (segment) {
      const decoded = decodeBase64Url(segment);
      if (looksLikePath(decoded)) {
        const nextUrl = request.nextUrl.clone();
        nextUrl.pathname = `/opencode-proxy${pathname}`;
        return NextResponse.rewrite(nextUrl);
      }
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/:path*',
};
