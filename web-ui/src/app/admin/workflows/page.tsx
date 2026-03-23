'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function WorkflowsPage() {
  const [searchTerm, setSearchTerm] = useState('');

  // 模拟工作流数据
  const workflows = [
    {
      id: '1',
      name: 'SAP数据分析',
      description: '自动化SAP数据分析流程',
      status: 'active',
      executions: 156,
    },
    { id: '2', name: '数据同步', description: '同步多个数据源', status: 'active', executions: 89 },
    {
      id: '3',
      name: '报告生成',
      description: '自动生成业务报告',
      status: 'paused',
      executions: 23,
    },
  ];

  const filteredWorkflows = workflows.filter(
    (workflow) =>
      workflow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      workflow.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">工作流管理</h1>
          <p className="text-gray-600 mt-1">管理和监控业务流程</p>
        </div>
        <Link
          href="/workflow-designer"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-center"
        >
          + 创建工作流
        </Link>
      </div>

      {/* 搜索栏 */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <input
          type="text"
          placeholder="搜索工作流..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* 工作流列表 */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredWorkflows.map((workflow) => (
          <div
            key={workflow.id}
            className="bg-white rounded-lg shadow border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{workflow.name}</h3>
                <p className="text-sm text-gray-600">{workflow.description}</p>
              </div>
              <span
                className={`px-2 py-1 text-xs font-medium rounded ${
                  workflow.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                {workflow.status === 'active' ? '运行中' : '已暂停'}
              </span>
            </div>

            <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
              <span>执行次数: {workflow.executions}</span>
            </div>

            <div className="flex gap-2">
              <Link
                href={`/workflow-designer?id=${workflow.id}`}
                className="flex-1 px-4 py-2 text-sm text-center border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                编辑
              </Link>
              <button className="flex-1 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                执行
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredWorkflows.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
          <p className="text-gray-500 mb-4">未找到匹配的工作流</p>
          <Link
            href="/workflow-designer"
            className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            创建工作流
          </Link>
        </div>
      )}
    </div>
  );
}
