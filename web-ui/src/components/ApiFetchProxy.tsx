'use client';

import { useEffect } from 'react';
import { getAccessToken, refreshAccessToken } from '@/lib/auth';

const trimTrailingSlash = (url: string) => url.replace(/\/+$/, '');

type Mapping = {
  from: string;
  to: string;
};

const buildMappings = (): Mapping[] => {
  const mappings: Mapping[] = [];
  const apiGateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL || '';
  const knowledgeBase = process.env.NEXT_PUBLIC_KNOWLEDGE_BASE_URL || '';

  if (apiGateway) {
    const base = trimTrailingSlash(apiGateway);
    mappings.push({ from: `${base}/api/`, to: '/api/' });
  }

  if (knowledgeBase) {
    const base = trimTrailingSlash(knowledgeBase);
    mappings.push({ from: `${base}/api/`, to: '/api/knowledge/' });
  }

  return mappings;
};

const rewriteUrl = (url: string, mappings: Mapping[]): string | null => {
  for (const mapping of mappings) {
    if (url.startsWith(mapping.from)) {
      return `${mapping.to}${url.slice(mapping.from.length)}`;
    }
  }
  return null;
};

const isApiPath = (url: string) => {
  try {
    const resolved = new URL(url, window.location.origin);
    return resolved.pathname.startsWith('/api/');
  } catch {
    return false;
  }
};

const shouldSkipRefresh = (url: string) => {
  try {
    const resolved = new URL(url, window.location.origin);
    return (
      resolved.pathname.startsWith('/api/auth/login') ||
      resolved.pathname.startsWith('/api/auth/refresh') ||
      resolved.pathname.startsWith('/api/auth/sso')
    );
  } catch {
    return false;
  }
};

export default function ApiFetchProxy() {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mappings = buildMappings();
    if (mappings.length === 0) return;

    const originalFetch = window.fetch.bind(window);

    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init);
      const originalUrl = request.url;

      const rewritten = rewriteUrl(originalUrl, mappings);
      const targetUrl = rewritten || originalUrl;
      const targetIsApi = isApiPath(targetUrl);

      const buildRequest = async (overrideToken?: string) => {
        const headers = new Headers(request.headers);
        if (targetIsApi) {
          if (overrideToken) {
            headers.set('Authorization', `Bearer ${overrideToken}`);
          } else if (!headers.has('Authorization')) {
            const token = getAccessToken();
            if (token) {
              headers.set('Authorization', `Bearer ${token}`);
            }
          }
        }

        let body: BodyInit | undefined;
        if (!['GET', 'HEAD'].includes(request.method)) {
          try {
            const buffer = await request.clone().arrayBuffer();
            body = buffer.byteLength > 0 ? buffer : undefined;
          } catch {
            body = undefined;
          }
        }

        return new Request(targetUrl, {
          method: request.method,
          headers,
          body,
          mode: request.mode,
          credentials: request.credentials,
          cache: request.cache,
          redirect: request.redirect,
          referrer: request.referrer,
          referrerPolicy: request.referrerPolicy,
          integrity: request.integrity,
          keepalive: request.keepalive,
          signal: request.signal,
        });
      };

      let response = await originalFetch(await buildRequest());
      if (response.status !== 401 || !isApiPath(targetUrl) || shouldSkipRefresh(targetUrl)) {
        return response;
      }

      const newToken = await refreshAccessToken();
      if (!newToken) {
        return response;
      }

      response = await originalFetch(await buildRequest(newToken));
      return response;
    };

    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  return null;
}
