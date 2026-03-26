'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = Number(process.env.PORT || 4096);
const WEB_ROOT = process.env.WEB_ROOT || '/app-web';
const API_HOST = process.env.API_HOST || 'opencode-api';
const API_PORT = Number(process.env.API_PORT || 4096);

const API_PREFIX = new RegExp(
  '^/(global|project|pty|config|experimental|session|permission|question|provider|mcp|tui|instance|path|vcs|command|log|agent|skill|lsp|formatter|event|file|find)(/|$)'
);
const SESSION_ID_RE = /^\/session\/(ses[^/?#]+)/;
const sessionMap = new Map();
const sessionPending = new Map();

const MIME = {
  '.html': 'text/html; charset=UTF-8',
  '.js': 'application/javascript',
  '.mjs': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.ico': 'image/x-icon',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.map': 'application/json',
};

const CSP = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; media-src 'self' data:; connect-src 'self' data:";

function setCommonHeaders(res) {
  res.setHeader('Content-Security-Policy', CSP);
}

function serveFile(filePath, res) {
  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME[ext] || 'application/octet-stream';
  setCommonHeaders(res);
  res.statusCode = 200;
  res.setHeader('Content-Type', contentType);
  fs.createReadStream(filePath).pipe(res);
}

function tryServeStatic(req, res) {
  if (req.method !== 'GET' && req.method !== 'HEAD') return false;
  const rawUrl = req.url || '/';
  const urlPath = rawUrl.split('?')[0] || '/';
  let safePath = decodeURIComponent(urlPath);
  safePath = path.posix.normalize(safePath);
  if (!safePath.startsWith('/')) safePath = `/${safePath}`;
  const relPath = safePath.replace(/^\/+/, '');
  let filePath = path.join(WEB_ROOT, relPath);
  if (safePath === '/' || safePath === '') {
    filePath = path.join(WEB_ROOT, 'index.html');
  }
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    serveFile(filePath, res);
    return true;
  }
  return false;
}

function serveIndex(res) {
  const indexPath = path.join(WEB_ROOT, 'index.html');
  if (fs.existsSync(indexPath)) {
    serveFile(indexPath, res);
    return true;
  }
  return false;
}

function proxyRequest(req, res) {
  return collectRequestBody(req)
    .then((body) => proxyWithFallback(req, res, body))
    .catch((err) => {
      res.statusCode = 502;
      setCommonHeaders(res);
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ error: 'proxy_error', message: err.message }));
    });
}

const server = http.createServer((req, res) => {
  const rawUrl = req.url || '/';
  const urlPath = rawUrl.split('?')[0] || '/';

  if (API_PREFIX.test(urlPath)) {
    proxyRequest(req, res);
    return;
  }

  if (tryServeStatic(req, res)) {
    return;
  }

  if (serveIndex(res)) {
    return;
  }

  proxyRequest(req, res);
});

function extractSessionID(urlPath) {
  const match = SESSION_ID_RE.exec(urlPath);
  return match ? match[1] : undefined;
}

function replaceSessionID(rawUrl, sessionID) {
  return rawUrl.replace(SESSION_ID_RE, `/session/${sessionID}`);
}

function collectRequestBody(req) {
  if (req.method === 'GET' || req.method === 'HEAD') return Promise.resolve(Buffer.alloc(0));
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

function buildProxyOptions(req, targetUrl, body) {
  const headers = { ...req.headers };
  headers.host = `${API_HOST}:${API_PORT}`;
  if (body && body.length) {
    headers['content-length'] = String(body.length);
    delete headers['transfer-encoding'];
  } else {
    delete headers['content-length'];
    delete headers['transfer-encoding'];
  }

  return {
    hostname: API_HOST,
    port: API_PORT,
    method: req.method,
    path: targetUrl,
    headers,
  };
}

function sendRequest(options, body) {
  return new Promise((resolve, reject) => {
    const proxy = http.request(options, (proxyRes) => resolve(proxyRes));
    proxy.on('error', reject);
    if (body && body.length) proxy.write(body);
    proxy.end();
  });
}

function isJsonResponse(proxyRes) {
  const contentType = proxyRes.headers['content-type'];
  if (!contentType) return false;
  if (Array.isArray(contentType)) return contentType.some((v) => v.includes('application/json'));
  return String(contentType).includes('application/json');
}

function rewriteBodyText(bodyText, originalSessionID, mappedSessionID) {
  if (!originalSessionID || !mappedSessionID) return bodyText;
  if (!bodyText || bodyText.indexOf(mappedSessionID) === -1) return bodyText;
  return bodyText.split(mappedSessionID).join(originalSessionID);
}

function sendResponse(proxyRes, res, rewrite) {
  if (!rewrite) {
    res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
    return;
  }

  const chunks = [];
  proxyRes.on('data', (chunk) => chunks.push(chunk));
  proxyRes.on('end', () => {
    const bodyBuffer = Buffer.concat(chunks);
    const bodyText = bodyBuffer.toString('utf8');
    const nextBody = rewrite.bodyText
      ? rewriteBodyText(bodyText, rewrite.originalSessionID, rewrite.mappedSessionID)
      : bodyText;
    const headers = { ...proxyRes.headers };
    headers['content-length'] = Buffer.byteLength(nextBody);
    res.writeHead(proxyRes.statusCode || 502, headers);
    res.end(nextBody);
  });
}

function buildSessionCreatePath(rawUrl) {
  try {
    const url = new URL(rawUrl, 'http://localhost');
    const directory = url.searchParams.get('directory');
    if (directory) return `/session?directory=${encodeURIComponent(directory)}`;
  } catch {
    // ignore parse errors
  }
  return '/session';
}

function createSession(rawUrl, headers) {
  const payload = Buffer.from('{}');
  const createHeaders = { ...headers };
  createHeaders.host = `${API_HOST}:${API_PORT}`;
  createHeaders['content-type'] = 'application/json';
  createHeaders['content-length'] = String(payload.length);
  delete createHeaders['transfer-encoding'];

  const options = {
    hostname: API_HOST,
    port: API_PORT,
    method: 'POST',
    path: buildSessionCreatePath(rawUrl),
    headers: createHeaders,
  };

  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf8');
        if (!res.statusCode || res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`create session failed: ${res.statusCode} ${body}`));
          return;
        }
        try {
          const data = JSON.parse(body);
          if (!data || !data.id) throw new Error('create session missing id');
          resolve(data.id);
        } catch (err) {
          reject(err);
        }
      });
    });

    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

function getOrCreateSession(originalSessionID, rawUrl, headers, forceNew) {
  if (!forceNew) {
    const existing = sessionMap.get(originalSessionID);
    if (existing) return Promise.resolve(existing);
    const pending = sessionPending.get(originalSessionID);
    if (pending) return pending;
  }

  const create = createSession(rawUrl, headers)
    .then((newID) => {
      sessionMap.set(originalSessionID, newID);
      sessionPending.delete(originalSessionID);
      return newID;
    })
    .catch((err) => {
      sessionPending.delete(originalSessionID);
      throw err;
    });

  sessionPending.set(originalSessionID, create);
  return create;
}

async function proxyWithFallback(req, res, body) {
  const rawUrl = req.url || '/';
  const urlPath = rawUrl.split('?')[0] || '/';
  const originalSessionID = extractSessionID(urlPath);

  const mapped = originalSessionID ? sessionMap.get(originalSessionID) : undefined;
  const targetUrl = mapped ? replaceSessionID(rawUrl, mapped) : rawUrl;
  const options = buildProxyOptions(req, targetUrl, body);

  try {
    const proxyRes = await sendRequest(options, body);
    if (proxyRes.statusCode === 404 && originalSessionID) {
      proxyRes.resume();
      const newID = await getOrCreateSession(originalSessionID, rawUrl, req.headers, !!mapped);
      const retryUrl = replaceSessionID(rawUrl, newID);
      const retryOptions = buildProxyOptions(req, retryUrl, body);
      const retryRes = await sendRequest(retryOptions, body);
      const rewrite = isJsonResponse(retryRes)
        ? { originalSessionID, mappedSessionID: newID, bodyText: true }
        : undefined;
      sendResponse(retryRes, res, rewrite);
      return;
    }

    const rewrite = mapped && isJsonResponse(proxyRes)
      ? { originalSessionID, mappedSessionID: mapped, bodyText: true }
      : undefined;
    sendResponse(proxyRes, res, rewrite);
  } catch (err) {
    res.statusCode = 502;
    setCommonHeaders(res);
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ error: 'proxy_error', message: err.message }));
  }
}

server.listen(PORT, '0.0.0.0', () => {
  // eslint-disable-next-line no-console
  console.log(`opencode-web-proxy listening on http://0.0.0.0:${PORT}`);
});
