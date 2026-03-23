'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Code2, Play, Loader2, AlertCircle } from 'lucide-react';

export default function CodexCliPage() {
  const { user, isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [cwd, setCwd] = useState('');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  const handleRun = async () => {
    if (!prompt.trim()) {
      setError('请输入任务描述');
      return;
    }
    setError('');
    setOutput('');
    setRunning(true);
    try {
      const res = await fetch('/api/codex/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim(), cwd: cwd.trim() || undefined }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.error || data.detail || `请求失败 (${res.status})`);
        if (data.hint) setOutput((o) => o + '\n' + data.hint);
        return;
      }
      setOutput(data.stdout ?? data.output ?? JSON.stringify(data));
      if (data.stderr) setOutput((o) => o + '\n[stderr]\n' + data.stderr);
    } catch (e) {
      setError(e instanceof Error ? e.message : '网络或请求异常');
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 bg-purple-100 rounded-xl">
            <Code2 className="w-8 h-8 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Codex CLI</h1>
            <p className="text-gray-600 text-sm">
              调用服务器已安装的 Codex CLI，配合内网大模型执行编码与自动化任务
            </p>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <label className="block text-sm font-medium text-gray-700 mb-2">任务描述（Codex 将根据描述执行）</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="例如：在当前目录列出所有 .py 文件"
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-y min-h-[120px]"
              disabled={running}
            />
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">工作目录（可选）</label>
              <input
                type="text"
                value={cwd}
                onChange={(e) => setCwd(e.target.value)}
                placeholder="/path/to/workspace 或留空使用默认"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                disabled={running}
              />
            </div>
            <button
              onClick={handleRun}
              disabled={running}
              className="mt-4 inline-flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white rounded-xl hover:bg-purple-700 disabled:opacity-60 disabled:cursor-not-allowed font-medium"
            >
              {running ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  执行中…
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  执行
                </>
              )}
            </button>
          </div>

          {(error || output) && (
            <div className="p-6 bg-gray-50 border-t border-gray-200">
              {error && (
                <div className="flex items-start gap-2 mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-800">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt0.5" />
                  <span>{error}</span>
                </div>
              )}
              {output && (
                <>
                  <label className="block text-sm font-medium text-gray-700 mb-2">输出</label>
                  <pre className="p-4 bg-gray-900 text-gray-100 rounded-xl text-sm overflow-auto max-h-[400px] whitespace-pre-wrap font-mono">
                    {output}
                  </pre>
                </>
              )}
            </div>
          )}
        </div>

        <p className="mt-6 text-sm text-gray-500">
          需在服务器上完成 Codex CLI 离线安装并部署 Codex Runner，并配置 <code className="bg-gray-200 px-1 rounded">CODEX_RUNNER_URL</code>。
          详见 <code className="bg-gray-200 px-1 rounded">docs/deployment/Codex-CLI-内网离线安装与门户集成.md</code>。
        </p>
      </div>
    </div>
  );
}
