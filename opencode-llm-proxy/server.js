'use strict';

const http = require('http');
const { URL } = require('url');
const crypto = require('crypto');
const path = require('path');

const PORT = Number(process.env.PORT || 18080);
const UPSTREAM_BASE_URL = process.env.UPSTREAM_BASE_URL || 'https://ai.sinochem.com/api/model-service/v1';
const LOG_LEVEL = process.env.LOG_LEVEL || 'info';
const FORCE_TOOL_CHOICE_REQUIRED = process.env.FORCE_TOOL_CHOICE_REQUIRED === '1';

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const LOG_LEVEL_NUM = LEVELS[LOG_LEVEL] ?? LEVELS.info;

function log(level, message, data) {
  if (LEVELS[level] > LOG_LEVEL_NUM) return;
  const payload = data ? ` ${JSON.stringify(data)}` : '';
  process.stdout.write(`[opencode-llm-proxy] ${level.toUpperCase()} ${message}${payload}\n`);
}

function readBody(req) {
  if (req.method === 'GET' || req.method === 'HEAD') return Promise.resolve(Buffer.alloc(0));
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

function buildUpstreamUrl(reqUrl) {
  const incoming = new URL(reqUrl || '/', 'http://localhost');
  const upstream = new URL(UPSTREAM_BASE_URL);
  const basePath = upstream.pathname.replace(/\/+$/, '');
  const incomingPath = incoming.pathname.replace(/\/+$/, '');
  const reqPath = incoming.pathname.replace(/^\/+/, '');
  if (basePath && incomingPath.startsWith(basePath)) {
    upstream.pathname = incomingPath || '/';
  } else {
    upstream.pathname = reqPath ? path.posix.join(basePath, reqPath) : basePath || '/';
  }
  upstream.search = incoming.search;
  return upstream.toString();
}

function buildUpstreamHeaders(reqHeaders, bodyLength) {
  const headers = {};
  for (const [key, value] of Object.entries(reqHeaders || {})) {
    if (value === undefined) continue;
    headers[key.toLowerCase()] = Array.isArray(value) ? value.join(',') : String(value);
  }
  delete headers.host;
  delete headers.connection;
  delete headers['content-length'];
  delete headers['accept-encoding'];
  headers['accept-encoding'] = 'identity';
  if (bodyLength > 0) {
    headers['content-length'] = String(bodyLength);
  }
  return headers;
}

function extractLastUserText(messages) {
  if (!Array.isArray(messages)) return '';
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i] || {};
    if (msg.role !== 'user') continue;
    const content = msg.content;
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) {
      return content
        .filter((part) => part && part.type === 'text' && typeof part.text === 'string')
        .map((part) => part.text)
        .join('\n');
    }
  }
  return '';
}

function shouldForceToolChoice(body) {
  if (!FORCE_TOOL_CHOICE_REQUIRED) return false;
  if (!body) return false;
  if (body.tool_choice != null && body.tool_choice !== 'auto') return false;
  if (!Array.isArray(body.tools) || body.tools.length === 0) return false;
  const model = String(body.model || '');
  if (!/qwen/i.test(model)) return false;
  const userText = extractLastUserText(body.messages);
  if (!userText) return false;
  return /(\b(bash|docker|logs?|command|run|execute|grep|rg|ripgrep|ls|cat|read|write|edit|fix|debug|analyz|trace|inspect|search)\b|执行|运行|命令|日志|报错|错误|排查|修复|分析|查询|查看|搜索|定位)/i.test(
    userText,
  );
}

function isEventStream(contentType) {
  if (!contentType) return false;
  return String(contentType).toLowerCase().includes('text/event-stream');
}

function normalizeToolCalls(choice, state) {
  if (!choice) return;
  if (choice.delta && choice.delta.function_call) {
    const fc = choice.delta.function_call;
    const index = 0;
    const id = state.toolCallIds.get(index) || `call_${state.nextToolCallId++}`;
    state.toolCallIds.set(index, id);
    if (fc.name) {
      state.toolCallNames.set(index, fc.name);
      if (state.toolCallNamesSeen) state.toolCallNamesSeen.add(fc.name);
    }
    const name = fc.name || state.toolCallNames.get(index) || '';

    const args =
      fc.arguments == null
        ? ''
        : typeof fc.arguments === 'string'
          ? fc.arguments
          : JSON.stringify(fc.arguments);
    choice.delta.tool_calls = [
      {
        index,
        id,
        function: {
          name,
          arguments: args,
        },
      },
    ];
    delete choice.delta.function_call;
    state.toolCallSeen = true;
  }

  if (choice.delta && Array.isArray(choice.delta.tool_calls)) {
    choice.delta.tool_calls = choice.delta.tool_calls.map((item, idx) => {
      const index = item.index != null ? item.index : idx;
      const id = item.id || state.toolCallIds.get(index) || `call_${state.nextToolCallId++}`;
      state.toolCallIds.set(index, id);
      if (item.function && item.function.name) {
        state.toolCallNames.set(index, item.function.name);
        if (state.toolCallNamesSeen) state.toolCallNamesSeen.add(item.function.name);
      }
      const name = (item.function && item.function.name) || state.toolCallNames.get(index) || '';
      const rawArgs = item.function && item.function.arguments;
      const args =
        rawArgs == null
          ? ''
          : typeof rawArgs === 'string'
            ? rawArgs
            : JSON.stringify(rawArgs);
      return {
        ...item,
        index,
        id,
        function: {
          name,
          arguments: args,
        },
      };
    });
    state.toolCallSeen = true;
  }

  if (choice.message && choice.message.function_call && !choice.message.tool_calls) {
    const fc = choice.message.function_call;
    const id = `call_${state.nextToolCallId++}`;
    const msgArgs =
      fc.arguments == null
        ? ''
        : typeof fc.arguments === 'string'
          ? fc.arguments
          : JSON.stringify(fc.arguments);
    choice.message.tool_calls = [
      {
        id,
        type: 'function',
        function: {
          name: fc.name || '',
          arguments: msgArgs,
        },
      },
    ];
    delete choice.message.function_call;
    state.toolCallSeen = true;
  }

    if (choice.message && Array.isArray(choice.message.tool_calls)) {
      choice.message.tool_calls = choice.message.tool_calls.map((item, idx) => {
        const id = item.id || `call_${idx}`;
        const name = (item.function && item.function.name) || '';
        if (name && state.toolCallNamesSeen) state.toolCallNamesSeen.add(name);
      const msgRawArgs = item.function && item.function.arguments;
      const args =
        msgRawArgs == null
          ? ''
          : typeof msgRawArgs === 'string'
            ? msgRawArgs
            : JSON.stringify(msgRawArgs);
      return {
        ...item,
        id,
        function: {
          name,
          arguments: args,
        },
      };
    });
    state.toolCallSeen = true;
  }

  if (choice.finish_reason && (choice.finish_reason === 'tool_calls' || choice.finish_reason === 'function_call')) {
    if (!state.toolCallSeen) {
      choice.finish_reason = 'stop';
    }
  }
}

function normalizeNonStream(payload) {
  if (!payload || !payload.choices || !payload.choices.length) return payload;
  const state = {
    nextToolCallId: 1,
    toolCallSeen: false,
    toolCallIds: new Map(),
    toolCallNames: new Map(),
  };
  for (const choice of payload.choices) {
    normalizeToolCalls(choice, state);
  }
  return payload;
}

function transformSseLine(line, state) {
  if (!line.startsWith('data:')) return line;
  const trimmed = line.slice(5).trim();
  if (!trimmed || trimmed === '[DONE]') return line;
  let payload;
  try {
    payload = JSON.parse(trimmed);
  } catch (err) {
    log('warn', 'Failed to parse SSE JSON chunk', { error: err.message });
    return line;
  }

  if (payload && payload.choices && payload.choices.length) {
    for (const choice of payload.choices) {
      normalizeToolCalls(choice, state);
      if (choice.message && Array.isArray(choice.message.tool_calls)) {
        choice.delta = choice.delta || {};
        if (!Array.isArray(choice.delta.tool_calls) || choice.delta.tool_calls.length === 0) {
          choice.delta.tool_calls = choice.message.tool_calls;
        }
        delete choice.message.tool_calls;
      }
    }
  }

  const next = JSON.stringify(payload);
  return `data: ${next}\n`;
}

const server = http.createServer(async (req, res) => {
  const requestId = crypto.randomUUID();
  const start = Date.now();
  try {
    let body = await readBody(req);
    const upstreamUrl = buildUpstreamUrl(req.url || '/');

    let bodyMeta;
    if (body.length) {
      const contentType = String(req.headers['content-type'] || '');
      if (contentType.includes('application/json')) {
        try {
          const parsed = JSON.parse(body.toString('utf8'));
          if (shouldForceToolChoice(parsed)) {
            parsed.tool_choice = 'required';
            log('info', 'forcing_tool_choice', {
              id: requestId,
              model: parsed.model,
            });
          }
          const tools = Array.isArray(parsed.tools) ? parsed.tools : [];
          bodyMeta = {
            model: parsed.model,
            hasTools: tools.length > 0,
            toolCount: tools.length,
            toolChoice: parsed.tool_choice,
          };
          body = Buffer.from(JSON.stringify(parsed));
        } catch (err) {
          bodyMeta = { parseError: err.message };
        }
      } else {
        bodyMeta = { contentType };
      }
    }

    const headers = buildUpstreamHeaders(req.headers, body.length);

    log('info', 'proxy_request', {
      id: requestId,
      method: req.method,
      url: req.url,
      upstream: upstreamUrl,
      ...(bodyMeta || {}),
    });

    const upstreamRes = await fetch(upstreamUrl, {
      method: req.method,
      headers,
      body: body.length ? body : undefined,
    });

    const contentType = upstreamRes.headers.get('content-type') || '';
    const eventStream = isEventStream(contentType);

    const responseHeaders = {};
    upstreamRes.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'content-length') return;
      responseHeaders[key] = value;
    });

    res.writeHead(upstreamRes.status, responseHeaders);

    if (!eventStream) {
      const text = await upstreamRes.text();
      if (contentType.includes('application/json')) {
        try {
          const payload = JSON.parse(text);
          const normalized = normalizeNonStream(payload);
          const hasToolCalls =
            Array.isArray(normalized?.choices) &&
            normalized.choices.some((choice) => {
              const msg = choice.message || {};
              const delta = choice.delta || {};
              return (
                (Array.isArray(msg.tool_calls) && msg.tool_calls.length > 0) ||
                (Array.isArray(delta.tool_calls) && delta.tool_calls.length > 0) ||
                choice.finish_reason === 'tool_calls'
              );
            });
          const output = JSON.stringify(normalized);
          res.end(output);
          log('info', 'proxy_response', {
            id: requestId,
            ms: Date.now() - start,
            streamed: false,
            toolCalls: hasToolCalls,
          });
          return;
        } catch (err) {
          log('warn', 'Failed to normalize JSON response', { id: requestId, error: err.message });
          res.end(text);
        }
      } else {
        res.end(text);
      }
      log('info', 'proxy_response', { id: requestId, ms: Date.now() - start, streamed: false, toolCalls: false });
      return;
    }

    const reader = upstreamRes.body?.getReader();
    if (!reader) {
      res.end();
      return;
    }

    const state = {
      nextToolCallId: 1,
      toolCallSeen: false,
      toolCallIds: new Map(),
      toolCallNames: new Map(),
      toolCallNamesSeen: new Set(),
    };

    let buffer = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += Buffer.from(value).toString('utf8');
      let idx;
      while ((idx = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, idx + 1);
        buffer = buffer.slice(idx + 1);
        const outputLine = transformSseLine(line, state);
        res.write(outputLine);
      }
    }

    if (buffer.length) {
      const outputLine = transformSseLine(buffer.endsWith('\n') ? buffer : `${buffer}\n`, state);
      res.write(outputLine);
    }
    res.end();

    log('info', 'proxy_response', {
      id: requestId,
      ms: Date.now() - start,
      streamed: true,
      toolCalls: state.toolCallSeen,
      toolCallNames: Array.from(state.toolCallNamesSeen || []),
    });
  } catch (err) {
    log('error', 'proxy_error', { id: requestId, error: err.message });
    res.statusCode = 502;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ error: 'proxy_error', message: err.message }));
  }
});

server.listen(PORT, () => {
  log('info', 'llm proxy started', { port: PORT, upstream: UPSTREAM_BASE_URL });
});
