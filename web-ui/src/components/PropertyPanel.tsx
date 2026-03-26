'use client';

import React, { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import {
  fetchAvailableLLMModels,
  fetchLLMDefaultConfig,
  getDefaultLLMModel,
} from '@/lib/config/llm';

interface PropertyPanelProps {
  node: Node | null;
  onUpdateNodeConfig: (nodeId: string, config: Record<string, any>) => void;
  onDeleteNode: (nodeId: string) => void;
}

interface LLMModel {
  value: string;
  label: string;
  provider: string;
}

export function PropertyPanel({ node, onUpdateNodeConfig, onDeleteNode }: PropertyPanelProps) {
  const [config, setConfig] = useState<Record<string, any>>({});
  const [nodeName, setNodeName] = useState('');
  const [availableModels, setAvailableModels] = useState<LLMModel[]>([]);
  const [defaultModel, setDefaultModel] = useState<string>('deepseek-chat');

  // 加载LLM配置
  useEffect(() => {
    const loadLLMConfig = async () => {
      try {
        const [models, defaultConfig] = await Promise.all([
          fetchAvailableLLMModels(),
          fetchLLMDefaultConfig(),
        ]);
        setAvailableModels(models);
        setDefaultModel(defaultConfig.model);
      } catch (error) {
        console.error('Failed to load LLM config:', error);
        // 使用默认值
        setAvailableModels([
          { value: 'deepseek-chat', label: 'DeepSeek Chat', provider: 'DeepSeek' },
          { value: 'gpt-4', label: 'GPT-4', provider: 'OpenAI' },
          { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', provider: 'OpenAI' },
        ]);
        setDefaultModel('deepseek-chat');
      }
    };
    loadLLMConfig();
  }, []);

  useEffect(() => {
    if (node) {
      setConfig(node.data.config || {});
      setNodeName(node.data.label || node.data.name || node.id);
    } else {
      setConfig({});
      setNodeName('');
    }
  }, [node]);

  const handleConfigChange = (key: string, value: any) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    if (node) {
      onUpdateNodeConfig(node.id, newConfig);
    }
  };

  const handleNameChange = (newName: string) => {
    setNodeName(newName);
    if (node) {
      onUpdateNodeConfig(node.id, { ...config, name: newName, label: newName });
    }
  };

  if (!node) {
    return (
      <div className="w-80 bg-white border-l shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">属性面板</h3>
        <p className="text-gray-500 text-sm">请选择一个节点来编辑属性</p>
      </div>
    );
  }

  const nodeType = node.type || 'task';

  return (
    <div className="w-80 bg-white border-l shadow-sm flex flex-col h-screen">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">节点属性</h3>
          <button
            onClick={() => onDeleteNode(node.id)}
            className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            删除
          </button>
        </div>
        <div className="text-sm text-gray-500">类型: {nodeType}</div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* 基本信息 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">节点名称</label>
          <input
            type="text"
            value={nodeName}
            onChange={(e) => handleNameChange(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
            placeholder="节点名称"
          />
        </div>

        {/* 根据节点类型显示不同的配置 */}
        {nodeType === 'llm' && <LLMNodeConfig config={config} onChange={handleConfigChange} />}

        {nodeType === 'tool' && <ToolNodeConfig config={config} onChange={handleConfigChange} />}

        {nodeType === 'condition' && (
          <ConditionNodeConfig config={config} onChange={handleConfigChange} />
        )}

        {nodeType === 'transform' && (
          <TransformNodeConfig config={config} onChange={handleConfigChange} />
        )}

        {nodeType === 'http' && <HTTPNodeConfig config={config} onChange={handleConfigChange} />}

        {nodeType === 'delay' && <DelayNodeConfig config={config} onChange={handleConfigChange} />}

        {nodeType === 'log' && <LogNodeConfig config={config} onChange={handleConfigChange} />}

        {nodeType === 'knowledge_search' && (
          <KnowledgeSearchNodeConfig config={config} onChange={handleConfigChange} />
        )}

        {nodeType === 'document_processing' && (
          <DocumentProcessingNodeConfig config={config} onChange={handleConfigChange} />
        )}

        {nodeType === 'knowledge_enhancement' && (
          <KnowledgeEnhancementNodeConfig config={config} onChange={handleConfigChange} />
        )}

        {nodeType === 'agent' && <AgentNodeConfig config={config} onChange={handleConfigChange} />}

        {/* 通用配置编辑器 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">高级配置 (JSON)</label>
          <textarea
            value={JSON.stringify(config, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                setConfig(parsed);
                if (node) {
                  onUpdateNodeConfig(node.id, parsed);
                }
              } catch {
                // 忽略无效JSON
              }
            }}
            className="w-full px-3 py-2 border rounded-lg font-mono text-xs"
            rows={8}
            placeholder='{"key": "value"}'
          />
        </div>
      </div>
    </div>
  );
}

// 知识搜索节点配置
function KnowledgeSearchNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">查询字段</label>
        <input
          type="text"
          value={config.query_field || 'query'}
          onChange={(e) => onChange('query_field', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
          placeholder="query"
        />
        <p className="mt-1 text-xs text-gray-500">从状态中获取查询的字段名</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">搜索类型</label>
        <select
          value={config.search_type || 'semantic'}
          onChange={(e) => onChange('search_type', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        >
          <option value="semantic">语义搜索</option>
          <option value="keyword">关键词搜索</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">返回数量</label>
        <input
          type="number"
          min="1"
          max="50"
          value={config.limit || 5}
          onChange={(e) => onChange('limit', parseInt(e.target.value))}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">最小相似度分数 (0-1)</label>
        <input
          type="number"
          min="0"
          max="1"
          step="0.1"
          value={config.min_score || 0.5}
          onChange={(e) => onChange('min_score', parseFloat(e.target.value))}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={config.summarize !== false}
          onChange={(e) => onChange('summarize', e.target.checked)}
          className="w-4 h-4"
        />
        <label className="text-sm text-gray-700">生成搜索结果摘要</label>
      </div>
    </div>
  );
}

// 文档处理节点配置
function DocumentProcessingNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">处理类型</label>
        <select
          value={config.process_type || 'parse'}
          onChange={(e) => onChange('process_type', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        >
          <option value="upload">上传文档</option>
          <option value="parse">解析文档</option>
          <option value="extract_metadata">提取元数据</option>
        </select>
      </div>

      {config.process_type === 'upload' ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">文件路径字段</label>
          <input
            type="text"
            value={config.file_path_field || 'file_path'}
            onChange={(e) => onChange('file_path_field', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
            placeholder="file_path"
          />
        </div>
      ) : (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">文档ID字段</label>
          <input
            type="text"
            value={config.input_field || 'document_id'}
            onChange={(e) => onChange('input_field', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
            placeholder="document_id"
          />
        </div>
      )}

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={config.extract_metadata !== false}
          onChange={(e) => onChange('extract_metadata', e.target.checked)}
          className="w-4 h-4"
        />
        <label className="text-sm text-gray-700">提取元数据</label>
      </div>
    </div>
  );
}

// 知识增强节点配置
function KnowledgeEnhancementNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">内容字段</label>
        <input
          type="text"
          value={config.content_field || 'content'}
          onChange={(e) => onChange('content_field', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
          placeholder="content"
        />
        <p className="mt-1 text-xs text-gray-500">从状态中获取要增强的内容字段名</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">增强策略</label>
        <select
          value={config.enhancement_strategy || 'search_and_merge'}
          onChange={(e) => onChange('enhancement_strategy', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        >
          <option value="search_and_merge">搜索并合并</option>
          <option value="context_expansion">上下文扩展</option>
          <option value="knowledge_graph">知识图谱</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">合并模式</label>
        <select
          value={config.merge_mode || 'context'}
          onChange={(e) => onChange('merge_mode', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        >
          <option value="append">追加</option>
          <option value="prepend">前置</option>
          <option value="replace">替换</option>
          <option value="context">上下文</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={config.enable_search !== false}
          onChange={(e) => onChange('enable_search', e.target.checked)}
          className="w-4 h-4"
        />
        <label className="text-sm text-gray-700">启用知识搜索</label>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={config.enable_graph !== false}
          onChange={(e) => onChange('enable_graph', e.target.checked)}
          className="w-4 h-4"
        />
        <label className="text-sm text-gray-700">启用知识图谱</label>
      </div>

      {config.enable_search && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">搜索返回数量</label>
          <input
            type="number"
            min="1"
            max="20"
            value={config.search_limit || 5}
            onChange={(e) => onChange('search_limit', parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>
      )}
    </div>
  );
}

// LLM节点配置
function LLMNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  const [documents, setDocuments] = useState<Array<{ id: string; filename: string }>>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [enableRAG, setEnableRAG] = useState(config.enable_rag || false);
  const [availableModels, setAvailableModels] = useState<LLMModel[]>([]);
  const [defaultModel, setDefaultModel] = useState<string>('deepseek-chat');

  // 加载LLM配置
  useEffect(() => {
    const loadLLMConfig = async () => {
      try {
        const [models, defaultConfig] = await Promise.all([
          fetchAvailableLLMModels(),
          fetchLLMDefaultConfig(),
        ]);
        setAvailableModels(models);
        setDefaultModel(defaultConfig.model);
      } catch (error) {
        console.error('Failed to load LLM config:', error);
        // 使用默认值
        setAvailableModels([
          { value: 'deepseek-chat', label: 'DeepSeek Chat', provider: 'DeepSeek' },
          { value: 'gpt-4', label: 'GPT-4', provider: 'OpenAI' },
          { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', provider: 'OpenAI' },
        ]);
        setDefaultModel('deepseek-chat');
      }
    };
    loadLLMConfig();
  }, []);

  // 加载文档列表
  useEffect(() => {
    if (enableRAG) {
      loadDocuments();
    }
  }, [enableRAG]);

  const loadDocuments = async () => {
    try {
      setLoadingDocs(true);
      const { knowledgeApi } = await import('@/lib/api/knowledge');
      const response = await knowledgeApi.listDocuments({ page: 1, page_size: 100 });
      setDocuments(response.documents || []);
    } catch (error) {
      console.error('Failed to load documents:', error);
      setDocuments([]);
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleRAGToggle = (enabled: boolean) => {
    setEnableRAG(enabled);
    onChange('enable_rag', enabled);
    if (!enabled) {
      onChange('knowledge_base_documents', []);
      onChange('rag_search_limit', 5);
      onChange('rag_min_score', 0.5);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">模型</label>
        <select
          value={config.model || defaultModel}
          onChange={(e) => onChange('model', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        >
          {availableModels.length > 0 ? (
            availableModels.map((model) => (
              <option key={model.value} value={model.value}>
                {model.label}
              </option>
            ))
          ) : (
            // Fallback选项
            <>
              <option value="deepseek-chat">DeepSeek Chat</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </>
          )}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">温度 (0-2)</label>
        <input
          type="number"
          min="0"
          max="2"
          step="0.1"
          value={config.temperature || 0.7}
          onChange={(e) => onChange('temperature', parseFloat(e.target.value))}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">提示词模板</label>
        <textarea
          value={config.prompt_template || ''}
          onChange={(e) => onChange('prompt_template', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
          rows={4}
          placeholder="使用 {variable} 引用状态变量，使用 {context} 引用知识库上下文"
        />
        <p className="mt-1 text-xs text-gray-500">
          启用RAG后，可以使用 {'{context}'} 占位符插入知识库检索结果
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">最大Token数</label>
        <input
          type="number"
          min="1"
          value={config.max_tokens || 2000}
          onChange={(e) => onChange('max_tokens', parseInt(e.target.value))}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      {/* RAG (检索增强生成) 配置 */}
      <div className="border-t pt-4 mt-4">
        <div className="flex items-center gap-2 mb-4">
          <input
            type="checkbox"
            checked={enableRAG}
            onChange={(e) => handleRAGToggle(e.target.checked)}
            className="w-4 h-4"
            id="enable-rag"
          />
          <label htmlFor="enable-rag" className="text-sm font-medium text-gray-700">
            启用知识库检索增强 (RAG)
          </label>
        </div>

        {enableRAG && (
          <div className="space-y-4 pl-6 border-l-2 border-blue-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">选择知识库文档</label>
              {loadingDocs ? (
                <div className="text-sm text-gray-500 py-2">加载文档列表中...</div>
              ) : documents.length === 0 ? (
                <div className="text-sm text-gray-500 py-2">暂无文档，请先上传文档到知识库</div>
              ) : (
                <select
                  multiple
                  value={
                    Array.isArray(config.knowledge_base_documents)
                      ? config.knowledge_base_documents
                      : []
                  }
                  onChange={(e) => {
                    const selected = Array.from(e.target.selectedOptions, (option) => option.value);
                    onChange('knowledge_base_documents', selected);
                  }}
                  className="w-full px-3 py-2 border rounded-lg min-h-[100px]"
                  size={5}
                >
                  {documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.filename}
                    </option>
                  ))}
                </select>
              )}
              <p className="mt-1 text-xs text-gray-500">
                按住 Ctrl/Cmd 键可多选文档，留空则搜索全部文档
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">检索查询字段</label>
              <input
                type="text"
                value={config.rag_query_field || 'query'}
                onChange={(e) => onChange('rag_query_field', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="query"
              />
              <p className="mt-1 text-xs text-gray-500">从工作流状态中获取检索查询的字段名</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">检索类型</label>
              <select
                value={config.rag_search_type || 'semantic'}
                onChange={(e) => onChange('rag_search_type', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="semantic">语义搜索</option>
                <option value="keyword">关键词搜索</option>
                <option value="hybrid">混合搜索</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">检索返回数量</label>
              <input
                type="number"
                min="1"
                max="20"
                value={config.rag_search_limit || 5}
                onChange={(e) => onChange('rag_search_limit', parseInt(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                最小相似度分数 (0-1)
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={config.rag_min_score || 0.5}
                onChange={(e) => onChange('rag_min_score', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// 工具节点配置
function ToolNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  const [toolName, setToolName] = useState(config.tool_name || '');
  const [parametersJson, setParametersJson] = useState(
    JSON.stringify(config.parameters || {}, null, 2)
  );

  const handleToolNameChange = (value: string) => {
    setToolName(value);
    onChange('tool_name', value);
  };

  const handleParametersChange = (value: string) => {
    setParametersJson(value);
    try {
      const parsed = JSON.parse(value);
      onChange('parameters', parsed);
    } catch {
      // 忽略无效JSON
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">工具名称</label>
        <input
          type="text"
          value={toolName}
          onChange={(e) => handleToolNameChange(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
          placeholder="sap_query"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">参数 (JSON)</label>
        <textarea
          value={parametersJson}
          onChange={(e) => handleParametersChange(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg font-mono text-xs"
          rows={6}
          placeholder='{"table": "MARA", "query": "..."}'
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">MCP Gateway URL</label>
        <input
          type="text"
          value={config.mcp_gateway_url || 'http://mcp-gateway:8001'}
          onChange={(e) => onChange('mcp_gateway_url', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>
    </div>
  );
}

// 条件节点配置
function ConditionNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">条件表达式</label>
        <textarea
          value={config.condition || 'True'}
          onChange={(e) => onChange('condition', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg font-mono text-xs"
          rows={3}
          placeholder='len(state.get("data", [])) > 0'
        />
        <p className="mt-1 text-xs text-gray-500">
          使用 state 访问工作流状态，例如: state.get(&quot;key&quot;)
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">真值分支标签</label>
        <input
          type="text"
          value={config.true_output || 'true'}
          onChange={(e) => onChange('true_output', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">假值分支标签</label>
        <input
          type="text"
          value={config.false_output || 'false'}
          onChange={(e) => onChange('false_output', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>
    </div>
  );
}

// 数据转换节点配置
function TransformNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">转换类型</label>
        <select
          value={config.transform || 'identity'}
          onChange={(e) => onChange('transform', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        >
          <option value="identity">不变换</option>
          <option value="mapping">字段映射</option>
          <option value="filter">过滤</option>
          <option value="format">格式化</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">映射配置 (JSON)</label>
        <textarea
          value={JSON.stringify(config.mapping || {}, null, 2)}
          onChange={(e) => {
            try {
              onChange('mapping', JSON.parse(e.target.value));
            } catch {
              // 忽略无效JSON
            }
          }}
          className="w-full px-3 py-2 border rounded-lg font-mono text-xs"
          rows={4}
          placeholder='{"target_key": "source_key"}'
        />
      </div>
    </div>
  );
}

// HTTP节点配置
function HTTPNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">URL</label>
        <input
          type="text"
          value={config.url || ''}
          onChange={(e) => onChange('url', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
          placeholder="https://api.example.com/endpoint"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">请求方法</label>
        <select
          value={config.method || 'GET'}
          onChange={(e) => onChange('method', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        >
          <option value="GET">GET</option>
          <option value="POST">POST</option>
          <option value="PUT">PUT</option>
          <option value="DELETE">DELETE</option>
          <option value="PATCH">PATCH</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">请求头 (JSON)</label>
        <textarea
          value={JSON.stringify(config.headers || {}, null, 2)}
          onChange={(e) => {
            try {
              onChange('headers', JSON.parse(e.target.value));
            } catch {
              // 忽略无效JSON
            }
          }}
          className="w-full px-3 py-2 border rounded-lg font-mono text-xs"
          rows={3}
          placeholder='{"Authorization": "Bearer ${token}"}'
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">请求体 (JSON)</label>
        <textarea
          value={JSON.stringify(config.body || {}, null, 2)}
          onChange={(e) => {
            try {
              onChange('body', JSON.parse(e.target.value));
            } catch {
              // 忽略无效JSON
            }
          }}
          className="w-full px-3 py-2 border rounded-lg font-mono text-xs"
          rows={4}
          placeholder='{"key": "value"}'
        />
      </div>
    </div>
  );
}

// 延迟节点配置
function DelayNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">延迟时间（秒）</label>
      <input
        type="number"
        min="0"
        step="0.1"
        value={config.delay_seconds || 1}
        onChange={(e) => onChange('delay_seconds', parseFloat(e.target.value))}
        className="w-full px-3 py-2 border rounded-lg"
      />
    </div>
  );
}

// 日志节点配置
function LogNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">日志级别</label>
        <select
          value={config.log_level || 'INFO'}
          onChange={(e) => onChange('log_level', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        >
          <option value="DEBUG">DEBUG</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">日志消息</label>
        <textarea
          value={config.message || ''}
          onChange={(e) => onChange('message', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
          rows={3}
          placeholder="使用 {variable} 引用状态变量"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">要记录的数据字段</label>
        <input
          type="text"
          value={Array.isArray(config.data) ? config.data.join(', ') : ''}
          onChange={(e) => {
            const fields = e.target.value
              .split(',')
              .map((s) => s.trim())
              .filter(Boolean);
            onChange('data', fields);
          }}
          className="w-full px-3 py-2 border rounded-lg"
          placeholder="field1, field2, field3"
        />
      </div>
    </div>
  );
}

// 智能体节点配置
function AgentNodeConfig({
  config,
  onChange,
}: {
  config: Record<string, any>;
  onChange: (key: string, value: any) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          智能体ID <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={config.agent_id || ''}
          onChange={(e) => onChange('agent_id', e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
          placeholder="agent-12345678-1234-1234-1234-123456789abc"
        />
        <p className="mt-1 text-xs text-gray-500">要执行的智能体ID（必需）</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">输入映射 (JSON)</label>
        <textarea
          value={JSON.stringify(config.input_mapping || {}, null, 2)}
          onChange={(e) => {
            try {
              onChange('input_mapping', JSON.parse(e.target.value));
            } catch {
              // 忽略无效JSON
            }
          }}
          className="w-full px-3 py-2 border rounded-lg font-mono text-xs"
          rows={4}
          placeholder='{"content": "data.message"}'
        />
        <p className="mt-1 text-xs text-gray-500">
          将工作流状态字段映射到智能体输入，例如: {'{'}&quot;content&quot;: &quot;data.message&quot;
          {'}'}
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">输出映射 (JSON)</label>
        <textarea
          value={JSON.stringify(config.output_mapping || {}, null, 2)}
          onChange={(e) => {
            try {
              onChange('output_mapping', JSON.parse(e.target.value));
            } catch {
              // 忽略无效JSON
            }
          }}
          className="w-full px-3 py-2 border rounded-lg font-mono text-xs"
          rows={4}
          placeholder='{"result": "content"}'
        />
        <p className="mt-1 text-xs text-gray-500">将智能体输出映射到工作流状态字段</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">重试次数</label>
        <input
          type="number"
          min="0"
          max="10"
          value={config.retry_count || 3}
          onChange={(e) => onChange('retry_count', parseInt(e.target.value))}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">重试延迟（秒）</label>
        <input
          type="number"
          min="0"
          step="0.1"
          value={config.retry_delay || 5}
          onChange={(e) => onChange('retry_delay', parseFloat(e.target.value))}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">超时时间（秒）</label>
        <input
          type="number"
          min="1"
          max="3600"
          value={config.timeout || 300}
          onChange={(e) => onChange('timeout', parseInt(e.target.value))}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">上下文窗口大小</label>
        <input
          type="number"
          min="1"
          max="100"
          value={config.context_window_size || 10}
          onChange={(e) => onChange('context_window_size', parseInt(e.target.value))}
          className="w-full px-3 py-2 border rounded-lg"
        />
        <p className="mt-1 text-xs text-gray-500">保留的对话历史消息数量</p>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={config.enable_streaming !== false}
          onChange={(e) => onChange('enable_streaming', e.target.checked)}
          className="w-4 h-4"
        />
        <label className="text-sm text-gray-700">启用流式输出</label>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={config.preserve_conversation !== false}
          onChange={(e) => onChange('preserve_conversation', e.target.checked)}
          className="w-4 h-4"
        />
        <label className="text-sm text-gray-700">保持对话上下文</label>
        <p className="text-xs text-gray-500 ml-2">跨工作流执行保持对话历史</p>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={config.enable_cache !== false}
          onChange={(e) => onChange('enable_cache', e.target.checked)}
          className="w-4 h-4"
        />
        <label className="text-sm text-gray-700">启用结果缓存</label>
      </div>
    </div>
  );
}
