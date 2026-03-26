import { NextRequest, NextResponse } from 'next/server';

const CODEX_RUNNER_URL = process.env.CODEX_RUNNER_URL || process.env.NEXT_PUBLIC_CODEX_RUNNER_URL;

export async function POST(request: NextRequest) {
  if (!CODEX_RUNNER_URL) {
    return NextResponse.json(
      {
        error: 'Codex Runner 未配置',
        detail: '请在内网部署 Codex Runner 并设置环境变量 CODEX_RUNNER_URL',
        hint:
          '1) 在安装 codex 的服务器上运行 project_management/demos/codex-runner；\n' +
          '2) 在 Web UI 或编排中配置 CODEX_RUNNER_URL 指向该服务（如 http://host:8321）。',
      },
      { status: 503 }
    );
  }

  try {
    const body = await request.json();
    const prompt = typeof body?.prompt === 'string' ? body.prompt.trim() : '';
    const cwd = typeof body?.cwd === 'string' ? body.cwd.trim() : undefined;
    if (!prompt) {
      return NextResponse.json({ error: '缺少 prompt' }, { status: 400 });
    }

    const runnerUrl = CODEX_RUNNER_URL.replace(/\/$/, '');
    const res = await fetch(`${runnerUrl}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, cwd }),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json(
        { error: data.error || data.detail || 'Codex Runner 执行失败', ...data },
        { status: res.status }
      );
    }
    return NextResponse.json(data);
  } catch (e) {
    console.error('Codex run request failed:', e);
    return NextResponse.json(
      { error: '请求 Codex Runner 失败', detail: e instanceof Error ? e.message : String(e) },
      { status: 500 }
    );
  }
}
