'use client';

import { useState, useEffect } from 'react';
import { MessageCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function HelloWorldPage() {
  const { user, isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const [inputText, setInputText] = useState('');
  const [displayText, setDisplayText] = useState('');

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const handleSubmit = () => {
    if (inputText.toLowerCase() === 'hello world') {
      setDisplayText('你好全世界');
    } else {
      setDisplayText('请输入 "hello world"');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-blue-100 rounded-full">
            <MessageCircle className="w-6 h-6 text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Hello World</h1>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              输入 hello world
            </label>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="请输入 hello world"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            />
          </div>

          <button
            onClick={handleSubmit}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
          >
            确认
          </button>

          {displayText && (
            <div className={`mt-6 p-4 rounded-lg text-center font-semibold text-lg ${
              displayText === '你好全世界' 
                ? 'bg-green-100 text-green-700' 
                : 'bg-yellow-100 text-yellow-700'
            }`}>
              {displayText}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
