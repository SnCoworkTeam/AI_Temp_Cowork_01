import crypto from 'crypto';

export const OPENCODE_PROXY_COOKIE = 'oc_proxy';

export function getProxySecret(): string {
  return process.env.OPENCODE_PROXY_SECRET || process.env.OPENCODE_SERVER_PASSWORD || '';
}

export function getProxyTTLSeconds(): number {
  const raw = process.env.OPENCODE_PROXY_TTL_SECONDS || '900';
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 900;
}

export function signProxySession(payload: Record<string, unknown>): string {
  const secret = getProxySecret();
  if (!secret) throw new Error('OPENCODE_PROXY_SECRET is not set');

  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const sig = crypto.createHmac('sha256', secret).update(body).digest('base64url');
  return `${body}.${sig}`;
}

export function verifyProxySession(token: string): Record<string, unknown> | null {
  const secret = getProxySecret();
  if (!secret) return null;

  const [body, sig] = token.split('.');
  if (!body || !sig) return null;

  const expected = crypto.createHmac('sha256', secret).update(body).digest('base64url');
  if (expected !== sig) return null;

  try {
    const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf8')) as Record<string, unknown>;
    const exp = typeof payload.exp === 'number' ? payload.exp : 0;
    if (!exp || Date.now() > exp) return null;
    return payload;
  } catch {
    return null;
  }
}

export function getOpencodeUpstreamUrl(): string {
  return process.env.OPENCODE_UPSTREAM_URL || 'http://opencode:4096';
}

export function getOpencodeBasicAuthHeader(): string | null {
  const user = process.env.OPENCODE_SERVER_USERNAME || '';
  const pass = process.env.OPENCODE_SERVER_PASSWORD || '';
  if (!user || !pass) return null;
  const encoded = Buffer.from(`${user}:${pass}`).toString('base64');
  return `Basic ${encoded}`;
}
