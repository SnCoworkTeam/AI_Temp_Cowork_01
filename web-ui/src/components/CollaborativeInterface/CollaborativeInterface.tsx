/**
 * 协同界面组件
 * 支持AI推荐和人工组装的协同工作流
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../UI/Card';
import { Button } from '../UI/Button';
import { Input } from '../UI/Input';

// 类型定义
interface Activity {
  id: string;
  name: string;
  description?: string;
  activity_type: string;
  business_domain: string;
  similarity_score?: number;
}

interface ExecutionSuggestion {
  activity_id: string;
  activity_name: string;
  capability_id?: string;
  capability_name?: string;
  input_schema?: Record<string, any>;
  estimated_time?: string;
  confidence: number;
}

interface UnifiedIntentResponse {
  user_input: string;
  base_intent: string;
  intent_type: string;
  confidence: number;
  suggested_activities: Activity[];
  execution_suggestions: ExecutionSuggestion[];
  reasoning: string;
  fallback_mode: boolean;
  query_time: number;
}

interface SelectedActivity {
  activity_id: string;
  capability_id?: string;
  parameters: Record<string, any>;
}

interface ExecutionPlan {
  plan_id: string;
  activities: Array<{
    activity_id: string;
    activity_name: string;
    capability_id?: string;
    capability_name?: string;
    parameters: Record<string, any>;
    confidence: number;
  }>;
  execution_order: string[];
  estimated_time?: string;
  total_confidence: number;
  created_at: string;
}

interface CollaborativeInterfaceProps {
  userInput: string;
  userId?: string;
  context?: Record<string, any>;
  onPlanAssembled?: (plan: ExecutionPlan) => void;
  onPlanExecuted?: (result: any) => void;
}

export const CollaborativeInterface: React.FC<CollaborativeInterfaceProps> = ({
  userInput,
  userId,
  context,
  onPlanAssembled,
  onPlanExecuted,
}) => {
  const [intentResponse, setIntentResponse] = useState<UnifiedIntentResponse | null>(null);
  const [selectedActivities, setSelectedActivities] = useState<SelectedActivity[]>([]);
  const [executionPlan, setExecutionPlan] = useState<ExecutionPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoSelected, setAutoSelected] = useState(false);

  // 1. 智能引导（用户体验优化）
  const guideUser = useCallback(
    (activities: Activity[], userInput: string) => {
      // 规则1：如果只有一个高置信度推荐，自动选择
      if (
        activities.length === 1 &&
        activities[0].similarity_score &&
        activities[0].similarity_score > 0.85
      ) {
        const suggestion = intentResponse?.execution_suggestions?.[0];
        if (suggestion) {
          handleSelectActivity(suggestion);
          setAutoSelected(true);
          console.log('已自动选择推荐的活动');
        }
      }

      // 规则2：根据用户输入的历史模式推荐（简化版）
      // TODO: 实现历史模式分析

      // 规则3：提供分步引导（简化版）
      if (isComplexOperation(userInput)) {
        console.log('复杂操作，建议分步进行');
      }
    },
    [intentResponse]
  );

  // 判断是否为复杂操作
  const isComplexOperation = (input: string): boolean => {
    const complexKeywords = ['处理', '分析', '生成', '创建多个', '批量'];
    return complexKeywords.some((keyword) => input.includes(keyword));
  };

  // 2. 参数智能填充（用户体验优化）
  const autoFillParameters = useCallback(
    async (activity: Activity, suggestion?: ExecutionSuggestion) => {
      try {
        // 从上下文提取参数（简化版）
        const extractedParams: Record<string, any> = {};

        // 从用户输入提取参数
        if (userInput.includes('订单')) {
          extractedParams['order_type'] = 'purchase';
        }

        // 从历史记录学习默认值（简化版）
        // TODO: 实现历史记录学习

        return extractedParams;
      } catch (error) {
        console.error('参数填充失败:', error);
        return {};
      }
    },
    [userInput]
  );

  // 3. 实时验证（用户体验优化）
  const validateInRealTime = useCallback(
    async (activityId: string, capabilityId: string | undefined, params: Record<string, any>) => {
      try {
        const response = await fetch('/api/v1/collaborative/execution/validate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            activity_id: activityId,
            capability_id: capabilityId,
            parameters: params,
          }),
        });

        if (!response.ok) {
          throw new Error('验证失败');
        }

        const validation = await response.json();
        return validation;
      } catch (error) {
        console.error('验证失败:', error);
        return { valid: false, errors: ['验证服务不可用'] };
      }
    },
    []
  );

  // 理解意图
  useEffect(() => {
    if (!userInput.trim()) {
      return;
    }

    const fetchIntent = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/v1/collaborative/intent/understand', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_input: userInput,
            context: context,
          }),
        });

        if (!response.ok) {
          throw new Error('意图理解失败');
        }

        const data = await response.json();
        setIntentResponse(data);

        // 智能引导
        if (data.suggested_activities) {
          guideUser(data.suggested_activities, userInput);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '意图理解失败');
      } finally {
        setLoading(false);
      }
    };

    fetchIntent();
  }, [userInput, context, guideUser]);

  // 选择活动
  const handleSelectActivity = useCallback(
    async (suggestion: ExecutionSuggestion) => {
      const activity = intentResponse?.suggested_activities.find(
        (a) => a.id === suggestion.activity_id
      );
      if (!activity) {
        return;
      }

      // 自动填充参数
      const params = await autoFillParameters(activity, suggestion);

      const selected: SelectedActivity = {
        activity_id: suggestion.activity_id,
        capability_id: suggestion.capability_id,
        parameters: params,
      };

      setSelectedActivities((prev) => {
        const exists = prev.find((s) => s.activity_id === selected.activity_id);
        if (exists) {
          return prev;
        }
        return [...prev, selected];
      });
    },
    [intentResponse, autoFillParameters]
  );

  // 移除活动
  const handleRemoveActivity = useCallback((activityId: string) => {
    setSelectedActivities((prev) => prev.filter((s) => s.activity_id !== activityId));
  }, []);

  // 更新参数
  const handleUpdateParameters = useCallback(
    (activityId: string, parameters: Record<string, any>) => {
      setSelectedActivities((prev) =>
        prev.map((s) => (s.activity_id === activityId ? { ...s, parameters } : s))
      );
    },
    []
  );

  // 组装执行计划
  const handleAssemblePlan = useCallback(async () => {
    if (selectedActivities.length === 0) {
      setError('请至少选择一个活动');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/collaborative/execution/assemble', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          selected_activities: selectedActivities,
          execution_order: null,
        }),
      });

      if (!response.ok) {
        throw new Error('组装执行计划失败');
      }

      const plan = await response.json();
      setExecutionPlan(plan);

      if (onPlanAssembled) {
        onPlanAssembled(plan);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '组装执行计划失败');
    } finally {
      setLoading(false);
    }
  }, [selectedActivities, onPlanAssembled]);

  // 执行计划
  const handleExecutePlan = useCallback(async () => {
    if (!executionPlan) {
      setError('没有可执行的计划');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/collaborative/execution/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan_id: executionPlan.plan_id,
          confirm: true,
        }),
      });

      if (!response.ok) {
        throw new Error('执行计划失败');
      }

      const result = await response.json();

      if (onPlanExecuted) {
        onPlanExecuted(result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '执行计划失败');
    } finally {
      setLoading(false);
    }
  }, [executionPlan, onPlanExecuted]);

  return (
    <div className="collaborative-interface space-y-6 p-6">
      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* 自动选择提示 */}
      {autoSelected && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded">
          已自动选择高置信度推荐的活动
        </div>
      )}

      {/* AI推荐区域 */}
      {intentResponse && (
        <Card title="AI推荐的活动">
          <div className="space-y-4">
            {intentResponse.suggested_activities.map((activity, index) => {
              const suggestion = intentResponse.execution_suggestions[index];
              const isSelected = selectedActivities.some((s) => s.activity_id === activity.id);

              return (
                <div
                  key={activity.id}
                  className={`border rounded-lg p-4 ${
                    isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="font-semibold text-lg">{activity.name}</h4>
                      {activity.description && (
                        <p className="text-gray-600 text-sm mt-1">{activity.description}</p>
                      )}
                      <div className="mt-2 flex gap-4 text-sm text-gray-500">
                        <span>类型: {activity.activity_type}</span>
                        <span>领域: {activity.business_domain}</span>
                        {activity.similarity_score && (
                          <span>相似度: {(activity.similarity_score * 100).toFixed(1)}%</span>
                        )}
                      </div>
                      {suggestion && (
                        <div className="mt-2 text-sm">
                          <span className="text-gray-600">推荐能力: </span>
                          <span className="font-medium">
                            {suggestion.capability_name || '未指定'}
                          </span>
                          <span className="ml-2 text-gray-500">
                            (置信度: {(suggestion.confidence * 100).toFixed(1)}%)
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="ml-4">
                      {!isSelected ? (
                        <Button
                          onClick={() => suggestion && handleSelectActivity(suggestion)}
                          disabled={loading}
                        >
                          选择
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          onClick={() => handleRemoveActivity(activity.id)}
                          disabled={loading}
                        >
                          移除
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* 用户选择区域 */}
      {selectedActivities.length > 0 && (
        <Card title="已选择的活动">
          <div className="space-y-4">
            {selectedActivities.map((selected) => {
              const activity = intentResponse?.suggested_activities.find(
                (a) => a.id === selected.activity_id
              );
              const suggestion = intentResponse?.execution_suggestions.find(
                (s) => s.activity_id === selected.activity_id
              );

              return (
                <div key={selected.activity_id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="font-semibold">{activity?.name || selected.activity_id}</h4>
                      {suggestion?.capability_name && (
                        <p className="text-sm text-gray-600 mt-1">
                          能力: {suggestion.capability_name}
                        </p>
                      )}
                      {/* 参数编辑区域 */}
                      {suggestion?.input_schema && (
                        <div className="mt-4 space-y-2">
                          <label className="text-sm font-medium">参数:</label>
                          {Object.entries(suggestion.input_schema).map(
                            ([key, schema]: [string, any]) => (
                              <div key={key} className="flex items-center gap-2">
                                <label className="text-sm w-24">{key}:</label>
                                <Input
                                  type="text"
                                  value={selected.parameters[key] || ''}
                                  onChange={(e) =>
                                    handleUpdateParameters(selected.activity_id, {
                                      ...selected.parameters,
                                      [key]: e.target.value,
                                    })
                                  }
                                  placeholder={schema.description || `输入${key}`}
                                  className="flex-1"
                                />
                              </div>
                            )
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-4">
            <Button onClick={handleAssemblePlan} disabled={loading} className="w-full">
              {loading ? '组装中...' : '组装执行计划'}
            </Button>
          </div>
        </Card>
      )}

      {/* 执行计划区域 */}
      {executionPlan && (
        <Card title="执行计划">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">计划ID: {executionPlan.plan_id}</p>
                <p className="text-sm text-gray-600">
                  总置信度: {(executionPlan.total_confidence * 100).toFixed(1)}%
                </p>
              </div>
              <Button onClick={handleExecutePlan} disabled={loading} variant="primary">
                {loading ? '执行中...' : '执行计划'}
              </Button>
            </div>
            <div className="space-y-2">
              <h5 className="font-medium">执行顺序:</h5>
              <ol className="list-decimal list-inside space-y-1">
                {executionPlan.execution_order.map((activityId, index) => {
                  const activity = executionPlan.activities.find(
                    (a) => a.activity_id === activityId
                  );
                  return (
                    <li key={activityId} className="text-sm">
                      {activity?.activity_name || activityId}
                    </li>
                  );
                })}
              </ol>
            </div>
          </div>
        </Card>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">处理中...</p>
        </div>
      )}
    </div>
  );
};

export default CollaborativeInterface;
