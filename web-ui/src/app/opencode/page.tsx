'use client';

import { AuthGuard } from '@/components/AuthGuard';
import { useAuth } from '@/contexts/AuthContext';
import { Code2, ExternalLink, Terminal } from 'lucide-react';
import { useMemo, useState, useEffect } from 'react';

export default function OpenCodePage() {
  const { user } = useAuth();
  const [opencodeUrl, setOpencodeUrl] = useState(
    typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_OPENCODE_URL || '') : process.env.NEXT_PUBLIC_OPENCODE_URL || ''
  );

  useEffect(() => {
    fetch('/api/opencode-url')
      .then((r) => r.json())
      .then((data) => {
        if (data?.url) setOpencodeUrl(data.url);
      })
      .catch(() => {});
  }, []);

  const opencodeHref = useMemo(() => {
    if (!opencodeUrl) return '';
    return opencodeUrl.replace(/\?.*$/, '');
  }, [opencodeUrl]);

  const handleOpen = () => {
    if (!opencodeHref) return;
    window.open(opencodeHref, '_blank', 'noopener,noreferrer');
  };

  return (
    <AuthGuard redirectTo="/login?redirect=/opencode">
      <div className="min-h-[80vh] flex flex-col items-center justify-center p-6">
        <div className="max-w-lg w-full bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-indigo-100">
              <Code2 className="h-8 w-8 text-indigo-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">OpenCode 开发环境</h1>
              <p className="text-sm text-gray-500">独立登录，固定在项目根目录运行</p>
            </div>
          </div>
          <p className="text-gray-600 mb-6">
            OpenCode 采用独立认证，不与平台 SSO 绑定。当前会话固定在 <strong>/workspace</strong> 项目根目录运行，不提供子目录切换。
          </p>
          {opencodeUrl ? (
            <>
              <div className="mb-4 rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-700">
                当前已固定为项目根目录（/workspace），不可切换到其他目录。
              </div>
              <button
                type="button"
                onClick={handleOpen}
                className="flex items-center justify-center gap-2 w-full py-3.5 px-4 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors"
              >
                <Terminal className="h-5 w-5" />
                跳转到 OpenCode（新窗口）
                <ExternalLink className="h-4 w-4" />
              </button>
            </>
          ) : (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm">
              <p className="font-medium mb-1">未配置 OpenCode 独立地址</p>
              <p>
                请在环境变量中设置 <code className="bg-amber-100 px-1 rounded">NEXT_PUBLIC_OPENCODE_URL</code>，例如
                <code className="bg-amber-100 px-1 rounded">http://10.24.20.56:4096</code>，然后重启 web-ui 容器。
              </p>
            </div>
          )}
          {user && (
            <p className="mt-6 text-center text-xs text-gray-400">
              当前用户：{user.display_name || user.username}
            </p>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
