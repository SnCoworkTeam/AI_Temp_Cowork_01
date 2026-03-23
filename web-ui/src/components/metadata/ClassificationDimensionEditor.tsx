'use client';

import React, { useState, useMemo } from 'react';
import {
  Building2,
  Database,
  RefreshCw,
  Shield,
  Tag,
  X,
  Plus,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  BUSINESS_DOMAINS,
  TECHNICAL_SOURCES,
  LIFECYCLE_STAGES,
  DATA_FORMATS,
  SECURITY_LEVELS,
  QUALITY_LEVELS,
  MODEL_STATUSES,
  WORKFLOW_EXECUTION_MODES,
  WORKFLOW_BUSINESS_DOMAINS,
  STANDARD_TAGS,
  getAllBusinessDomains,
  getAllTechnicalSources,
  getAllLifecycleStages,
  getBusinessDomainDisplayName,
  getTechnicalSourceDisplayName,
  getLifecycleStageDisplayName,
  type ClassificationDimensions,
} from '@/lib/classification-standards';
import { getClassificationDisplayName } from '@/lib/metadata-classification';

type MetadataType = 'data-assets' | 'workflows' | 'ai-models' | 'business-entities';

interface ClassificationDimensionEditorProps {
  type: MetadataType;
  dimensions?:
    | ClassificationDimensions
    | {
        primary?: string;
        business?: { domain?: string; criticality?: string };
        technical?: { source?: string; format?: string; framework?: string };
        lifecycle?: { stage?: string; status?: string; freshness?: string };
        governance?: { security?: string; quality?: string; compliance?: string[] };
      };
  standardizedTags?: string[];
  primaryClassification?: string;
  onChange?: (dimensions: ClassificationDimensions, tags: string[]) => void;
  onPrimaryClassificationChange?: (classification: string) => void;
  compact?: boolean;
  readOnly?: boolean;
}

export function ClassificationDimensionEditor({
  type,
  dimensions = {},
  standardizedTags = [],
  primaryClassification,
  onChange,
  onPrimaryClassificationChange,
  compact = false,
  readOnly = false,
}: ClassificationDimensionEditorProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['business', 'technical'])
  );
  const [tagInput, setTagInput] = useState('');

  // 根据类型获取可用的维度选项
  const availableDimensions = useMemo(() => {
    const dims: {
      business?: { domain?: string[] };
      technical?: { source?: string[]; format?: string[]; framework?: string[] };
      lifecycle?: { stage?: string[]; status?: string[] };
      governance?: { security?: string[]; quality?: string[] };
    } = {};

    // 业务维度
    dims.business = {
      domain:
        type === 'workflows' ? Object.keys(WORKFLOW_BUSINESS_DOMAINS) : getAllBusinessDomains(),
    };

    // 技术维度
    dims.technical = {
      source: getAllTechnicalSources(),
      format: type === 'data-assets' ? Object.keys(DATA_FORMATS) : undefined,
      framework:
        type === 'ai-models'
          ? ['pytorch', 'tensorflow', 'huggingface', 'scikit_learn', 'custom']
          : undefined,
    };

    // 生命周期维度
    dims.lifecycle = {
      stage: getAllLifecycleStages(),
      status: type === 'ai-models' ? Object.keys(MODEL_STATUSES) : undefined,
    };

    // 治理维度
    dims.governance = {
      security: Object.keys(SECURITY_LEVELS),
      quality: Object.keys(QUALITY_LEVELS),
    };

    return dims;
  }, [type]);

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const updateDimension = (dimensionPath: string[], value: string | undefined) => {
    const newDimensions = JSON.parse(JSON.stringify(dimensions)) as ClassificationDimensions;

    let current: any = newDimensions;
    for (let i = 0; i < dimensionPath.length - 1; i++) {
      const key = dimensionPath[i];
      if (!current[key]) {
        current[key] = {};
      }
      current = current[key];
    }

    const lastKey = dimensionPath[dimensionPath.length - 1];
    if (value) {
      current[lastKey] = value;
    } else {
      delete current[lastKey];
    }

    onChange?.(newDimensions, standardizedTags);
  };

  const addTag = (tag: string) => {
    if (tag && !standardizedTags.includes(tag)) {
      const newTags = [...standardizedTags, tag];
      onChange?.(dimensions, newTags);
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    const newTags = standardizedTags.filter((t) => t !== tag);
    onChange?.(dimensions, newTags);
  };

  const handleTagInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      addTag(tagInput.trim());
    }
  };

  if (compact) {
    return (
      <div className="space-y-2">
        {/* 主分类选择 */}
        {onPrimaryClassificationChange && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">主分类</label>
            <select
              value={primaryClassification || ''}
              onChange={(e) => onPrimaryClassificationChange(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              <option value="">未选择</option>
              {/* 这里需要根据type获取主分类选项 */}
            </select>
          </div>
        )}

        {/* 简化的维度选择 */}
        <div className="grid grid-cols-2 gap-2">
          {availableDimensions.business?.domain && (
            <div>
              <label className="block text-xs text-gray-600 mb-1">业务领域</label>
              <select
                value={dimensions.business?.domain || ''}
                onChange={(e) =>
                  updateDimension(['business', 'domain'], e.target.value || undefined)
                }
                className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
              >
                <option value="">未选择</option>
                {availableDimensions.business.domain.map((domain) => (
                  <option key={domain} value={domain}>
                    {getBusinessDomainDisplayName(domain)}
                  </option>
                ))}
              </select>
            </div>
          )}

          {availableDimensions.technical?.source && (
            <div>
              <label className="block text-xs text-gray-600 mb-1">技术来源</label>
              <select
                value={dimensions.technical?.source || ''}
                onChange={(e) =>
                  updateDimension(['technical', 'source'], e.target.value || undefined)
                }
                className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
              >
                <option value="">未选择</option>
                {availableDimensions.technical.source.map((source) => (
                  <option key={source} value={source}>
                    {getTechnicalSourceDisplayName(source)}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 主分类选择 */}
      {onPrimaryClassificationChange && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">主分类</label>
          <select
            value={primaryClassification || ''}
            onChange={(e) => onPrimaryClassificationChange(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">未选择</option>
            {/* 主分类选项需要从metadata-classification.ts获取 */}
          </select>
        </div>
      )}

      {/* 业务维度 */}
      {availableDimensions.business && (
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('business')}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-gray-500" />
              <span className="font-medium text-gray-900">业务维度</span>
            </div>
            {expandedSections.has('business') ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </button>

          {expandedSections.has('business') && (
            <div className="p-4 space-y-3 border-t border-gray-200">
              {availableDimensions.business.domain && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">业务领域</label>
                  <select
                    value={dimensions.business?.domain || ''}
                    onChange={(e) =>
                      updateDimension(['business', 'domain'], e.target.value || undefined)
                    }
                    disabled={readOnly}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  >
                    <option value="">未选择</option>
                    {availableDimensions.business.domain.map((domain) => (
                      <option key={domain} value={domain}>
                        {getBusinessDomainDisplayName(domain)}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 技术维度 */}
      {availableDimensions.technical && (
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('technical')}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-gray-500" />
              <span className="font-medium text-gray-900">技术维度</span>
            </div>
            {expandedSections.has('technical') ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </button>

          {expandedSections.has('technical') && (
            <div className="p-4 space-y-3 border-t border-gray-200">
              {availableDimensions.technical.source && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">技术来源</label>
                  <select
                    value={dimensions.technical?.source || ''}
                    onChange={(e) =>
                      updateDimension(['technical', 'source'], e.target.value || undefined)
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">未选择</option>
                    {availableDimensions.technical.source.map((source) => (
                      <option key={source} value={source}>
                        {getTechnicalSourceDisplayName(source)}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {availableDimensions.technical.format && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">数据格式</label>
                  <select
                    value={dimensions.technical?.format || ''}
                    onChange={(e) =>
                      updateDimension(['technical', 'format'], e.target.value || undefined)
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">未选择</option>
                    {availableDimensions.technical.format.map((format) => (
                      <option key={format} value={format}>
                        {format}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 生命周期维度 */}
      {availableDimensions.lifecycle && (
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('lifecycle')}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-gray-500" />
              <span className="font-medium text-gray-900">生命周期维度</span>
            </div>
            {expandedSections.has('lifecycle') ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </button>

          {expandedSections.has('lifecycle') && (
            <div className="p-4 space-y-3 border-t border-gray-200">
              {availableDimensions.lifecycle.stage && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    生命周期阶段
                  </label>
                  <select
                    value={dimensions.lifecycle?.stage || ''}
                    onChange={(e) =>
                      updateDimension(['lifecycle', 'stage'], e.target.value || undefined)
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">未选择</option>
                    {availableDimensions.lifecycle.stage.map((stage) => (
                      <option key={stage} value={stage}>
                        {getLifecycleStageDisplayName(stage)}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {availableDimensions.lifecycle.status && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">状态</label>
                  <select
                    value={dimensions.lifecycle?.status || ''}
                    onChange={(e) =>
                      updateDimension(['lifecycle', 'status'], e.target.value || undefined)
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">未选择</option>
                    {availableDimensions.lifecycle.status.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 治理维度 */}
      {availableDimensions.governance && (
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('governance')}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-gray-500" />
              <span className="font-medium text-gray-900">治理维度</span>
            </div>
            {expandedSections.has('governance') ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </button>

          {expandedSections.has('governance') && (
            <div className="p-4 space-y-3 border-t border-gray-200">
              {availableDimensions.governance.security && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">安全等级</label>
                  <select
                    value={dimensions.governance?.security || ''}
                    onChange={(e) =>
                      updateDimension(['governance', 'security'], e.target.value || undefined)
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">未选择</option>
                    {availableDimensions.governance.security.map((security) => (
                      <option key={security} value={security}>
                        {security}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {availableDimensions.governance.quality && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">质量等级</label>
                  <select
                    value={dimensions.governance?.quality || ''}
                    onChange={(e) =>
                      updateDimension(['governance', 'quality'], e.target.value || undefined)
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">未选择</option>
                    {availableDimensions.governance.quality.map((quality) => (
                      <option key={quality} value={quality}>
                        {quality}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 标准化标签 */}
      <div className="border border-gray-200 rounded-lg">
        <button
          onClick={() => toggleSection('tags')}
          className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4 text-gray-500" />
            <span className="font-medium text-gray-900">标准化标签</span>
            {standardizedTags.length > 0 && (
              <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full">
                {standardizedTags.length}
              </span>
            )}
          </div>
          {expandedSections.has('tags') ? (
            <ChevronUp className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          )}
        </button>

        {expandedSections.has('tags') && (
          <div className="p-4 space-y-3 border-t border-gray-200">
            {/* 标签输入 */}
            <div className="flex gap-2">
              {!readOnly && (
                <>
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={handleTagInputKeyDown}
                    placeholder="输入标签并按Enter添加"
                    className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => addTag(tagInput.trim())}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </>
              )}
            </div>

            {/* 标准标签建议 */}
            <div>
              <label className="block text-xs text-gray-600 mb-2">建议标签</label>
              <div className="flex flex-wrap gap-2">
                {Object.entries(STANDARD_TAGS)
                  .slice(0, 10)
                  .map(([key, name]) => (
                    <button
                      key={key}
                      onClick={() => addTag(key)}
                      disabled={standardizedTags.includes(key)}
                      className={`px-2 py-1 text-xs rounded border transition-colors ${
                        standardizedTags.includes(key)
                          ? 'bg-gray-100 text-gray-400 border-gray-300 cursor-not-allowed'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-50 hover:border-blue-300'
                      }`}
                    >
                      {name}
                    </button>
                  ))}
              </div>
            </div>

            {/* 已添加的标签 */}
            {standardizedTags.length > 0 && (
              <div>
                <label className="block text-xs text-gray-600 mb-2">已添加标签</label>
                <div className="flex flex-wrap gap-2">
                  {standardizedTags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded"
                    >
                      {STANDARD_TAGS[tag as keyof typeof STANDARD_TAGS] || tag}
                      <button onClick={() => removeTag(tag)} className="hover:text-blue-900">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
