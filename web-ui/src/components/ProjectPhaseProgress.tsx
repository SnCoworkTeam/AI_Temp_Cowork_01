'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, Circle } from 'lucide-react';
import { apiGatewayClient } from '@/lib/api/client';

export interface PhaseCategory {
  id: string;
  code: string;
  name: string;
  sort_order: number;
}

interface ProjectPhaseProgressProps {
  currentPhase?: string; // 当前阶段ID或名称，例如 "01-准备/可研" 或基础数据分类ID
  className?: string;
  phases?: PhaseCategory[]; // 可选的阶段列表（如果提供，则不从API获取）
}

export default function ProjectPhaseProgress({
  currentPhase,
  className = '',
  phases: externalPhases,
}: ProjectPhaseProgressProps) {
  const [phases, setPhases] = useState<PhaseCategory[]>([]);
  const [loading, setLoading] = useState(true);

  // 如果外部提供了phases，直接使用，否则从API获取
  useEffect(() => {
    if (externalPhases && externalPhases.length > 0) {
      // 使用外部提供的phases
      setPhases(externalPhases);
      setLoading(false);
      return;
    }

    // 从基础数据API获取项目阶段列表（仅在未提供外部phases时）
    const loadPhases = async () => {
      try {
        setLoading(true);

        // 使用 apiGatewayClient 进行请求，它已经包含了超时和错误处理
        try {
          const data = await apiGatewayClient.get<{ items: any[] }>(
            '/api/v1/basic-data/categories?category_type=project_phase&limit=1000'
          );

          const phaseList = (data.items || []).filter((cat: any) => cat.is_active !== false);

          // 按sort_order排序，如果没有sort_order则按code排序
          phaseList.sort((a: PhaseCategory, b: PhaseCategory) => {
            if (a.sort_order !== b.sort_order) {
              return (a.sort_order || 0) - (b.sort_order || 0);
            }
            return (a.code || '').localeCompare(b.code || '');
          });
          setPhases(phaseList);
        } catch (fetchError: any) {
          // 静默处理所有错误，避免在控制台显示错误信息
          // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
          // 其他错误（包括超时、网络错误等）都静默处理
          // 设置空数组，避免页面崩溃
          setPhases([]);
        }
      } catch (error) {
        // 静默处理错误
        setPhases([]);
      } finally {
        setLoading(false);
      }
    };

    loadPhases();
  }, [externalPhases]); // 依赖externalPhases，如果提供了就不需要重新获取

  // 确定当前阶段索引
  const getCurrentPhaseIndex = (): number => {
    if (!currentPhase || phases.length === 0) return -1;

    // 优先通过ID匹配
    let index = phases.findIndex((p: PhaseCategory) => p.id === currentPhase);
    if (index !== -1) return index;

    // 尝试通过code匹配
    index = phases.findIndex((p: PhaseCategory) => {
      if (!p.code) return false;
      // 支持完整匹配或前缀匹配
      return (
        p.code === currentPhase ||
        p.code.startsWith(currentPhase) ||
        currentPhase.startsWith(p.code) ||
        p.code.replace(/[^0-9]/g, '') === currentPhase.replace(/[^0-9]/g, '')
      );
    });
    if (index !== -1) return index;

    // 尝试通过名称匹配
    index = phases.findIndex((p: PhaseCategory) => {
      if (!p.name) return false;
      return (
        p.name === currentPhase || p.name.includes(currentPhase) || currentPhase.includes(p.name)
      );
    });

    return index;
  };

  const currentPhaseIndex = getCurrentPhaseIndex();

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-4 ${className}`}>
        <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (phases.length === 0) {
    return (
      <div className={`text-sm text-gray-500 text-center py-4 ${className}`}>暂无项目阶段数据</div>
    );
  }

  return (
    <div className={`flex items-start justify-between gap-2 ${className}`}>
      {phases.map((phase, index) => {
        const isCompleted = currentPhaseIndex >= 0 && index < currentPhaseIndex;
        const isCurrent = currentPhaseIndex >= 0 && index === currentPhaseIndex;
        const isPending = currentPhaseIndex < 0 || index > currentPhaseIndex;

        return (
          <div key={phase.id || phase.code || index} className="flex items-start flex-1 relative">
            {/* 阶段节点 */}
            <div className="flex flex-col items-center flex-1 relative min-w-0">
              {/* 连接线 */}
              {index < phases.length - 1 && (
                <div
                  className={`absolute top-4 left-1/2 w-full h-0.5 ${
                    isCompleted ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                  style={{ zIndex: 0 }}
                />
              )}

              {/* 阶段图标 */}
              <div
                className={`relative z-10 flex flex-col items-center w-full ${
                  isCurrent ? 'scale-105' : ''
                }`}
              >
                {isCompleted ? (
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shadow-md">
                    <CheckCircle className="w-5 h-5 text-white" />
                  </div>
                ) : isCurrent ? (
                  <div className="w-8 h-8 rounded-full bg-blue-600 border-3 border-blue-200 flex items-center justify-center shadow-lg">
                    <Circle className="w-4 h-4 text-white fill-white" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gray-200 border-2 border-gray-300 flex items-center justify-center">
                    <Circle className="w-4 h-4 text-gray-400" />
                  </div>
                )}

                {/* 阶段标签 */}
                <div className="mt-2 text-center w-full">
                  {/* 只显示阶段名称，不显示code */}
                  {/* 如果name中包含"01-"、"02-"等前缀，则去掉前缀 */}
                  {(() => {
                    let displayName = phase.name || '';
                    // 去掉类似"01-"、"02-"这样的前缀
                    displayName = displayName.replace(/^\d{2}-/, '');
                    return (
                      <div
                        className={`text-xs mt-0.5 leading-tight ${
                          isCurrent
                            ? 'text-blue-600 font-semibold'
                            : isCompleted
                              ? 'text-gray-700'
                              : 'text-gray-400'
                        }`}
                      >
                        {displayName}
                      </div>
                    );
                  })()}
                  {isCurrent && (
                    <div className="mt-1 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium whitespace-nowrap">
                      当前
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

