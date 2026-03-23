'use client';

import React, { useState } from 'react';
import { NodeTypeDefinition } from '@/types/workflow';

interface NodePanelProps {
  onAddNode: (nodeType: string, position: { x: number; y: number }) => void;
}

const nodeTypes: NodeTypeDefinition[] = [
  {
    type: 'start',
    label: '开始',
    icon: '▶',
    color: 'bg-green-500',
    category: '基础',
    defaultConfig: {},
  },
  {
    type: 'end',
    label: '结束',
    icon: '■',
    color: 'bg-red-500',
    category: '基础',
    defaultConfig: {},
  },
  {
    type: 'llm',
    label: 'LLM节点',
    icon: '🤖',
    color: 'bg-blue-500',
    category: 'AI',
    defaultConfig: {
      // 模型将从配置中心动态获取，这里只是占位符
      model: 'deepseek-chat', // 将在组件初始化时从配置中心更新
      temperature: 0.7,
      prompt_template: '{input}',
    },
  },
  {
    type: 'tool',
    label: '工具调用',
    icon: '🔧',
    color: 'bg-purple-500',
    category: '工具',
    defaultConfig: {
      tool_name: '',
      parameters: {},
    },
  },
  {
    type: 'condition',
    label: '条件判断',
    icon: '❓',
    color: 'bg-yellow-500',
    category: '逻辑',
    defaultConfig: {
      condition: 'True',
    },
  },
  {
    type: 'transform',
    label: '数据转换',
    icon: '🔄',
    color: 'bg-indigo-500',
    category: '数据处理',
    defaultConfig: {
      transform: 'identity',
      mapping: {},
    },
  },
  {
    type: 'http',
    label: 'HTTP请求',
    icon: '🌐',
    color: 'bg-teal-500',
    category: '集成',
    defaultConfig: {
      url: '',
      method: 'GET',
      headers: {},
      body: {},
    },
  },
  {
    type: 'delay',
    label: '延迟',
    icon: '⏱',
    color: 'bg-gray-500',
    category: '控制',
    defaultConfig: {
      delay_seconds: 1,
    },
  },
  {
    type: 'log',
    label: '日志',
    icon: '📝',
    color: 'bg-orange-500',
    category: '调试',
    defaultConfig: {
      message: 'Log message',
      log_level: 'INFO',
    },
  },
  {
    type: 'knowledge_search',
    label: '知识搜索',
    icon: '🔍',
    color: 'bg-cyan-500',
    category: '知识库',
    defaultConfig: {
      query_source: 'input',
      query_field: 'query',
      search_type: 'semantic',
      limit: 5,
      min_score: 0.5,
      summarize: true,
    },
  },
  {
    type: 'document_processing',
    label: '文档处理',
    icon: '📄',
    color: 'bg-amber-500',
    category: '知识库',
    defaultConfig: {
      process_type: 'parse',
      input_field: 'document_id',
      extract_metadata: true,
    },
  },
  {
    type: 'knowledge_enhancement',
    label: '知识增强',
    icon: '✨',
    color: 'bg-pink-500',
    category: '知识库',
    defaultConfig: {
      content_source: 'input',
      content_field: 'content',
      enhancement_strategy: 'search_and_merge',
      enable_search: true,
      enable_graph: true,
      merge_mode: 'context',
    },
  },
  {
    type: 'agent',
    label: '智能体节点',
    icon: '🤖',
    color: 'bg-emerald-500',
    category: 'AI',
    defaultConfig: {
      agent_id: '',
      input_mapping: {},
      output_mapping: {},
      retry_count: 3,
      retry_delay: 5,
      enable_streaming: false,
      context_window_size: 10,
      preserve_conversation: true,
    },
  },
];

export function NodePanel({ onAddNode }: NodePanelProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = Array.from(new Set(nodeTypes.map((n) => n.category)));

  const filteredNodes = nodeTypes.filter((node) => {
    const matchesSearch =
      node.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !selectedCategory || node.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-64 bg-white border-r shadow-sm flex flex-col h-screen">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold mb-3">节点面板</h2>

        {/* 搜索框 */}
        <input
          type="text"
          placeholder="搜索节点..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg text-sm"
        />

        {/* 分类筛选 */}
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-2 py-1 text-xs rounded ${
              !selectedCategory ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
            }`}
          >
            全部
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-2 py-1 text-xs rounded ${
                selectedCategory === category
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* 节点列表 */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {filteredNodes.map((node) => (
            <div
              key={node.type}
              draggable
              onDragStart={(e) => handleDragStart(e, node.type)}
              onClick={() => {
                // 点击时添加到画布中心（简化处理，实际应该添加到画布中心位置）
                onAddNode(node.type, { x: 400, y: 300 });
              }}
              className="flex items-center gap-3 p-3 border rounded-lg cursor-move hover:bg-gray-50 hover:shadow transition-all"
            >
              <div
                className={`w-10 h-10 rounded-lg ${node.color} flex items-center justify-center text-white text-lg`}
              >
                {node.icon}
              </div>
              <div className="flex-1">
                <div className="font-medium text-sm">{node.label}</div>
                <div className="text-xs text-gray-500">{node.type}</div>
              </div>
            </div>
          ))}
        </div>

        {filteredNodes.length === 0 && (
          <div className="text-center text-gray-500 text-sm py-8">未找到匹配的节点</div>
        )}
      </div>

      {/* 说明 */}
      <div className="p-4 border-t bg-gray-50 text-xs text-gray-600">
        <p className="mb-1">💡 提示：</p>
        <p>拖拽节点到画布，或点击节点添加到画布中心</p>
      </div>
    </div>
  );
}
