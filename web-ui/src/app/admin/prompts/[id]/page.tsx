'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';

interface PromptTemplate {
  id: number;
  name: string;
  category: string;
  description?: string;
  system_prompt?: string;
  examples?: Array<{ user: string; assistant: string; metadata?: any }>;
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
  stop_sequences?: string[];
  output_format?: any;
  dynamic_placeholders?: string[];
  is_active: boolean;
  version: number;
  metadata?: any;
}

export default function EditPromptPage() {
  const router = useRouter();
  const params = useParams();
  const promptId = params?.id as string;

  const [prompt, setPrompt] = useState<PromptTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<Partial<PromptTemplate>>({});

  useEffect(() => {
    if (promptId) {
      fetchPrompt();
    }
  }, [promptId]);

  const fetchPrompt = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/prompts/${promptId}`);
      if (response.ok) {
        const data = await response.json();
        setPrompt(data);
        setFormData(data);
      }
    } catch (error) {
      console.error('Failed to fetch prompt:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const response = await fetch(`/api/v1/prompts/${promptId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (response.ok) {
        router.push('/admin/prompts');
      }
    } catch (error) {
      console.error('Failed to save prompt:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  if (!prompt) {
    return <div className="text-center py-8">提示词模板不存在</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">编辑提示词</h1>
          <p className="text-gray-600 mt-1">
            {prompt.name} (v{prompt.version})
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/admin/prompts"
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            取消
          </Link>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border border-gray-200 p-6 space-y-6">
        {/* 基本信息 */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">基本信息</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
            <input
              type="text"
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
            <input
              type="text"
              value={formData.category || ''}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* 系统提示词 */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">系统提示词</h2>
          <textarea
            value={formData.system_prompt || ''}
            onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
            rows={15}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            placeholder="输入系统提示词..."
          />
        </div>

        {/* LLM参数 */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">LLM参数</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={formData.temperature || 0.3}
                onChange={(e) =>
                  setFormData({ ...formData, temperature: parseFloat(e.target.value) })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
              <input
                type="number"
                min="100"
                max="8000"
                value={formData.max_tokens || 2000}
                onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* 状态 */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">状态</h2>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.is_active ?? true}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4"
            />
            <span>激活</span>
          </label>
        </div>
      </div>
    </div>
  );
}
