'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  ThinkingIcon,
  SearchIcon,
  DesignIcon,
  CheckIcon,
  AgentIcon,
  SuccessIcon,
  ErrorIcon,
  SynthIcon,
  LayerIcon,
} from './Icons';
import { Settings, ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';
import { MessageContent } from './MessageContent';

interface WorkflowChunk {
  type: string;
  stage?: string;
  message?: string;
  progress?: number;
  design?: any;
  network_summary?: any;
  analysis?: any;
  agent_id?: string;
  agent_type?: string;
  agent_task?: string;
  agent_result?: any;
  layer_number?: number;
  is_streaming?: boolean; // 标记是否为流式输出
  total_layers?: number;
  final_result?: any;
  result?: any; // 最终结果（备用字段）
  data?: any; // 数据字段（备用）
  error?: string;
}

interface DynamicWorkflowDisplayProps {
  chunks: WorkflowChunk[];
  onComplete?: (result: any) => void;
  showThinkingContent?: boolean;
  fallbackContent?: string;
}

export function DynamicWorkflowDisplay({
  chunks,
  onComplete,
  showThinkingContent = true,
  fallbackContent,
}: DynamicWorkflowDisplayProps) {
  const [thinkingProcess, setThinkingProcess] = useState<WorkflowChunk[]>([]);
  const [executionProcess, setExecutionProcess] = useState<WorkflowChunk[]>([]);
  const [finalResult, setFinalResult] = useState<any>(null);
  const [isComplete, setIsComplete] = useState(false);

  const allowThinkingContent = showThinkingContent !== false;

  const decodeEscapedText = (text: string): string =>
    text
      .replace(/\\n/g, '\n')
      .replace(/\\r/g, '\r')
      .replace(/\\t/g, '\t')
      .replace(/\\"/g, '"')
      .replace(/\\'/g, "'")
      .replace(/\\\\/g, '\\');

  const extractFieldFromString = (raw: string, field: string): string | null => {
    const regex = new RegExp(`['"]${field}['"]\\s*:\\s*(['"])([\\s\\S]*?)\\1`, 'm');
    const match = raw.match(regex);
    if (!match) return null;
    return decodeEscapedText(match[2].trim());
  };

  const normalizeFinalResult = (raw: any): any => {
    if (raw === null || raw === undefined) return null;
    if (typeof raw === 'string') {
      const text = raw.trim();
      // Attempt JSON parse first.
      if (text.startsWith('{') || text.startsWith('[')) {
        try {
          const parsed = JSON.parse(text);
          return normalizeFinalResult(parsed);
        } catch {
          // fall through
        }
      }
      const extracted =
        extractFieldFromString(text, 'formatted_output') ||
        extractFieldFromString(text, 'main_content') ||
        extractFieldFromString(text, 'summary');
      return {
        formatted_output: extracted || text,
      };
    }
    if (typeof raw === 'object') {
      if (raw.formatted_output || raw.synthesized_result) return raw;
      if (raw.final_result) {
        const nested = normalizeFinalResult(raw.final_result);
        if (nested && typeof nested === 'object') {
          return { ...raw, ...nested };
        }
        if (nested) {
          return { ...raw, formatted_output: nested };
        }
      }
      if (raw.result) {
        const nested = normalizeFinalResult(raw.result);
        if (nested && typeof nested === 'object') {
          return { ...raw, ...nested };
        }
        if (nested) {
          return { ...raw, formatted_output: nested };
        }
      }
    }
    return raw;
  };

  const extractFinalBlockFromContent = (content: string): string | null => {
    if (!content) return null;
    const markers = ['✅ 最终结果', '最终结果'];
    for (const marker of markers) {
      const idx = content.lastIndexOf(marker);
      if (idx >= 0) {
        const after = content.slice(idx + marker.length).trim();
        if (after) return after;
      }
    }
    return null;
  };

  const hasRenderableOutput = (value: any): boolean => {
    if (!value) return false;
    if (typeof value === 'string') return value.trim().length > 0;
    return Boolean(value.formatted_output || value.synthesized_result || value.main_content);
  };

  // 思考过程和执行过程的折叠状态
  const [showThinking, setShowThinking] = useState(() => {
    const saved = localStorage.getItem('workflow_show_thinking');
    return saved !== null ? saved === 'true' : true; // 默认显示
  });
  const [showExecution, setShowExecution] = useState(() => {
    const saved = localStorage.getItem('workflow_show_execution');
    return saved !== null ? saved === 'true' : true; // 默认显示
  });
  const [thinkingCollapsed, setThinkingCollapsed] = useState(false);
  const [executionCollapsed, setExecutionCollapsed] = useState(false);

  // 保存用户偏好
  useEffect(() => {
    localStorage.setItem('workflow_show_thinking', String(showThinking));
  }, [showThinking]);

  useEffect(() => {
    localStorage.setItem('workflow_show_execution', String(showExecution));
  }, [showExecution]);

  // 使用 useMemo 缓存合并结果，避免每次渲染都重新计算
  const mergedThinking = useMemo(() => {
    if (thinkingProcess.length === 0) {
      return { fullMessage: '', lastChunk: null };
    }

    // 获取最后一个thinking chunk（用于analysis和design）
    const lastChunk = thinkingProcess[thinkingProcess.length - 1];

    // 合并所有thinking chunks的message，确保获取完整内容
    // 流式输出时，每个chunk的message通常是累积的完整内容，所以使用最长的message
    let fullThinkingMessage = '';
    let maxLength = 0;

    // 只在开发环境或chunks数量变化较大时输出调试信息（减少日志频率）
    const shouldLog =
      process.env.NODE_ENV === 'development' &&
      (thinkingProcess.length % 10 === 0 || thinkingProcess.length <= 5);

    if (shouldLog && thinkingProcess.length > 0) {
      console.log('[DynamicWorkflowDisplay] Merging thinking chunks:', {
        totalChunks: thinkingProcess.length,
        chunkLengths: thinkingProcess.map((c, i) => ({
          index: i,
          length: c.message?.length || 0,
          preview: c.message?.substring(0, 50) || 'no message',
        })),
      });
    }

    // 首先，找到最长的message（通常是完整的累积内容）
    for (const chunk of thinkingProcess) {
      if (chunk.message && chunk.message.length > maxLength) {
        maxLength = chunk.message.length;
        fullThinkingMessage = chunk.message;
      }
    }

    // 如果没找到，使用最后一个chunk的message
    if (!fullThinkingMessage && lastChunk.message) {
      fullThinkingMessage = lastChunk.message;
    }

    // 如果仍然为空，尝试合并所有非空的message（作为最后的后备方案）
    if (!fullThinkingMessage) {
      const allMessages = thinkingProcess
        .map((chunk) => chunk.message)
        .filter((msg) => msg && msg.trim().length > 0);

      if (allMessages.length > 0) {
        // 使用最长的message
        fullThinkingMessage = allMessages.reduce(
          (longest, current) => (current.length > longest.length ? current : longest),
          allMessages[0]
        );
      }
    }

    // 只在开发环境且需要时输出调试信息
    if (shouldLog && fullThinkingMessage) {
      console.log('[DynamicWorkflowDisplay] Merged thinking message:', {
        length: fullThinkingMessage.length,
        preview: fullThinkingMessage.substring(0, 100),
        end: fullThinkingMessage.substring(Math.max(0, fullThinkingMessage.length - 50)),
      });
    } else if (!fullThinkingMessage && thinkingProcess.length > 0) {
      console.warn('[DynamicWorkflowDisplay] ⚠️ No thinking message found after merging!', {
        thinkingChunksCount: thinkingProcess.length,
        lastChunkHasMessage: !!lastChunk.message,
      });
    }

    return { fullMessage: fullThinkingMessage, lastChunk };
  }, [thinkingProcess]);

  useEffect(() => {
    const thinking: WorkflowChunk[] = [];
    const execution: WorkflowChunk[] = [];
    let result: any = null;
    let completed = false;
    let lastThinkingChunk: WorkflowChunk | null = null;

    for (const chunk of chunks) {
      if (chunk.type === 'thinking') {
        // 修复：保留所有thinking chunks，包括流式的，以便在合并时能找到最完整的message
        // 流式输出时，每个chunk的message可能是累积的，但最后一个可能不完整（如果流被中断）
        // 所以我们需要保留所有chunks，然后在合并时使用最长的message
        if ((chunk as any).is_streaming === true) {
          // 流式输出中，保留所有chunks（不替换）
          // 这样可以在合并时找到最完整的message
          lastThinkingChunk = chunk;
          thinking.push(chunk);
        } else {
          // 流式输出完成，添加最终的chunk
          // 不移除之前的流式chunks，因为最终chunk的message可能不完整
          thinking.push(chunk);
          lastThinkingChunk = null;
        }
      } else if (chunk.type === 'execution') {
        execution.push(chunk);
        // 检查是否是execution_complete阶段
        if (chunk.stage === 'execution_complete') {
          // 提取最终结果，支持多种格式
          result =
            chunk.final_result || chunk.result || chunk.data?.result || chunk.data?.final_result;
          completed = true;
          console.log(
            '[DynamicWorkflowDisplay] Execution complete (from execution type), final_result:',
            result
          );
        }
        // 即使不是execution_complete，也检查是否有final_result（可能流被中断但结果已发送）
        if (
          !result &&
          (chunk.final_result || chunk.result || chunk.data?.result || chunk.data?.final_result)
        ) {
          result =
            chunk.final_result || chunk.result || chunk.data?.result || chunk.data?.final_result;
          console.log(
            '[DynamicWorkflowDisplay] Found final_result in execution chunk (stage:',
            chunk.stage,
            '):',
            result
          );
        }
      } else if (chunk.type === 'design_complete') {
        thinking.push(chunk);
      } else if (chunk.type === 'execution_complete') {
        execution.push(chunk);
        // 提取最终结果，支持多种格式
        result =
          chunk.final_result || chunk.result || chunk.data?.result || chunk.data?.final_result;
        completed = true;
        console.log(
          '[DynamicWorkflowDisplay] Execution complete (from execution_complete type), final_result:',
          result
        );
        console.log(
          '[DynamicWorkflowDisplay] Full chunk:',
          JSON.stringify(chunk, null, 2).substring(0, 500)
        );
      }
    }

    // 如果有未完成的流式thinking chunk，添加到列表末尾
    if (lastThinkingChunk) {
      thinking.push(lastThinkingChunk);
    }

    // 如果执行过程已完成（有多个执行chunk且最后一个不是错误），尝试从最后一个执行chunk提取结果
    if (!completed && execution.length > 0 && !result) {
      const lastExecutionChunk = execution[execution.length - 1];
      // 检查最后一个执行chunk是否有结果（可能是agent_complete或layer_complete）
      if (lastExecutionChunk.agent_result?.output) {
        // 尝试从agent_result中提取结果
        const agentOutput = lastExecutionChunk.agent_result.output;
        if (typeof agentOutput === 'object' && agentOutput !== null) {
          result = {
            formatted_output:
              agentOutput.formatted_output ||
              agentOutput.formatted_text ||
              JSON.stringify(agentOutput, null, 2),
            output: agentOutput,
          };
          completed = true;
          console.log('[DynamicWorkflowDisplay] Extracted result from last agent_result:', result);
        } else if (typeof agentOutput === 'string' && agentOutput.length > 0) {
          result = {
            formatted_output: agentOutput,
            output: agentOutput,
          };
          completed = true;
          console.log(
            '[DynamicWorkflowDisplay] Extracted result from last agent_result (string):',
            result
          );
        }
      }
    }

    setThinkingProcess(thinking);
    setExecutionProcess(execution);
    let isCompleted = completed;
    let finalResultCandidate = result ? normalizeFinalResult(result) : null;

    if (
      (!finalResultCandidate || !hasRenderableOutput(finalResultCandidate)) &&
      fallbackContent &&
      fallbackContent.trim().length > 0
    ) {
      const extractedBlock = extractFinalBlockFromContent(fallbackContent);
      const fallbackNormalized = normalizeFinalResult(extractedBlock || fallbackContent);
      if (fallbackNormalized) {
        finalResultCandidate = fallbackNormalized;
      }
    }

    if (finalResultCandidate) {
      if (!isCompleted) {
        isCompleted = true;
      }
      setFinalResult(finalResultCandidate);
      onComplete?.(finalResultCandidate);
    }
    setIsComplete(isCompleted);
  }, [chunks, onComplete]);

  return (
    <div className="dynamic-workflow-display space-y-6 animate-fade-in">
      {/* 按照顺序显示：1. 思考内容 → 2. 分析处理内容 → 3. 最终结果 */}

      {/* 1. 思考过程 - 美化显示，确保执行过程中持续显示 */}
      {thinkingProcess.length > 0 && allowThinkingContent && showThinking && (
        <div className="thinking-process bg-blue-50 dark:bg-gray-800 rounded-lg p-5 border border-blue-200 dark:border-gray-700 transition-all duration-300">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                <ThinkingIcon className="text-white" size={16} />
              </div>
              <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                思考过程
                {!isComplete && (
                  <span className="text-xs font-normal text-blue-500 dark:text-blue-400 animate-pulse">
                    (思考中...)
                  </span>
                )}
              </h3>
            </div>
            {isComplete && (
              <button
                onClick={() => setThinkingCollapsed(!thinkingCollapsed)}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                title={thinkingCollapsed ? '展开' : '折叠'}
              >
                {thinkingCollapsed ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
              </button>
            )}
          </div>
          {!thinkingCollapsed && (
            <div className="space-y-3">
              {/* 显示所有thinking chunks，合并所有message以确保完整内容 */}
              {(() => {
                const { fullMessage: fullThinkingMessage, lastChunk } = mergedThinking;

                if (!lastChunk) {
                  return null;
                }

                // 显示分析结果（如果有）
                if (lastChunk.analysis) {
                  return (
                    <div key="thinking-analysis" className="space-y-3">
                      <div className="thinking-text bg-white/70 dark:bg-gray-800/70 rounded-lg p-4 border-l-4 border-blue-400 dark:border-blue-500 shadow-sm">
                        <div className="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-2 uppercase tracking-wide">
                          📊 请求分析结果
                        </div>
                        <div className="text-xs text-gray-700 dark:text-gray-300 font-mono bg-gray-50 dark:bg-gray-900/50 p-3 rounded overflow-x-auto">
                          {typeof lastChunk.analysis === 'string'
                            ? lastChunk.analysis
                            : JSON.stringify(lastChunk.analysis, null, 2)}
                        </div>
                      </div>
                      {lastChunk.message && (
                        <div className="thinking-text bg-white/70 dark:bg-gray-800/70 rounded-lg p-4 border-l-4 border-blue-400 dark:border-blue-500 shadow-sm">
                          <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap font-medium">
                            {lastChunk.message}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                }

                // 显示设计结果（如果有）
                if (lastChunk.design) {
                  return (
                    <div key="thinking-design" className="space-y-3">
                      <div className="thinking-text bg-white dark:bg-gray-800 rounded-lg p-4 border-l-4 border-purple-500 dark:border-purple-500">
                        <div className="text-xs font-semibold text-purple-600 dark:text-purple-400 mb-2 uppercase tracking-wide flex items-center gap-2">
                          <DesignIcon className="w-4 h-4" />
                          工作流设计
                        </div>
                        <div className="text-xs text-gray-700 dark:text-gray-300 space-y-2">
                          {lastChunk.design.agents && (
                            <div>
                              <span className="font-semibold">智能体数量:</span>{' '}
                              {lastChunk.design.agents.length}
                            </div>
                          )}
                          {lastChunk.design.execution_layers && (
                            <div>
                              <span className="font-semibold">执行层数:</span>{' '}
                              {lastChunk.design.execution_layers.length}
                            </div>
                          )}
                          {lastChunk.design.complexity && (
                            <div>
                              <span className="font-semibold">复杂度:</span>{' '}
                              {lastChunk.design.complexity}
                            </div>
                          )}
                          <details className="mt-2">
                            <summary className="cursor-pointer text-purple-600 dark:text-purple-400 hover:underline">
                              查看详细设计
                            </summary>
                            <div className="mt-2 font-mono bg-gray-50 dark:bg-gray-900/50 p-3 rounded overflow-x-auto text-xs">
                              {JSON.stringify(lastChunk.design, null, 2)}
                            </div>
                          </details>
                        </div>
                      </div>
                      {fullThinkingMessage && (
                        <div className="thinking-text bg-white/70 dark:bg-gray-800/70 rounded-lg p-4 border-l-4 border-blue-400 dark:border-blue-500 shadow-sm">
                          <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap font-medium">
                            {fullThinkingMessage}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                }

                // 显示思考消息（使用合并后的完整内容）
                if (fullThinkingMessage) {
                  // 调试：记录清理前后的内容长度
                  const originalLength = fullThinkingMessage.length;

                  let cleanMessage = fullThinkingMessage;
                  // 移除复杂度信息（如：medium复杂度、simple、complex等）
                  cleanMessage = cleanMessage.replace(
                    /[：:]\s*(simple|medium|complex|简单|中等|复杂|低|中|高)\s*复杂度?/gi,
                    ''
                  );
                  cleanMessage = cleanMessage.replace(
                    /复杂度[：:]\s*(simple|medium|complex|简单|中等|复杂|低|中|高)/gi,
                    ''
                  );
                  // 移除类型信息（如：类型: data_analysis等）
                  cleanMessage = cleanMessage.replace(/类型[：:]\s*[^，,\n]+/gi, '');
                  cleanMessage = cleanMessage.replace(/[，,]\s*类型[：:]\s*[^，,\n]+/gi, '');
                  // 移除预计时间信息
                  cleanMessage = cleanMessage.replace(/预计时间[：:]\s*[^，,\n]+/gi, '');
                  cleanMessage = cleanMessage.replace(/[，,]\s*预计时间[：:]\s*[^，,\n]+/gi, '');
                  // 移除智能体数量、执行层等统计信息（如果只是简单描述）
                  cleanMessage = cleanMessage.replace(/：\s*\d+个智能体[，,]\s*\d+个执行层/gi, '');
                  // 清理多余的空格和标点（但保留换行符，确保内容完整性）
                  // 注意：不要将所有空格替换为单个空格，这会破坏内容的可读性
                  // 只清理连续的空格（但保留换行符）
                  // 重要：不要使用 replace(/\s+/g, ' ')，这会破坏换行符，导致内容被压缩成一行
                  cleanMessage = cleanMessage.replace(/[ \t]+/g, ' ').trim(); // 只清理空格和制表符，保留换行符
                  cleanMessage = cleanMessage.replace(/[，,]\s*[，,]/g, '，');

                  // 调试：记录清理后的内容长度（必须在检查之前定义）
                  const cleanedLength = cleanMessage.length;

                  // 确保清理后的内容不会因为过度清理而丢失重要信息
                  // 如果清理后内容长度显著减少（超过30%），可能是清理逻辑过于激进，使用原始内容
                  if (originalLength > 100 && cleanedLength < originalLength * 0.7) {
                    console.warn(
                      '[DynamicWorkflowDisplay] ⚠️ Thinking message cleaned too aggressively, using original content'
                    );
                    cleanMessage = fullThinkingMessage; // 使用原始完整内容
                  }
                  if (originalLength > 100 && cleanedLength < originalLength * 0.8) {
                    // 如果清理后内容减少了超过20%，记录警告
                    console.warn(
                      '[DynamicWorkflowDisplay] ⚠️ Thinking message cleaned significantly:',
                      {
                        originalLength,
                        cleanedLength,
                        reduction:
                          (((originalLength - cleanedLength) / originalLength) * 100).toFixed(1) +
                          '%',
                        originalPreview: fullThinkingMessage.substring(0, 100),
                        cleanedPreview: cleanMessage.substring(0, 100),
                      }
                    );
                  }

                  // 如果清理后为空，跳过
                  if (!cleanMessage || cleanMessage.length < 3) {
                    console.warn(
                      '[DynamicWorkflowDisplay] ⚠️ Thinking message became empty after cleaning, using original'
                    );
                    cleanMessage = fullThinkingMessage; // 如果清理后为空，使用原始内容
                  }

                  return (
                    <div
                      key="thinking-last"
                      className="thinking-text bg-white/70 dark:bg-gray-800/70 rounded-lg p-4 border-l-4 border-blue-400 dark:border-blue-500 shadow-sm"
                    >
                      <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap font-medium">
                        {cleanMessage}
                      </div>
                    </div>
                  );
                }
                return null;
              })()}
            </div>
          )}
        </div>
      )}

      {/* 2. 分析和处理过程（执行过程） - 始终显示（如果有数据且用户选择显示） */}
      {executionProcess.length > 0 && showExecution && (
        <div className="execution-process bg-gradient-to-br from-green-50 via-emerald-50/50 to-teal-50/30 dark:from-green-900/20 dark:via-emerald-900/15 dark:to-teal-900/10 rounded-xl p-5 border-2 border-green-200/50 dark:border-green-800/50 shadow-lg backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                <Settings className="text-white" size={16} />
              </div>
              <h3 className="text-base font-semibold text-green-700 dark:text-green-300 flex items-center gap-2">
                执行过程
                {!isComplete && (
                  <span className="text-xs font-normal text-green-500 dark:text-green-400 animate-pulse">
                    (执行中...)
                  </span>
                )}
              </h3>
            </div>
            {isComplete && (
              <button
                onClick={() => setExecutionCollapsed(!executionCollapsed)}
                className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200 transition-colors p-1 rounded hover:bg-green-100 dark:hover:bg-green-900/30"
                title={executionCollapsed ? '展开' : '折叠'}
              >
                {executionCollapsed ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
              </button>
            )}
          </div>
          {!executionCollapsed && (
            <div className="space-y-3">
              {executionProcess.map((chunk, idx) => (
                <div key={idx} className="execution-step">
                  {chunk.stage === 'execution_start' && (
                    <div className="text-green-700 dark:text-green-300">
                      <div className="font-medium flex items-center gap-2">
                        {chunk.message}
                        {chunk.progress !== undefined && (
                          <div className="ml-auto flex items-center gap-2">
                            <div className="w-24 h-2 bg-green-200 dark:bg-green-800 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-green-500 dark:bg-green-400 transition-all duration-300"
                                style={{ width: `${chunk.progress}%` }}
                              ></div>
                            </div>
                            <span className="text-xs opacity-75">{chunk.progress}%</span>
                          </div>
                        )}
                      </div>
                      {(chunk as any).total_agents && (
                        <div className="text-xs mt-1 opacity-75">
                          {(chunk as any).total_agents}个智能体 | {chunk.total_layers}个执行层
                        </div>
                      )}
                      {chunk.network_summary && (
                        <div className="mt-2 p-3 bg-gradient-to-r from-green-50/80 via-emerald-50/60 to-green-50/80 dark:from-green-900/30 dark:via-emerald-900/20 dark:to-green-900/30 rounded-lg border-l-4 border-green-400 shadow-sm">
                          <div className="text-xs font-semibold text-green-700 dark:text-green-300 mb-2 uppercase tracking-wide flex items-center gap-2">
                            <LayerIcon className="w-3 h-3" />
                            网络设计摘要
                          </div>
                          <div className="text-xs text-gray-700 dark:text-gray-300 space-y-1">
                            {typeof chunk.network_summary === 'string' ? (
                              <div className="whitespace-pre-wrap">{chunk.network_summary}</div>
                            ) : (
                              <>
                                {chunk.network_summary.total_agents && (
                                  <div>
                                    <span className="font-semibold">智能体总数:</span>{' '}
                                    {chunk.network_summary.total_agents}
                                  </div>
                                )}
                                {chunk.network_summary.total_layers && (
                                  <div>
                                    <span className="font-semibold">执行层数:</span>{' '}
                                    {chunk.network_summary.total_layers}
                                  </div>
                                )}
                                {chunk.network_summary.complexity && (
                                  <div>
                                    <span className="font-semibold">复杂度:</span>{' '}
                                    {chunk.network_summary.complexity}
                                  </div>
                                )}
                                <details className="mt-2">
                                  <summary className="cursor-pointer text-green-600 dark:text-green-400 hover:underline text-xs">
                                    查看完整摘要
                                  </summary>
                                  <div className="mt-2 font-mono bg-white/50 dark:bg-gray-800/50 p-2 rounded overflow-x-auto text-xs">
                                    {JSON.stringify(chunk.network_summary, null, 2)}
                                  </div>
                                </details>
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {chunk.stage === 'layer_start' && (
                    <div className="ml-4 border-l-2 border-green-300 dark:border-green-600 pl-3">
                      <div className="text-green-600 dark:text-green-400 font-medium flex items-center justify-between">
                        <div className="flex items-center">
                          <LayerIcon className="mr-2 flex-shrink-0" size={16} />第{' '}
                          {chunk.layer_number}/{chunk.total_layers} 层
                        </div>
                        {chunk.progress !== undefined && (
                          <span className="text-xs opacity-75">{chunk.progress}%</span>
                        )}
                      </div>
                      <div className="text-xs text-green-500 dark:text-green-500 mt-1">
                        {chunk.message}
                      </div>
                    </div>
                  )}
                  {chunk.stage === 'agent_start' && (
                    <div className="ml-8 border-l-2 border-green-200 dark:border-green-700 pl-3">
                      <div className="flex items-center text-green-600 dark:text-green-400">
                        <AgentIcon className="mr-2 flex-shrink-0" size={16} />
                        <span className="text-xs flex-1">
                          {chunk.agent_task || chunk.agent_type || chunk.agent_id}
                        </span>
                        {chunk.progress !== undefined && (
                          <div className="ml-2 flex items-center gap-1.5">
                            <div className="w-16 h-1.5 bg-green-200 dark:bg-green-800 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-green-500 dark:bg-green-400 transition-all duration-300"
                                style={{ width: `${chunk.progress}%` }}
                              ></div>
                            </div>
                            <span className="text-xs opacity-75 min-w-[2.5rem]">
                              {chunk.progress}%
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {chunk.stage === 'agent_complete' && chunk.agent_result && (
                    <div className="ml-8 border-l-2 border-green-200 dark:border-green-700 pl-3">
                      <div className="flex items-center justify-between text-green-600 dark:text-green-400">
                        <div className="flex items-center gap-2 flex-1">
                          <SuccessIcon className="mr-2 flex-shrink-0" size={16} />
                          <span className="text-xs">{chunk.message}</span>
                          {chunk.agent_result.success === false && (
                            <span className="text-xs text-red-500 dark:text-red-400">(失败)</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs opacity-75">
                          {chunk.agent_result.execution_time != null &&
                            typeof chunk.agent_result.execution_time === 'number' && (
                              <span>{chunk.agent_result.execution_time.toFixed(2)}s</span>
                            )}
                          {chunk.agent_result.confidence != null &&
                            typeof chunk.agent_result.confidence === 'number' && (
                              <span className="px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                                置信度: {(chunk.agent_result.confidence * 100).toFixed(0)}%
                              </span>
                            )}
                          {chunk.agent_result.quality_score != null &&
                            typeof chunk.agent_result.quality_score === 'number' && (
                              <span className="px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
                                质量: {chunk.agent_result.quality_score.toFixed(0)}
                              </span>
                            )}
                        </div>
                      </div>

                      {/* 显示错误信息 */}
                      {chunk.agent_result.error && (
                        <div className="mt-2 p-2 bg-red-50/50 dark:bg-red-900/20 rounded text-xs text-red-700 dark:text-red-300 border-l-2 border-red-400">
                          <div className="font-semibold mb-1">错误:</div>
                          <div>{chunk.agent_result.error}</div>
                          {chunk.agent_result.error_code && (
                            <div className="mt-1 opacity-75">
                              错误代码: {chunk.agent_result.error_code}
                            </div>
                          )}
                        </div>
                      )}

                      {/* 显示警告信息 */}
                      {chunk.agent_result.warnings &&
                        Array.isArray(chunk.agent_result.warnings) &&
                        chunk.agent_result.warnings.length > 0 && (
                          <div className="mt-2 p-2 bg-amber-50/50 dark:bg-amber-900/20 rounded text-xs text-amber-700 dark:text-amber-300 border-l-2 border-amber-400">
                            <div className="font-semibold mb-1">⚠️ 警告:</div>
                            <ul className="list-disc list-inside space-y-1">
                              {chunk.agent_result.warnings.map((warning: string, idx: number) => (
                                <li key={idx}>{warning}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                      {/* 显示建议 */}
                      {chunk.agent_result.recommendations &&
                        Array.isArray(chunk.agent_result.recommendations) &&
                        chunk.agent_result.recommendations.length > 0 && (
                          <div className="mt-2 p-2 bg-blue-50/50 dark:bg-blue-900/20 rounded text-xs text-blue-700 dark:text-blue-300 border-l-2 border-blue-400">
                            <div className="font-semibold mb-1">💡 建议:</div>
                            <ul className="list-disc list-inside space-y-1">
                              {chunk.agent_result.recommendations.map(
                                (rec: string, idx: number) => (
                                  <li key={idx}>{rec}</li>
                                )
                              )}
                            </ul>
                          </div>
                        )}

                      {/* 显示下一步操作 */}
                      {chunk.agent_result.next_actions &&
                        Array.isArray(chunk.agent_result.next_actions) &&
                        chunk.agent_result.next_actions.length > 0 && (
                          <div className="mt-2 p-2 bg-green-50/50 dark:bg-green-900/20 rounded text-xs text-green-700 dark:text-green-300 border-l-2 border-green-400">
                            <div className="font-semibold mb-1">➡️ 下一步操作:</div>
                            <ul className="list-disc list-inside space-y-1">
                              {chunk.agent_result.next_actions.map(
                                (action: string, idx: number) => (
                                  <li key={idx}>{action}</li>
                                )
                              )}
                            </ul>
                          </div>
                        )}

                      {/* 显示产物（artifacts） */}
                      {chunk.agent_result.artifacts &&
                        Array.isArray(chunk.agent_result.artifacts) &&
                        chunk.agent_result.artifacts.length > 0 && (
                          <div className="mt-2 p-2 bg-indigo-50/50 dark:bg-indigo-900/20 rounded text-xs text-indigo-700 dark:text-indigo-300 border-l-2 border-indigo-400">
                            <div className="font-semibold mb-1">
                              📎 产物 ({chunk.agent_result.artifacts.length}):
                            </div>
                            <div className="space-y-1">
                              {chunk.agent_result.artifacts.map((artifact: any, idx: number) => (
                                <div key={idx} className="flex items-start gap-2">
                                  <span className="font-medium">
                                    {artifact.name || artifact.file_name || `产物 ${idx + 1}`}:
                                  </span>
                                  <span className="opacity-75">
                                    {artifact.type || artifact.mime_type || '未知类型'}
                                  </span>
                                  {artifact.url && (
                                    <a
                                      href={artifact.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-600 dark:text-blue-400 hover:underline"
                                    >
                                      查看
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                      {/* 显示执行元数据 */}
                      {chunk.agent_result.execution_metadata && (
                        <div className="mt-2 p-2 bg-gray-50/50 dark:bg-gray-800/50 rounded text-xs text-gray-600 dark:text-gray-400 border-l-2 border-gray-400">
                          <div className="font-semibold mb-1">📊 执行元数据:</div>
                          <div className="space-y-1">
                            {chunk.agent_result.execution_metadata.tokens_used && (
                              <div>
                                Token使用: {chunk.agent_result.execution_metadata.tokens_used}
                              </div>
                            )}
                            {chunk.agent_result.execution_metadata.model && (
                              <div>模型: {chunk.agent_result.execution_metadata.model}</div>
                            )}
                            {chunk.agent_result.execution_metadata.temperature !== undefined && (
                              <div>温度: {chunk.agent_result.execution_metadata.temperature}</div>
                            )}
                            {chunk.agent_result.execution_metadata.tools_used &&
                              Array.isArray(chunk.agent_result.execution_metadata.tools_used) && (
                                <div>
                                  工具:{' '}
                                  {chunk.agent_result.execution_metadata.tools_used.join(', ')}
                                </div>
                              )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {chunk.stage === 'agent_error' && (
                    <div className="ml-8 border-l-2 border-red-200 dark:border-red-700 pl-3">
                      <div className="text-red-600 dark:text-red-400 text-xs flex items-center">
                        <ErrorIcon className="mr-2 flex-shrink-0" size={16} />
                        {chunk.message}
                      </div>
                    </div>
                  )}
                  {chunk.stage === 'layer_complete' && (
                    <div className="ml-4 border-l-2 border-green-300 dark:border-green-600 pl-3">
                      <div className="text-green-600 dark:text-green-400 text-xs flex items-center">
                        <SuccessIcon className="mr-2 flex-shrink-0" size={16} />
                        {chunk.message}
                      </div>
                    </div>
                  )}
                  {chunk.stage === 'synthesizing' && (
                    <div className="text-green-600 dark:text-green-400 flex items-center">
                      <SynthIcon className="mr-2 flex-shrink-0" size={16} />
                      {chunk.message}
                    </div>
                  )}
                  {chunk.stage === 'execution_complete' && (
                    <div className="text-green-700 dark:text-green-300 font-medium flex items-center">
                      <SuccessIcon className="mr-2 flex-shrink-0" size={18} />
                      {chunk.message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 全局控制按钮 - 只在完成后显示，放在最终结果之前 */}
      {isComplete && (thinkingProcess.length > 0 || executionProcess.length > 0) && (
        <div className="flex items-center gap-3 mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <span className="text-xs font-medium text-gray-600 dark:text-gray-400">显示详情：</span>
          <div className="flex items-center gap-2">
            {allowThinkingContent && thinkingProcess.length > 0 && (
              <button
                onClick={() => setShowThinking(!showThinking)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/60 transition-all hover:scale-105 shadow-sm"
              >
                {showThinking ? <Eye size={14} /> : <EyeOff size={14} />}
                思考过程
              </button>
            )}
            {executionProcess.length > 0 && (
              <button
                onClick={() => setShowExecution(!showExecution)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-900/60 transition-all"
              >
                {showExecution ? <Eye size={14} /> : <EyeOff size={14} />}
                执行过程
              </button>
            )}
          </div>
        </div>
      )}

      {/* 3. 最终结果 - 只在执行完成后显示，放在最后 */}
      {/* 调试信息 */}
      {isComplete && !finalResult && (
        <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
          <div className="text-sm text-yellow-800 dark:text-yellow-300">
            ⚠️ 执行已完成，但未找到最终结果。请检查chunks数据。
            <details className="mt-2">
              <summary className="cursor-pointer text-xs">查看chunks数据</summary>
              <pre className="mt-2 text-xs overflow-auto max-h-40">
                {JSON.stringify(
                  chunks.filter((c) => c.type === 'execution_complete'),
                  null,
                  2
                )}
              </pre>
            </details>
          </div>
        </div>
      )}
      {isComplete && finalResult && (
        <div className="final-result mt-8 bg-gradient-to-br from-white via-blue-50/50 to-indigo-50/30 dark:from-gray-800 dark:via-gray-800 dark:to-gray-900 rounded-2xl p-8 border-2 border-blue-200/50 dark:border-gray-700 shadow-2xl backdrop-blur-sm relative overflow-hidden">
          {/* 装饰性背景元素 */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-400/10 to-purple-400/10 rounded-full blur-3xl -mr-32 -mt-32"></div>
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-green-400/10 to-blue-400/10 rounded-full blur-3xl -ml-24 -mb-24"></div>

          {/* 标题栏 */}
          <div className="flex items-center justify-between mb-8 pb-6 border-b-2 border-blue-200/50 dark:border-gray-700 relative z-10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center">
                <SuccessIcon className="text-white" size={20} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">分析结果</h3>
                {finalResult.synthesized_result?.title && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    {finalResult.synthesized_result.title}
                  </p>
                )}
              </div>
            </div>
            {finalResult.execution_summary && (
              <div className="text-xs text-gray-500 dark:text-gray-400 bg-white/60 dark:bg-gray-700/60 px-3 py-1.5 rounded-full border border-gray-200 dark:border-gray-600">
                {finalResult.execution_summary.executed_agents}/
                {finalResult.execution_summary.total_agents} 智能体 | 成功率:{' '}
                {finalResult.execution_summary.success_rate != null &&
                typeof finalResult.execution_summary.success_rate === 'number'
                  ? (finalResult.execution_summary.success_rate * 100).toFixed(1)
                  : '0.0'}
                %
              </div>
            )}
          </div>

          {/* 执行摘要 */}
          {finalResult.synthesized_result?.summary && (
            <div className="mb-8 p-5 bg-blue-50 dark:bg-gray-700 rounded-lg border-l-4 border-blue-500 relative z-10">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></div>
                <div className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wide">
                  执行摘要
                </div>
              </div>
              <div className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed pl-3.5">
                {finalResult.synthesized_result.summary}
              </div>
            </div>
          )}

          {/* 显示格式化的最终输出 - 使用MessageContent组件渲染Markdown */}
          {finalResult.formatted_output && (
            <div className="final-output-content bg-white dark:bg-gray-800 rounded-lg p-6 md:p-8 border border-gray-200 dark:border-gray-700 animate-fade-in relative overflow-hidden">
              {/* 内容区域 - 优化间距，减少空白 */}
              <div className="prose prose-lg dark:prose-invert max-w-none relative z-10 prose-headings:mt-4 prose-headings:mb-3 prose-p:my-3 prose-ul:my-3 prose-ol:my-3 prose-table:my-4">
                <MessageContent content={finalResult.formatted_output} isOwnMessage={false} />
              </div>
            </div>
          )}

          {/* 如果没有formatted_output，显示基本信息 */}
          {!finalResult.formatted_output && finalResult.synthesized_result && (
            <div className="space-y-4">
              {/* 主要发现 */}
              {finalResult.synthesized_result.key_findings &&
                finalResult.synthesized_result.key_findings.length > 0 && (
                  <div className="bg-amber-50/50 dark:bg-amber-900/20 rounded-lg p-4 border-l-4 border-amber-400">
                    <div className="text-sm font-semibold text-amber-800 dark:text-amber-300 mb-2">
                      主要发现
                    </div>
                    <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                      {finalResult.synthesized_result.key_findings.map(
                        (finding: string, idx: number) => (
                          <li key={idx} className="flex items-start">
                            <span className="text-amber-500 mr-2 mt-0.5">•</span>
                            <span>{finding}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}

              {/* 建议 */}
              {finalResult.synthesized_result.recommendations &&
                finalResult.synthesized_result.recommendations.length > 0 && (
                  <div className="bg-green-50/50 dark:bg-green-900/20 rounded-lg p-4 border-l-4 border-green-400">
                    <div className="text-sm font-semibold text-green-800 dark:text-green-300 mb-2">
                      建议与后续步骤
                    </div>
                    <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                      {finalResult.synthesized_result.recommendations.map(
                        (rec: string, idx: number) => (
                          <li key={idx} className="flex items-start">
                            <span className="text-green-500 mr-2 mt-0.5">→</span>
                            <span>{rec}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}

              {/* 主要内容 */}
              {finalResult.synthesized_result.main_content && (
                <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                  <div className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                    {finalResult.synthesized_result.main_content}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
