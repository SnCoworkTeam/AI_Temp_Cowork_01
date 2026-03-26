'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PlayIcon, ArrowLeftIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/UI/Button';

interface Workflow {
  id: string;
  name: string;
  description: string;
  version: string;
  status: string;
}

export default function WorkflowRunPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [inputData, setInputData] = useState('{}');
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

  useEffect(() => {
    if (workflowId) {
      fetchWorkflow();
    }
  }, [workflowId]);

  const fetchWorkflow = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/workflows/${workflowId}`);
      const data = await response.json();

      if (response.ok) {
        // 后端可能返回 { workflow: {...} } 或直接是工作流对象
        const workflowData = data.workflow || data;
        if (workflowData) {
          setWorkflow({
            id: workflowData.workflow_id || workflowData.id || workflowId,
            name: workflowData.name || workflowData.workflow?.name || '未命名工作流',
            description: workflowData.description || workflowData.workflow?.description || '',
            version: workflowData.version || '1.0.0',
            status: workflowData.status || workflowData.workflow?.status || 'draft',
          });
          // 检查工作流状态
          const status = workflowData.status || workflowData.workflow?.status;
          if (status && status !== 'active') {
            setExecutionError('此工作流尚未发布，无法执行');
          }
        } else {
          setExecutionError('工作流数据格式错误');
        }
      } else {
        setExecutionError(data.error || '工作流不存在或无法访问');
      }
    } catch (error) {
      console.error('Failed to fetch workflow:', error);
      setExecutionError('加载工作流失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!workflow) return;

    try {
      setExecuting(true);
      setExecutionError(null);
      setExecutionResult(null);

      // 解析输入数据
      let parsedInputData = {};
      try {
        parsedInputData = JSON.parse(inputData);
      } catch (e) {
        setExecutionError('输入数据格式错误，请输入有效的 JSON');
        setExecuting(false);
        return;
      }

      const response = await fetch(`/api/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_data: parsedInputData,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setExecutionResult(data);
      } else {
        setExecutionError(data.error || '工作流执行失败');
      }
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      setExecutionError('执行失败: ' + (error instanceof Error ? error.message : '未知错误'));
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!workflow || (executionError && !executionResult)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-center mb-4">
            <XCircleIcon className="h-12 w-12 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">无法访问工作流</h2>
          <p className="text-sm text-gray-600 text-center mb-6">
            {executionError || '工作流不存在或已被删除'}
          </p>
          <Button variant="primary" fullWidth onClick={() => router.push('/workflows')}>
            返回工作流列表
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/workflows')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeftIcon className="h-5 w-5 text-gray-600" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{workflow.name}</h1>
                {workflow.description && (
                  <p className="text-sm text-gray-500 mt-1">{workflow.description}</p>
                )}
              </div>
            </div>
            <div className="text-xs text-gray-500">版本 {workflow.version}</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">执行工作流</h2>

          {/* Input Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">输入参数 (JSON格式)</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setInputData('{\n  "input": "请输入您的问题或内容"\n}')}
                  className="text-xs text-blue-600 hover:text-blue-800 underline px-2 py-1 hover:bg-blue-50 rounded"
                  disabled={executing}
                >
                  简单示例
                </button>
                <button
                  type="button"
                  onClick={() => setInputData('{\n  "query": "搜索关键词",\n  "limit": 5\n}')}
                  className="text-xs text-blue-600 hover:text-blue-800 underline px-2 py-1 hover:bg-blue-50 rounded"
                  disabled={executing}
                >
                  搜索示例
                </button>
                <button
                  type="button"
                  onClick={() => setInputData('{}')}
                  className="text-xs text-gray-600 hover:text-gray-800 underline px-2 py-1 hover:bg-gray-50 rounded"
                  disabled={executing}
                >
                  清空
                </button>
              </div>
            </div>
            <textarea
              value={inputData}
              onChange={(e) => setInputData(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              rows={12}
              placeholder='{"input": "您的问题或内容"}'
              disabled={executing}
            />
            <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs font-medium text-blue-800 mb-2">💡 输入参数说明：</p>
              <ul className="text-xs text-blue-700 space-y-1 ml-4 list-disc">
                <li>
                  输入参数会被放入工作流的 <code className="bg-blue-100 px-1 rounded">input</code>{' '}
                  字段
                </li>
                <li>
                  简单文本：
                  <code className="bg-blue-100 px-1 rounded">
                    {'{'}&quot;input&quot;: &quot;问题&quot;{'}'}
                  </code>
                </li>
                <li>
                  多字段：
                  <code className="bg-blue-100 px-1 rounded">
                    {'{'}&quot;query&quot;: &quot;关键词&quot;, &quot;limit&quot;: 10{'}'}
                  </code>
                </li>
                <li>
                  如果工作流不需要参数，可以输入：
                  <code className="bg-blue-100 px-1 rounded">{'{}'}</code>
                </li>
              </ul>
            </div>
          </div>

          {/* Execute Button */}
          <div className="mb-6">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={handleExecute}
              loading={executing}
              disabled={executing}
              icon={<PlayIcon className="h-5 w-5" />}
            >
              {executing ? '执行中...' : '执行工作流'}
            </Button>
          </div>

          {/* Error Display */}
          {executionError && !executionResult && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <XCircleIcon className="h-5 w-5 text-red-500 mr-3 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-red-800 mb-1">执行失败</h3>
                  <p className="text-sm text-red-700">{executionError}</p>
                </div>
              </div>
            </div>
          )}

          {/* Success Result */}
          {executionResult && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-start mb-4">
                <CheckCircleIcon className="h-6 w-6 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-green-800 mb-2">执行成功</h3>
                  {executionResult.execution_time !== undefined && (
                    <p className="text-sm text-green-700 mb-4">
                      执行时间: {executionResult.execution_time.toFixed(2)} 秒
                    </p>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      执行结果:
                    </label>
                    <pre className="bg-white border border-gray-200 rounded-lg p-4 text-xs overflow-auto max-h-96">
                      {JSON.stringify(executionResult.result || executionResult, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg
              className="h-5 w-5 text-blue-500 mr-3 mt-0.5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-blue-800 mb-1">提示</h4>
              <p className="text-sm text-blue-700">
                此页面是工作流的公开执行界面。您可以通过分享此页面的链接，让其他人也能执行此工作流。
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
