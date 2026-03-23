'use client';

import { useState, useEffect } from 'react';

// 类型定义
interface ErrorAnalysis {
  error_category: string;
  error_type: string;
  root_cause: string;
  confidence_score: number;
  related_components: string[];
  service_call_chain: string[];
  error_message: string;
  error_traceback?: string;
}

interface FixPlan {
  plan_id: string;
  fix_strategy: string;
  fix_steps: Array<{
    step: number;
    action: string;
    description: string;
    estimated_time: string;
  }>;
  estimated_time: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  impact_assessment: {
    affected_services: string[];
    user_impact: string;
    business_impact: string;
  };
  rollback_plan: {
    available: boolean;
    steps: string[];
  };
}

interface RiskAssessment {
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: Array<{
    factor: string;
    impact: string;
    probability: string;
  }>;
  impact_score: number;
  impact_level: 'low' | 'medium' | 'high' | 'critical';
  requires_approval: boolean;
}

interface DecisionOption {
  id: string;
  title: string;
  description: string;
  type: 'approve' | 'reject' | 'modify' | 'request_info';
  pros: string[];
  cons: string[];
  ai_recommendation_score: number;
  historical_similarity?: number;
  expert_advice?: string;
}

interface HistoricalCase {
  case_id: string;
  similar_error: string;
  fix_applied: string;
  outcome: 'success' | 'partial_success' | 'failed';
  effectiveness_score: number;
  date: string;
}

interface ApprovalRecord {
  id: string;
  decision: 'approved' | 'rejected' | 'pending';
  approver?: string;
  reason?: string;
  timestamp?: string;
  urgency_level?: 'normal' | 'high' | 'critical';
}

interface DecisionEffect {
  decision_id: string;
  fix_applied: boolean;
  fix_effectiveness: number;
  user_feedback_score?: number;
  business_impact_score?: number;
  lessons_learned?: string[];
  improvement_suggestions?: string[];
}

interface DecisionPanelProps {
  decisionId?: string;
  errorAnalysis?: ErrorAnalysis;
  fixPlans?: FixPlan[];
  riskAssessment?: RiskAssessment;
  onDecision?: (decision: 'approve' | 'reject' | 'modify', reason?: string) => void;
}

export function DecisionPanel({
  decisionId,
  errorAnalysis,
  fixPlans = [],
  riskAssessment,
  onDecision,
}: DecisionPanelProps) {
  const [activeTab, setActiveTab] = useState<'analysis' | 'options' | 'approval' | 'tracking'>(
    'analysis'
  );
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [approvalReason, setApprovalReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [decisionOptions, setDecisionOptions] = useState<DecisionOption[]>([]);
  const [historicalCases, setHistoricalCases] = useState<HistoricalCase[]>([]);
  const [approvalRecords, setApprovalRecords] = useState<ApprovalRecord[]>([]);
  const [decisionEffects, setDecisionEffects] = useState<DecisionEffect[]>([]);

  // 模拟数据加载
  useEffect(() => {
    if (decisionId) {
      loadDecisionData(decisionId);
    }
  }, [decisionId]);

  const loadDecisionData = async (id: string) => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise((resolve) => setTimeout(resolve, 500));

      // 生成决策选项
      const options: DecisionOption[] = [
        {
          id: 'approve-immediate',
          title: '立即批准修复方案',
          description: '批准当前修复方案并立即执行',
          type: 'approve',
          pros: ['快速解决问题', '降低用户影响', '自动化执行'],
          cons: ['风险较高', '需要监控'],
          ai_recommendation_score: 0.85,
          historical_similarity: 0.92,
          expert_advice: '建议在非高峰期执行',
        },
        {
          id: 'approve-with-modifications',
          title: '批准修改后的方案',
          description: '对修复方案进行小幅修改后批准',
          type: 'modify',
          pros: ['降低风险', '保留核心修复', '提高成功率'],
          cons: ['需要额外时间', '可能延迟修复'],
          ai_recommendation_score: 0.75,
          historical_similarity: 0.78,
        },
        {
          id: 'request-more-info',
          title: '请求更多信息',
          description: '需要更多上下文信息才能做出决策',
          type: 'request_info',
          pros: ['降低决策风险', '获得更多信息'],
          cons: ['延迟修复', '用户可能受影响'],
          ai_recommendation_score: 0.35,
        },
        {
          id: 'reject',
          title: '拒绝修复方案',
          description: '当前修复方案不适合，需要重新设计',
          type: 'reject',
          pros: ['避免错误修复', '保护系统稳定性'],
          cons: ['问题继续存在', '用户受影响延长'],
          ai_recommendation_score: 0.15,
        },
      ];

      setDecisionOptions(options);
      setSelectedOption(options[0].id);

      // 模拟历史案例
      setHistoricalCases([
        {
          case_id: 'case-001',
          similar_error: 'MCP工具执行超时',
          fix_applied: '增加重试机制和超时设置',
          outcome: 'success',
          effectiveness_score: 0.92,
          date: '2024-01-15',
        },
        {
          case_id: 'case-002',
          similar_error: '工作流节点执行失败',
          fix_applied: '状态恢复和节点重试',
          outcome: 'success',
          effectiveness_score: 0.88,
          date: '2024-01-10',
        },
      ]);

      // 模拟审批记录
      setApprovalRecords([
        {
          id: 'record-001',
          decision: 'pending',
          urgency_level: 'high',
        },
      ]);

      // 模拟决策效果
      setDecisionEffects([
        {
          decision_id: 'decision-001',
          fix_applied: true,
          fix_effectiveness: 0.85,
          user_feedback_score: 8.5,
          business_impact_score: 7.8,
          lessons_learned: ['超时设置需要根据实际情况调整', '重试机制有效'],
          improvement_suggestions: ['增加监控指标', '优化错误提示'],
        },
      ]);
    } catch (error) {
      console.error('Failed to load decision data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedOption) return;

    setLoading(true);
    try {
      const option = decisionOptions.find((o) => o.id === selectedOption);
      if (option?.type === 'approve' && onDecision) {
        await onDecision('approve', approvalReason || option.title);
      }

      // 更新审批记录
      const newRecord: ApprovalRecord = {
        id: `record-${Date.now()}`,
        decision: 'approved',
        approver: 'current_user', // 实际应该从认证上下文获取
        reason: approvalReason || option?.title,
        timestamp: new Date().toISOString(),
        urgency_level: riskAssessment?.risk_level === 'critical' ? 'critical' : 'high',
      };

      setApprovalRecords([...approvalRecords, newRecord]);
      setActiveTab('tracking');
    } catch (error) {
      console.error('Failed to approve:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedOption) return;

    setLoading(true);
    try {
      const option = decisionOptions.find((o) => o.id === selectedOption);
      if (option?.type === 'reject' && onDecision) {
        await onDecision('reject', approvalReason || '修复方案不适合');
      }

      // 更新审批记录
      const newRecord: ApprovalRecord = {
        id: `record-${Date.now()}`,
        decision: 'rejected',
        approver: 'current_user',
        reason: approvalReason || '修复方案不适合',
        timestamp: new Date().toISOString(),
      };

      setApprovalRecords([...approvalRecords, newRecord]);
    } catch (error) {
      console.error('Failed to reject:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'bg-green-100 text-green-800 border-green-500';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-500';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-500';
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-500';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-500';
    }
  };

  const getRecommendationColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* 标签页导航 */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px">
          {[
            { id: 'analysis', label: '错误分析', icon: '📊' },
            { id: 'options', label: '决策选项', icon: '💡' },
            { id: 'approval', label: '审批流程', icon: '✅' },
            { id: 'tracking', label: '效果追踪', icon: '📈' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="p-6">
        {/* 错误分析标签页 */}
        {activeTab === 'analysis' && (
          <div className="space-y-6">
            {/* 错误详细分析 */}
            {errorAnalysis && (
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">错误详细分析报告</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">错误类别</p>
                    <p className="text-base font-medium">{errorAnalysis.error_category}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">错误类型</p>
                    <p className="text-base font-medium">{errorAnalysis.error_type}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-gray-500">根因分析</p>
                    <p className="text-base">{errorAnalysis.root_cause}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">置信度</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${errorAnalysis.confidence_score * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">
                        {(errorAnalysis.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-gray-500 mb-2">相关组件</p>
                    <div className="flex flex-wrap gap-2">
                      {errorAnalysis.related_components.map((comp, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                        >
                          {comp}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 修复方案对比 */}
            {fixPlans.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">修复方案对比</h3>
                <div className="space-y-4">
                  {fixPlans.map((plan) => (
                    <div key={plan.plan_id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-gray-900">{plan.fix_strategy}</h4>
                          <p className="text-sm text-gray-500 mt-1">
                            预计时间: {plan.estimated_time}
                          </p>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskColor(
                            plan.risk_level
                          )}`}
                        >
                          {plan.risk_level.toUpperCase()}
                        </span>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-gray-700">修复步骤:</p>
                        <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                          {plan.fix_steps.map((step, idx) => (
                            <li key={idx}>
                              {step.action}: {step.description}
                            </li>
                          ))}
                        </ol>
                      </div>
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-sm text-gray-500">
                          影响范围: {plan.impact_assessment.affected_services.join(', ')}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                          用户影响: {plan.impact_assessment.user_impact}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 风险评估数据 */}
            {riskAssessment && (
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">风险评估数据</h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-500">风险评分</p>
                    <p className="text-2xl font-bold">{riskAssessment.risk_score}/10</p>
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-sm font-medium border mt-2 ${getRiskColor(
                        riskAssessment.risk_level
                      )}`}
                    >
                      {riskAssessment.risk_level.toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">影响评分</p>
                    <p className="text-2xl font-bold">{riskAssessment.impact_score}/10</p>
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-sm font-medium border mt-2 ${getRiskColor(
                        riskAssessment.impact_level
                      )}`}
                    >
                      {riskAssessment.impact_level.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">风险因素:</p>
                  <ul className="space-y-2">
                    {riskAssessment.risk_factors.map((factor, idx) => (
                      <li key={idx} className="text-sm text-gray-600">
                        <span className="font-medium">{factor.factor}:</span> {factor.impact} (概率:{' '}
                        {factor.probability})
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* 影响范围可视化 */}
            {errorAnalysis && errorAnalysis.service_call_chain.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">影响范围可视化</h3>
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="flex items-center justify-center space-x-4">
                    {errorAnalysis.service_call_chain.map((service, idx) => (
                      <div key={idx} className="flex items-center">
                        <div className="bg-blue-500 text-white rounded-lg px-4 py-2 font-medium">
                          {service}
                        </div>
                        {idx < errorAnalysis.service_call_chain.length - 1 && (
                          <svg
                            className="w-6 h-6 text-gray-400 mx-2"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5l7 7-7 7"
                            />
                          </svg>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 决策选项标签页 */}
        {activeTab === 'options' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">AI推荐的决策选项</h3>

            <div className="space-y-4">
              {decisionOptions.map((option) => (
                <div
                  key={option.id}
                  className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                    selectedOption === option.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedOption(option.id)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{option.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{option.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500 mb-1">AI推荐度</p>
                      <p
                        className={`text-lg font-bold ${getRecommendationColor(option.ai_recommendation_score)}`}
                      >
                        {(option.ai_recommendation_score * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>

                  {/* 利弊分析 */}
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div>
                      <p className="text-sm font-medium text-green-700 mb-2">✓ 优点</p>
                      <ul className="space-y-1">
                        {option.pros.map((pro, idx) => (
                          <li key={idx} className="text-sm text-gray-600 flex items-start">
                            <span className="text-green-500 mr-2">•</span>
                            {pro}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-red-700 mb-2">✗ 缺点</p>
                      <ul className="space-y-1">
                        {option.cons.map((con, idx) => (
                          <li key={idx} className="text-sm text-gray-600 flex items-start">
                            <span className="text-red-500 mr-2">•</span>
                            {con}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* 历史案例参考 */}
                  {option.historical_similarity && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-xs text-gray-500 mb-2">
                        历史相似度: {(option.historical_similarity * 100).toFixed(0)}%
                      </p>
                      {historicalCases
                        .filter((c) => c.outcome === 'success')
                        .slice(0, 2)
                        .map((case_) => (
                          <div
                            key={case_.case_id}
                            className="text-xs text-gray-600 bg-gray-50 p-2 rounded mt-2"
                          >
                            <span className="font-medium">{case_.similar_error}:</span>{' '}
                            {case_.fix_applied} (效果:{' '}
                            {(case_.effectiveness_score * 100).toFixed(0)}%)
                          </div>
                        ))}
                    </div>
                  )}

                  {/* 专家建议 */}
                  {option.expert_advice && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-xs font-medium text-gray-700 mb-1">💡 专家建议</p>
                      <p className="text-sm text-gray-600">{option.expert_advice}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 审批流程标签页 */}
        {activeTab === 'approval' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">快速审批流程</h3>

              {/* 选中的决策选项 */}
              {selectedOption && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-gray-600 mb-2">已选择:</p>
                  <p className="font-semibold text-gray-900">
                    {decisionOptions.find((o) => o.id === selectedOption)?.title}
                  </p>
                </div>
              )}

              {/* 审批理由 */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">审批理由</label>
                <textarea
                  value={approvalReason}
                  onChange={(e) => setApprovalReason(e.target.value)}
                  placeholder="请输入审批理由（可选）"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                />
              </div>

              {/* 审批按钮 */}
              <div className="flex gap-4">
                <button
                  onClick={handleApprove}
                  disabled={loading || !selectedOption}
                  className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {riskAssessment?.risk_level === 'low' ? '一键批准' : '批准修复方案'}
                </button>
                <button
                  onClick={handleReject}
                  disabled={loading}
                  className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  拒绝
                </button>
              </div>

              {/* 分级审批权限提示 */}
              {riskAssessment && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-gray-700">
                    {riskAssessment.risk_level === 'critical' && (
                      <span className="font-medium text-red-600">
                        ⚠️ 需要高级审批: 此操作风险较高，需要技术负责人审批
                      </span>
                    )}
                    {riskAssessment.risk_level === 'high' && (
                      <span className="font-medium text-orange-600">
                        ⚠️ 需要审批: 此操作需要团队负责人审批
                      </span>
                    )}
                    {riskAssessment.risk_level === 'medium' && (
                      <span className="font-medium text-yellow-600">
                        ℹ️ 建议审批: 建议在审批后执行
                      </span>
                    )}
                    {riskAssessment.risk_level === 'low' && (
                      <span className="font-medium text-green-600">✓ 低风险: 可以快速批准</span>
                    )}
                  </p>
                </div>
              )}

              {/* 审批记录追踪 */}
              <div className="mt-6">
                <h4 className="text-md font-semibold text-gray-900 mb-3">审批记录</h4>
                <div className="space-y-2">
                  {approvalRecords.map((record) => (
                    <div
                      key={record.id}
                      className="border border-gray-200 rounded-lg p-3 flex items-center justify-between"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {record.decision === 'approved' && '✓ 已批准'}
                          {record.decision === 'rejected' && '✗ 已拒绝'}
                          {record.decision === 'pending' && '⏳ 待审批'}
                        </p>
                        {record.reason && (
                          <p className="text-xs text-gray-500 mt-1">{record.reason}</p>
                        )}
                        {record.approver && (
                          <p className="text-xs text-gray-500 mt-1">审批人: {record.approver}</p>
                        )}
                        {record.timestamp && (
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(record.timestamp).toLocaleString()}
                          </p>
                        )}
                      </div>
                      {record.urgency_level && (
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            record.urgency_level === 'critical'
                              ? 'bg-red-100 text-red-800'
                              : record.urgency_level === 'high'
                                ? 'bg-orange-100 text-orange-800'
                                : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {record.urgency_level}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* 紧急通道 */}
              {riskAssessment?.risk_level === 'critical' && (
                <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
                  <p className="text-sm font-semibold text-red-800 mb-2">🚨 紧急通道</p>
                  <p className="text-sm text-red-700 mb-3">
                    检测到严重问题，可以启用紧急通道快速审批。紧急通道将跳过部分审批流程，请谨慎使用。
                  </p>
                  <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium">
                    启用紧急通道
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 效果追踪标签页 */}
        {activeTab === 'tracking' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">决策效果追踪</h3>

            {decisionEffects.map((effect) => (
              <div key={effect.decision_id} className="border border-gray-200 rounded-lg p-6">
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div>
                    <p className="text-sm text-gray-500">修复是否应用</p>
                    <p className="text-lg font-semibold">{effect.fix_applied ? '✓ 是' : '✗ 否'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">修复有效性</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${effect.fix_effectiveness * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-lg font-semibold">
                        {(effect.fix_effectiveness * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">用户反馈</p>
                    <p className="text-lg font-semibold">
                      {effect.user_feedback_score ? `${effect.user_feedback_score}/10` : 'N/A'}
                    </p>
                  </div>
                </div>

                {effect.business_impact_score && (
                  <div className="mb-6">
                    <p className="text-sm text-gray-500 mb-2">业务影响评分</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${(effect.business_impact_score / 10) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-semibold">
                        {effect.business_impact_score}/10
                      </span>
                    </div>
                  </div>
                )}

                {effect.lessons_learned && effect.lessons_learned.length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">经验总结</p>
                    <ul className="space-y-1">
                      {effect.lessons_learned.map((lesson, idx) => (
                        <li key={idx} className="text-sm text-gray-600 flex items-start">
                          <span className="text-blue-500 mr-2">•</span>
                          {lesson}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {effect.improvement_suggestions && effect.improvement_suggestions.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">持续优化建议</p>
                    <ul className="space-y-1">
                      {effect.improvement_suggestions.map((suggestion, idx) => (
                        <li key={idx} className="text-sm text-gray-600 flex items-start">
                          <span className="text-green-500 mr-2">→</span>
                          {suggestion}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}

            {decisionEffects.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p>暂无决策效果数据</p>
                <p className="text-sm mt-2">决策执行后将显示效果追踪信息</p>
              </div>
            )}
          </div>
        )}

        {loading && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}
      </div>
    </div>
  );
}
