import { cookies } from 'next/headers';
import {
  getOpencodeBasicAuthHeader,
  getOpencodeUpstreamUrl,
  OPENCODE_PROXY_COOKIE,
  verifyProxySession,
} from '@/lib/opencodeProxy';

export const dynamic = 'force-dynamic';

const PROXY_BASE_PATH = '/opencode-proxy';
const OPENCODE_DEFAULT_SERVER_KEY = 'opencode.settings.dat:defaultServerUrl';
const OPENCODE_BOOTSTRAP_PATH = `${PROXY_BASE_PATH}/opencode-bootstrap.js`;
const OPENCODE_BOOTSTRAP_SNIPPET = `<script src="${OPENCODE_BOOTSTRAP_PATH}"></script>`;
const OPENCODE_BOOTSTRAP_JS = `(function(){try{var key='${OPENCODE_DEFAULT_SERVER_KEY}';var origin=window.location.origin;var value=origin+'${PROXY_BASE_PATH}';var current=localStorage.getItem(key);if(!current||(current.indexOf(origin)===0&&current!==value)){localStorage.setItem(key,value);}}catch(e){}})();`;

function rewriteHtml(body: string) {
  const rewritten = body.replace(/(href|src|content)=([\"'])\/(?!\/)/g, `$1=$2${PROXY_BASE_PATH}/`);
  const headMatch = rewritten.match(/<head[^>]*>/i);
  if (!headMatch || headMatch.index === undefined) return `${OPENCODE_BOOTSTRAP_SNIPPET}${rewritten}`;
  const insertAt = headMatch.index + headMatch[0].length;
  return `${rewritten.slice(0, insertAt)}${OPENCODE_BOOTSTRAP_SNIPPET}${rewritten.slice(insertAt)}`;
}

function rewriteCss(body: string) {
  const rewritten = body.replace(/url\(\s*(['"]?)\/(?!\/)/g, `url($1${PROXY_BASE_PATH}/`);
  return rewritten.replace(/@import\s+(['"])\/(?!\/)/g, `@import $1${PROXY_BASE_PATH}/`);
}

function rewriteJavascript(body: string) {
  return body.replace(/([\"'`])\/assets\//g, `$1${PROXY_BASE_PATH}/assets/`);
}

async function handleProxy(request: Request, params: { path?: string[] }) {
  const incomingUrl = new URL(request.url);
  const rawPath = incomingUrl.pathname.startsWith(PROXY_BASE_PATH)
    ? incomingUrl.pathname.slice(PROXY_BASE_PATH.length)
    : incomingUrl.pathname;
  const normalizedPath = rawPath.replace(/^\/+/, '');
  const path = params.path?.join('/') || normalizedPath;
  const isSessionList =
    request.method === 'GET' &&
    (path === 'session' ||
      path.startsWith('session/') ||
      normalizedPath === 'session' ||
      request.url.includes(`${PROXY_BASE_PATH}/session`));
  const isPublicGet =
    request.method === 'GET' &&
    (path === 'opencode-bootstrap.js' ||
      path === 'site.webmanifest' ||
      path.startsWith('assets/') ||
      path === 'global/event' ||
      path === 'global/health');

  const cookieStore = cookies();
  const sessionToken = cookieStore.get(OPENCODE_PROXY_COOKIE)?.value || '';
  const session = sessionToken ? verifyProxySession(sessionToken) : null;

  if (!session && isSessionList) {
    return new Response('[]', {
      status: 200,
      headers: {
        'content-type': 'application/json; charset=utf-8',
        'cache-control': 'no-store',
      },
    });
  }

  if (!session && !isPublicGet) {
    return new Response('Unauthorized', { status: 401 });
  }

  const upstreamBase = getOpencodeUpstreamUrl().replace(/\/+$/, '');

  if (path === 'opencode-bootstrap.js') {
    return new Response(OPENCODE_BOOTSTRAP_JS, {
      status: 200,
      headers: {
        'content-type': 'application/javascript; charset=utf-8',
        'cache-control': 'no-store',
      },
    });
  }
  const targetUrl = `${upstreamBase}/${path}${incomingUrl.search}`;

  const headers = new Headers(request.headers);
  headers.delete('host');
  headers.delete('cookie');
  headers.delete('authorization');

  const basicAuth = getOpencodeBasicAuthHeader();
  if (basicAuth) {
    headers.set('authorization', basicAuth);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: 'manual',
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = await request.arrayBuffer();
  }

  const upstreamResponse = await fetch(targetUrl, init);
  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.delete('www-authenticate');

  const location = responseHeaders.get('location');
  if (location?.startsWith('/')) {
    responseHeaders.set('location', `${PROXY_BASE_PATH}${location}`);
  }

  const contentType = responseHeaders.get('content-type') || '';

  if (request.method === 'GET' && path === 'session') {
    const bodyText = await upstreamResponse.text();
    let data: unknown = [];
    if (bodyText) {
      try {
        data = JSON.parse(bodyText);
      } catch {
        data = null;
      }
    }
    if (!Array.isArray(data)) {
      return new Response('[]', {
        status: 200,
        headers: {
          'content-type': 'application/json; charset=utf-8',
          'cache-control': 'no-store',
        },
      });
    }
    responseHeaders.set('content-length', String(Buffer.byteLength(bodyText)));
    return new Response(bodyText, { status: upstreamResponse.status, headers: responseHeaders });
  }

  if (contentType.includes('text/html')) {
    const bodyText = await upstreamResponse.text();
    const rewritten = rewriteHtml(bodyText);
    responseHeaders.set('content-length', String(Buffer.byteLength(rewritten)));
    return new Response(rewritten, { status: upstreamResponse.status, headers: responseHeaders });
  }

  if (contentType.includes('text/css')) {
    const bodyText = await upstreamResponse.text();
    const rewritten = rewriteCss(bodyText);
    responseHeaders.set('content-length', String(Buffer.byteLength(rewritten)));
    return new Response(rewritten, { status: upstreamResponse.status, headers: responseHeaders });
  }

  if (contentType.includes('javascript')) {
    const bodyText = await upstreamResponse.text();
    const rewritten = rewriteJavascript(bodyText);
    responseHeaders.set('content-length', String(Buffer.byteLength(rewritten)));
    return new Response(rewritten, { status: upstreamResponse.status, headers: responseHeaders });
  }

  return new Response(upstreamResponse.body, { status: upstreamResponse.status, headers: responseHeaders });
}

export async function GET(request: Request, ctx: { params: { path?: string[] } }) {
  return handleProxy(request, ctx.params);
}

export async function POST(request: Request, ctx: { params: { path?: string[] } }) {
  return handleProxy(request, ctx.params);
}

export async function PUT(request: Request, ctx: { params: { path?: string[] } }) {
  return handleProxy(request, ctx.params);
}

export async function PATCH(request: Request, ctx: { params: { path?: string[] } }) {
  return handleProxy(request, ctx.params);
}

export async function DELETE(request: Request, ctx: { params: { path?: string[] } }) {
  return handleProxy(request, ctx.params);
}

export async function OPTIONS(request: Request, ctx: { params: { path?: string[] } }) {
  return handleProxy(request, ctx.params);
}
