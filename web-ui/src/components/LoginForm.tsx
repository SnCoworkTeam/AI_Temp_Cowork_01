'use client';

import { useState, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { authClient } from '@/lib/api/auth';
import { setAccessToken, setRefreshToken, saveUser } from '@/lib/auth';

interface LoginFormProps {
  /** 登录成功后的跳转路径，默认 /portal；例如 /opencode 表示认证后跳转到 OpenCode 入口 */
  redirectTo?: string;
}

export function LoginForm({ redirectTo = '/portal' }: LoginFormProps) {
  const { login, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const isSubmittingRef = useRef(false); // 使用 ref 跟踪提交状态，避免重复提交
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loginType, setLoginType] = useState<'password' | 'sso'>('password');

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();

    console.log('=== Login Form Submit Handler Called ===');
    console.log('Username:', username);
    console.log('Password length:', password?.length || 0);

    // 验证输入
    if (!username || !password) {
      console.log('Validation failed: missing username or password');
      setError('请输入用户名和密码');
      // 确保状态已重置
      setLoading(false);
      isSubmittingRef.current = false;
      return;
    }

    // 如果已经在提交中，防止重复提交（使用 ref 而不是 state，避免 React 严格模式的问题）
    if (isSubmittingRef.current) {
      console.log('登录请求正在进行中，忽略重复提交');
      return;
    }

    isSubmittingRef.current = true;
    setError('');
    setSuccess('');
    setLoading(true);

    console.log('Login form submitted:', { username, password: '***' });

    // 直接调用API，不依赖AuthContext的login函数
    console.log('Calling authClient.login...');

    try {
      console.log('请求开始时间:', new Date().toISOString());

      // 使用 Promise.race 实现超时，但不在 fetch 中使用 signal
      const loginPromise = authClient.login(username, password);
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => {
          reject(new Error('请求超时（10秒），请检查服务器是否运行'));
        }, 10000); // 10秒超时
      });

      // 使用 race 来处理超时
      const data = await Promise.race([loginPromise, timeoutPromise]);

      console.log('响应接收时间:', new Date().toISOString());
      console.log('响应数据:', data);

      // 登录成功
      console.log('登录成功，保存token');
      if (data.access_token) {
        setAccessToken(data.access_token);
        setRefreshToken(data.refresh_token);
        if (data.user) {
          saveUser(data.user);
          updateUser(data.user);
        }
      } else {
        console.warn('响应中没有access_token');
        setError('登录响应中缺少访问令牌');
        setLoading(false);
        isSubmittingRef.current = false;
        return;
      }

      setSuccess('登录成功！正在跳转...');
      // 立即重置状态，允许用户再次点击（如果跳转失败）
      setLoading(false);
      isSubmittingRef.current = false;

      const target = redirectTo.startsWith('/') ? redirectTo : '/portal';
      setTimeout(() => {
        window.location.href = target;
      }, 500);
    } catch (err: any) {
      console.error('Login error:', err);
      console.error('Error name:', err?.name);
      console.error('Error message:', err?.message);
      console.error('Error stack:', err?.stack);

      let errorMessage = '登录失败，请检查网络连接';

      // 处理不同类型的错误
      if (
        (err?.name === 'TypeError' && err?.message?.includes('fetch')) ||
        err?.message?.includes('网络错误')
      ) {
        errorMessage =
          '无法连接到服务器，请检查：\n1. API Gateway 是否运行 (http://localhost:8080/health)\n2. Auth Service 是否运行 (http://localhost:8003/health)';
      } else if (err?.name === 'AbortError') {
        errorMessage = '请求被取消，请重试';
      } else if (err?.message) {
        // 如果错误消息包含"超时"，说明可能是网络问题
        if (err.message.includes('超时') || err.message.includes('timeout')) {
          errorMessage =
            '请求超时，可能的原因：\n1. API Gateway 未运行\n2. Auth Service 未运行\n3. 网络连接问题\n\n请检查服务器状态或尝试直接访问 Auth Service';
        } else {
          errorMessage = err.message;
        }
      }

      setError(errorMessage);
      setLoading(false);
      isSubmittingRef.current = false;
    }
  };

  const handleSSOLogin = async () => {
    // 如果已经在提交中，防止重复提交
    if (isSubmittingRef.current) {
      console.log('SSO登录请求正在进行中，忽略重复提交');
      return;
    }

    isSubmittingRef.current = true;
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await login();
      // 注意：如果登录成功，login() 会处理跳转，但为了安全，我们也应该重置状态
      // 但由于 SSO 登录可能会重定向，这里不立即重置，让跳转处理
    } catch (error: any) {
      console.error('SSO登录失败:', error);
      setError(error?.message || 'SSO登录失败，请重试');
      setLoading(false);
      isSubmittingRef.current = false;
    }
  };

  return (
    <div className="w-full bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl p-8 border border-white/20">
      {/* Logo和标题 */}
      <div className="text-center mb-8">
        <div className="flex justify-center mb-4">
          <img src="/logo.jpg" alt="中化国际" className="h-16 w-auto object-contain" />
        </div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">中化国际AIOS平台</h1>
        <p className="text-gray-500 text-sm">请选择登录方式</p>
      </div>

      {/* 登录方式切换 */}
      <div className="flex gap-2 mb-6 bg-gray-50 rounded-lg p-1">
        <button
          onClick={() => setLoginType('password')}
          className={`flex-1 py-2.5 text-sm font-medium transition-all duration-200 rounded-md ${
            loginType === 'password'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
          }`}
        >
          密码登录
        </button>
        <button
          onClick={() => setLoginType('sso')}
          className={`flex-1 py-2.5 text-sm font-medium transition-all duration-200 rounded-md ${
            loginType === 'sso'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
          }`}
        >
          SSO登录
        </button>
      </div>

      <div className="space-y-6">
        {loginType === 'password' ? (
          <form onSubmit={handlePasswordLogin} className="space-y-5">
            {error && (
              <div className="p-4 bg-red-50 border-l-4 border-red-400 rounded-lg text-red-700 text-sm animate-fade-in">
                <div className="flex items-start">
                  <svg
                    className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <div className="flex-1">{error}</div>
                </div>
              </div>
            )}
            {success && (
              <div className="p-4 bg-green-50 border-l-4 border-green-400 rounded-lg text-green-700 text-sm animate-fade-in">
                <div className="flex items-start">
                  <svg
                    className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <div className="flex-1">{success}</div>
                </div>
              </div>
            )}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                用户名或邮箱
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg
                    className="h-5 w-5 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={loading}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 transition-all duration-200"
                  placeholder="请输入用户名或邮箱"
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                密码
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg
                    className="h-5 w-5 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 transition-all duration-200"
                  placeholder="请输入密码"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading || !username.trim() || !password.trim()}
              className="w-full flex items-center justify-center gap-3 px-6 py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  <span>登录中...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                    />
                  </svg>
                  <span>登录</span>
                </>
              )}
            </button>
          </form>
        ) : (
          <div className="space-y-4">
            <button
              onClick={handleSSOLogin}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 px-6 py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  <span>登录中...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                    />
                  </svg>
                  <span>使用SSO登录</span>
                </>
              )}
            </button>
            <div className="text-center text-sm text-gray-500">
              <p>使用企业单点登录系统进行身份验证</p>
            </div>
          </div>
        )}

        <div className="text-center text-xs text-gray-400 mt-6">
          <p>登录即表示您同意我们的服务条款和隐私政策</p>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="text-center text-sm text-gray-500">
          <p className="mb-1">需要帮助？</p>
          <a
            href="mailto:support@example.com"
            className="text-blue-600 hover:text-blue-700 font-medium transition-colors duration-200 inline-flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            联系支持团队
          </a>
        </div>
      </div>
    </div>
  );
}
