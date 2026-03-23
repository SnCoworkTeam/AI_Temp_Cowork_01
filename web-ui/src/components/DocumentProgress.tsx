'use client';

import React, { useState, useEffect } from 'react';
import {
  CheckCircleIcon,
  ArrowPathIcon,
  ClockIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

interface ProcessingProgress {
  document_id: string;
  stage: string;
  progress_percentage: number;
  current_step: string;
  total_steps: number;
  completed_steps: number;
  estimated_time_remaining?: number;
  started_at?: string;
  updated_at?: string;
  details?: Record<string, any>;
  error?: string;
}

interface DocumentProgressProps {
  documentId: string;
  status: string;
  onUpdate?: () => void;
}

// 处理阶段定义
const PROCESSING_STAGES = [
  { key: 'uploading', label: '上传', weight: 5, icon: '📤' },
  { key: 'parsing', label: '解析', weight: 15, icon: '📄' },
  { key: 'preprocessing', label: '预处理', weight: 0, icon: '🧹' },
  { key: 'quality_assessment', label: '质量评估', weight: 0, icon: '⭐' },
  { key: 'metadata_enhancement', label: '元数据增强', weight: 0, icon: '✨' },
  { key: 'chunking', label: '分块', weight: 10, icon: '✂️' },
  { key: 'embedding', label: '向量化', weight: 60, icon: '🔢' },
  { key: 'storing', label: '存储', weight: 10, icon: '💾' },
  { key: 'completed', label: '完成', weight: 0, icon: '✅' },
];

export default function DocumentProgress({ documentId, status, onUpdate }: DocumentProgressProps) {
  const [progress, setProgress] = useState<ProcessingProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 如果文档已完成或失败，不轮询
  const shouldPoll = status === 'processing' || status === 'uploading';

  useEffect(() => {
    if (!shouldPoll) {
      return;
    }

    // 立即获取一次
    fetchProgress();

    // 每2秒轮询一次
    const interval = setInterval(() => {
      fetchProgress();
    }, 2000);

    return () => clearInterval(interval);
  }, [documentId, shouldPoll]);

  const fetchProgress = async () => {
    try {
      setLoading(true);
      setError(null);

      // 尝试通过 API Gateway
      let response = await fetch(`/api/knowledge/documents/${documentId}/progress`).catch(
        () => null
      );

      // 如果失败，尝试直接访问知识库服务
      if (!response || !response.ok) {
        const knowledgeBaseUrl =
          process.env.NEXT_PUBLIC_KNOWLEDGE_BASE_URL || 'http://localhost:8004';
        response = await fetch(`${knowledgeBaseUrl}/api/documents/${documentId}/progress`).catch(
          () => null
        );
      }

      if (response && response.ok) {
        const data = await response.json();
        setProgress(data);

        // 如果完成，通知父组件更新
        if (data.stage === 'completed' && onUpdate) {
          onUpdate();
        }
      } else {
        // 如果无法获取进度，使用文档状态推断
        setProgress(null);
      }
    } catch (err: any) {
      console.error('Failed to fetch progress:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 根据阶段确定阶段状态
  const getStageStatus = (stageKey: string): 'completed' | 'active' | 'pending' | 'failed' => {
    if (!progress) {
      // 根据文档状态推断
      if (status === 'processed') return 'completed';
      if (status === 'failed') return 'failed';
      if (status === 'processing' || status === 'uploading') {
        // 根据阶段顺序判断
        const currentIndex = PROCESSING_STAGES.findIndex((s) => s.key === stageKey);
        const uploadingIndex = PROCESSING_STAGES.findIndex((s) => s.key === 'uploading');
        if (currentIndex <= uploadingIndex) return 'active';
        return 'pending';
      }
      return 'pending';
    }

    const currentStage = progress.stage;
    const currentIndex = PROCESSING_STAGES.findIndex((s) => s.key === currentStage);
    const stageIndex = PROCESSING_STAGES.findIndex((s) => s.key === stageKey);

    if (progress.error && stageKey === currentStage) return 'failed';
    if (stageIndex < currentIndex) return 'completed';
    if (stageIndex === currentIndex) return 'active';
    return 'pending';
  };

  // 获取当前阶段的详细进度
  const getCurrentStageProgress = (): { current: number; total: number; percentage: number } => {
    if (!progress) return { current: 0, total: 0, percentage: 0 };

    if (progress.total_steps > 0) {
      return {
        current: progress.completed_steps,
        total: progress.total_steps,
        percentage: (progress.completed_steps / progress.total_steps) * 100,
      };
    }

    return { current: 0, total: 0, percentage: 0 };
  };

  // 格式化剩余时间
  const formatRemainingTime = (seconds?: number): string => {
    if (!seconds || seconds <= 0) return '';
    if (seconds < 60) return `约 ${Math.round(seconds)} 秒`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `约 ${minutes} 分 ${secs} 秒`;
  };

  const overallProgress = progress?.progress_percentage || 0;
  const currentStageProgress = getCurrentStageProgress();

  return (
    <div className="w-full">
      {/* 总体进度条 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">总体进度</span>
            {progress && (
              <span className="text-xs text-gray-500">
                {progress.stage === 'completed'
                  ? '已完成'
                  : progress.stage === 'failed'
                    ? '失败'
                    : `进行中: ${progress.current_step}`}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm font-bold text-blue-600">{overallProgress.toFixed(1)}%</span>
            {progress?.estimated_time_remaining && (
              <span className="text-xs text-gray-500">
                {formatRemainingTime(progress.estimated_time_remaining)}
              </span>
            )}
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all duration-300 ${
              progress?.stage === 'failed'
                ? 'bg-red-500'
                : progress?.stage === 'completed'
                  ? 'bg-green-500'
                  : 'bg-blue-600'
            }`}
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>

      {/* 处理阶段列表 */}
      <div className="space-y-2">
        {PROCESSING_STAGES.map((stage, index) => {
          const stageStatus = getStageStatus(stage.key);
          const isActive = stageStatus === 'active';
          const isCompleted = stageStatus === 'completed';
          const isFailed = stageStatus === 'failed';

          return (
            <div
              key={stage.key}
              className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-50 border border-blue-200'
                  : isCompleted
                    ? 'bg-green-50'
                    : isFailed
                      ? 'bg-red-50'
                      : 'bg-gray-50'
              }`}
            >
              {/* 阶段图标 */}
              <div className="flex-shrink-0">
                {isCompleted ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                ) : isFailed ? (
                  <XCircleIcon className="h-5 w-5 text-red-500" />
                ) : isActive ? (
                  <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />
                ) : (
                  <ClockIcon className="h-5 w-5 text-gray-400" />
                )}
              </div>

              {/* 阶段信息 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{stage.icon}</span>
                    <span
                      className={`text-sm font-medium ${
                        isActive
                          ? 'text-blue-700'
                          : isCompleted
                            ? 'text-green-700'
                            : isFailed
                              ? 'text-red-700'
                              : 'text-gray-500'
                      }`}
                    >
                      {stage.label}
                    </span>
                  </div>
                  {stage.weight > 0 && (
                    <span className="text-xs text-gray-400">{stage.weight}%</span>
                  )}
                </div>

                {/* 当前阶段的详细进度 */}
                {isActive && progress && currentStageProgress.total > 0 && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-600">{progress.current_step}</span>
                      <span className="text-xs text-gray-500">
                        {currentStageProgress.current} / {currentStageProgress.total}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${currentStageProgress.percentage}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* 错误信息 */}
                {isFailed && progress?.error && (
                  <div className="mt-1 text-xs text-red-600">{progress.error}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-700">
          无法获取实时进度: {error}
        </div>
      )}

      {/* 时间信息 */}
      {progress && (progress.started_at || progress.updated_at) && (
        <div className="mt-3 text-xs text-gray-500 space-y-1">
          {progress.started_at && (
            <div>开始时间: {new Date(progress.started_at).toLocaleString('zh-CN')}</div>
          )}
          {progress.updated_at && (
            <div>更新时间: {new Date(progress.updated_at).toLocaleString('zh-CN')}</div>
          )}
        </div>
      )}
    </div>
  );
}
