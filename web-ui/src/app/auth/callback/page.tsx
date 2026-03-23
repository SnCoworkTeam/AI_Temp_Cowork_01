'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshToken } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('正在处理登录...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // 检查是否有错误
        const error = searchParams.get('error');
        if (error) {
          setStatus('error');
          setMessage(`登录失败: ${error}`);
          setTimeout(() => {
            router.push('/login');
          }, 3000);
          return;
        }

        // 检查是否有授权码
        const code = searchParams.get('code');
        const state = searchParams.get('state');

        if (!code || !state) {
          setStatus('error');
          setMessage('缺少必要的认证参数');
          setTimeout(() => {
            router.push('/login');
          }, 3000);
          return;
        }

        // 等待后端处理回调（Cookie会自动设置）
        // 前端只需要等待并重定向
        setMessage('登录成功，正在跳转...');

        // 等待一段时间让后端处理完成
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // 尝试刷新令牌以获取用户信息
        const refreshed = await refreshToken();
        if (refreshed) {
          setStatus('success');
          setMessage('登录成功！');
          setTimeout(() => {
            router.push('/portal');
          }, 1500);
        } else {
          // Cookie应该已经设置，直接跳转
          setStatus('success');
          setMessage('登录成功！');
          setTimeout(() => {
            router.push('/portal');
          }, 1500);
        }
      } catch (error) {
        console.error('Callback error:', error);
        setStatus('error');
        setMessage('登录处理失败，请重试');
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mb-4">
          {status === 'loading' && (
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          )}
          {status === 'success' && (
            <div className="rounded-full h-12 w-12 bg-green-100 flex items-center justify-center mx-auto">
              <svg
                className="w-6 h-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          )}
          {status === 'error' && (
            <div className="rounded-full h-12 w-12 bg-red-100 flex items-center justify-center mx-auto">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
          )}
        </div>
        <p className="text-lg text-gray-700">{message}</p>
      </div>
    </div>
  );
}
