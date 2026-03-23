'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowUpTrayIcon,
  DocumentTextIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  status: string;
}

export default function UploadDocumentPage() {
  const router = useRouter();
  const params = useParams();
  const kbId = params?.id as string;

  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadResults, setUploadResults] = useState<
    Array<{
      filename: string;
      status: 'success' | 'error';
      message: string;
    }>
  >([]);

  useEffect(() => {
    if (kbId) {
      fetchKnowledgeBase();
    }
  }, [kbId]);

  const fetchKnowledgeBase = async () => {
    try {
      const response = await fetch(`/api/knowledge-bases/${kbId}`);
      if (response.ok) {
        const data = await response.json();
        setKnowledgeBase(data);
      } else {
        alert('知识库不存在');
        router.push('/knowledge-bases');
      }
    } catch (error) {
      console.error('Failed to fetch knowledge base:', error);
      alert('加载知识库信息失败');
      router.push('/knowledge-bases');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setSelectedFiles((prev) => [...prev, ...files]);
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      alert('请选择要上传的文件');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadResults([]);

    const results: Array<{ filename: string; status: 'success' | 'error'; message: string }> = [];

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('knowledge_base_id', kbId);

      try {
        // 确保knowledge_base_id在FormData中
        if (!formData.has('knowledge_base_id')) {
          formData.append('knowledge_base_id', kbId);
        }

        // 通过API网关上传文档（已修复流式传输支持）
        const apiGatewayUrl =
          process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
        const response = await fetch(`${apiGatewayUrl}/api/knowledge/documents/upload`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          results.push({
            filename: file.name,
            status: 'success',
            message: '上传成功',
          });
        } else {
          const error = await response.json().catch(() => ({ detail: '上传失败' }));
          results.push({
            filename: file.name,
            status: 'error',
            message: error.detail || '上传失败',
          });
        }
      } catch (error) {
        results.push({
          filename: file.name,
          status: 'error',
          message: '上传失败: ' + (error instanceof Error ? error.message : '未知错误'),
        });
      }

      setUploadProgress(((i + 1) / selectedFiles.length) * 100);
      setUploadResults([...results]);
    }

    setUploading(false);

    // 显示结果
    const successCount = results.filter((r) => r.status === 'success').length;
    const failCount = results.filter((r) => r.status === 'error').length;

    if (failCount === 0) {
      alert(`所有文件上传成功 (${successCount}个)`);
      router.push(`/knowledge/${kbId}`);
    } else {
      alert(`上传完成: ${successCount}个成功, ${failCount}个失败`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!knowledgeBase) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">上传文档</h1>
              <p className="mt-1 text-sm text-gray-500">知识库: {knowledgeBase.name}</p>
            </div>
            <button
              onClick={() => router.push(`/knowledge/${kbId}`)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <XMarkIcon className="h-5 w-5 mr-2" />
              取消
            </button>
          </div>
        </div>
      </div>

      {/* Upload Area */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          {/* File Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">选择文件</label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-blue-400 transition-colors">
              <div className="space-y-1 text-center">
                <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label
                    htmlFor="file-upload"
                    className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                  >
                    <span>选择文件</span>
                    <input
                      id="file-upload"
                      name="file-upload"
                      type="file"
                      multiple
                      className="sr-only"
                      onChange={handleFileSelect}
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.md,.markdown"
                    />
                  </label>
                  <p className="pl-1">或拖放文件到此处</p>
                </div>
                <p className="text-xs text-gray-500">
                  PDF, Word, Excel, Text, Markdown (最大 50MB)
                </p>
              </div>
            </div>
          </div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                已选择文件 ({selectedFiles.length})
              </h3>
              <div className="space-y-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center flex-1 min-w-0">
                      <DocumentTextIcon className="h-5 w-5 text-gray-400 mr-3 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="ml-4 text-gray-400 hover:text-red-500"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Progress */}
          {uploading && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">上传进度</span>
                <span className="text-sm text-gray-500">{Math.round(uploadProgress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Upload Results */}
          {uploadResults.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">上传结果</h3>
              <div className="space-y-2">
                {uploadResults.map((result, index) => (
                  <div
                    key={index}
                    className={`flex items-center p-3 rounded-lg ${
                      result.status === 'success' ? 'bg-green-50' : 'bg-red-50'
                    }`}
                  >
                    {result.status === 'success' ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3" />
                    ) : (
                      <ExclamationCircleIcon className="h-5 w-5 text-red-500 mr-3" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{result.filename}</p>
                      <p
                        className={`text-xs ${
                          result.status === 'success' ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {result.message}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={() => router.push(`/knowledge/${kbId}`)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              disabled={uploading}
            >
              取消
            </button>
            <button
              onClick={handleUpload}
              disabled={uploading || selectedFiles.length === 0}
              className="px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? '上传中...' : '开始上传'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
