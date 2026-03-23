'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useRef } from 'react';
import { Code2, Send, Loader2, User, Bot, AlertCircle, FolderOpen } from 'lucide-react';

const CODEX_BASE_DIR = '/opt/enterprise-ai-platform';
const CODEX_SUBFOLDERS = [
  { value: '', label: '根目录' },
  { value: 'api-gateway', label: 'api-gateway' },
  { value: 'auth-service', label: 'auth-service' },
  { value: 'chat-service', label: 'chat-service' },
  { value: 'knowledge-base', label: 'knowledge-base' },
  { value: 'workflow-engine', label: 'workflow-engine' },
  { value: 'project_management', label: 'project_management' },
  { value: 'web-ui', label: 'web-ui' },
  { value: 'docs', label: 'docs' },
  { value: 'database', label: 'database' },
  { value: 'opencode-src', label: 'opencode-src' },
  { value: 'opencode-server-export', label: 'opencode-server-export' },
];

type MessageRole = 'user' | 'assistant';

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  cwd?: string;
  isError?: boolean;
  isPending?: boolean;
}

function getCwdFromSelection(subfolder: string): string {
  return subfolder ? `${CODEX_BASE_DIR}/${subfolder}` : CODEX_BASE_DIR;
}

export default function CodexCliPage() {
  const { user, isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [subfolder, setSubfolder] = useState('');
  const [running, setRunning] = useState(false);
  const listEndRef = useRef<HTMLDivElement>(null);

  const cwd = getCwdFromSelection(subfolder);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const text = prompt.trim();
    if (!text || running) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      cwd: cwd.trim() || undefined,
    };
    setMessages((prev) => [...prev, userMsg]);
    setPrompt('');
    setRunning(true);

    const pendingId = `pending-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: pendingId, role: 'assistant', content: '', isPending: true },
    ]);

    try {
      const res = await fetch('/api/codex/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: text, cwd: cwd.trim() || undefined }),
      });
      const data = await res.json().catch(() => ({}));

      const errText = data.error || data.detail || `请求失败 (${res.status})`;
      const hintText = !res.ok && data.hint ? '\n\n' + data.hint : '';
      const assistantContent = res.ok
        ? [data.stdout ?? data.output ?? '']
            .concat(data.stderr ? `[stderr]\n${data.stderr}` : '')
            .filter(Boolean)
            .join('\n\n') || '(无输出)'
        : errText + hintText;

      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingId
            ? {
                ...m,
                id: `assistant-${Date.now()}`,
                content: assistantContent,
                cwd: userMsg.cwd,
                isError: !res.ok,
                isPending: false,
              }
            : m
        )
      );
    } catch (e) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingId
            ? {
                ...m,
                id: `assistant-${Date.now()}`,
                content: e instanceof Error ? e.message : '网络或请求异常',
                cwd: userMsg.cwd,
                isError: true,
                isPending: false,
              }
            : m
        )
      );
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-10 h-10 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 标题栏 */}
      <div className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Code2 className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">Codex CLI</h1>
            <p className="text-xs text-gray-500">
              对话式调用服务器 Codex CLI，配合内网大模型执行任务
            </p>
          </div>
        </div>
      </div>

      {/* 对话区域 */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="p-4 bg-purple-50 rounded-2xl mb-4">
                <Bot className="w-12 h-12 text-purple-500" />
              </div>
              <p className="text-gray-600 mb-1">在下方输入任务描述，Codex 将执行并在此显示结果</p>
              <p className="text-sm text-gray-400">例如：列出当前目录下的 .py 文件</p>
            </div>
          )}

          <div className="space-y-6">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div
                  className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${
                    msg.role === 'user' ? 'bg-purple-100 text-purple-600' : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <User className="w-5 h-5" />
                  ) : msg.isPending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Bot className="w-5 h-5" />
                  )}
                </div>
                <div
                  className={`flex-1 min-w-0 max-w-[85%] ${
                    msg.role === 'user' ? 'text-right' : ''
                  }`}
                >
                  {msg.role === 'user' && msg.cwd && (
                    <p className="text-xs text-gray-500 mb-1 flex items-center justify-end gap-1">
                      <FolderOpen className="w-3.5 h-3.5" />
                      {msg.cwd}
                    </p>
                  )}
                  <div
                    className={`inline-block px-4 py-3 rounded-2xl text-left ${
                      msg.role === 'user'
                        ? 'bg-purple-600 text-white rounded-tr-sm'
                        : msg.isError
                          ? 'bg-red-50 text-red-800 border border-red-200 rounded-tl-sm'
                          : 'bg-white border border-gray-200 shadow-sm rounded-tl-sm'
                    }`}
                  >
                    {msg.role === 'assistant' && msg.cwd && (
                      <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                        <FolderOpen className="w-3.5 h-3.5" />
                        {msg.cwd}
                      </p>
                    )}
                    {msg.isPending ? (
                      <span className="text-gray-500 text-sm">执行中…</span>
                    ) : msg.isError ? (
                      <div className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 flex-shrink-0 mt0.5" />
                        <pre className="whitespace-pre-wrap break-words font-sans text-sm">
                          {msg.content}
                        </pre>
                      </div>
                    ) : (
                      <pre className="whitespace-pre-wrap break-words font-mono text-sm overflow-x-auto">
                        {msg.content}
                      </pre>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div ref={listEndRef} />
        </div>
      </div>

      {/* 输入区 */}
      <div className="flex-shrink-0 bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-gray-600 flex items-center gap-1">
              <FolderOpen className="w-4 h-4 text-gray-400" />
              工作目录
            </span>
            <select
              value={subfolder}
              onChange={(e) => setSubfolder(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white"
              disabled={running}
            >
              {CODEX_SUBFOLDERS.map((opt) => (
                <option key={opt.value || 'root'} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <span className="text-xs text-gray-500 truncate max-w-[280px]" title={cwd}>
              {cwd}
            </span>
          </div>
          <div className="flex gap-2">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="输入任务描述，Enter 发送，Shift+Enter 换行…"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none min-h-[52px] max-h-32"
              rows={2}
              disabled={running}
            />
            <button
              onClick={handleSend}
              disabled={running || !prompt.trim()}
              className="flex-shrink-0 self-end p-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="发送"
            >
              {running ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <Send className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
