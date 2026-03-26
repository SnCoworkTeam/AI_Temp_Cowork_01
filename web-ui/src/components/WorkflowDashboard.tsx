'use client';

import { useState, useEffect } from 'react';
import { getWorkflows, executeWorkflow } from '@/lib/api/workflow';

interface Workflow {
  name: string;
  description: string;
  version: string;
}

export function WorkflowDashboard() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const data = await getWorkflows();
      setWorkflows(data);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (workflowName: string) => {
    setExecuting(workflowName);
    try {
      const result = await executeWorkflow(workflowName, {});
      alert(`工作流执行成功: ${result.execution_id}`);
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      alert('工作流执行失败');
    } finally {
      setExecuting(null);
    }
  };

  if (loading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">工作流管理</h2>
      <div className="space-y-4">
        {workflows.map((workflow) => (
          <div
            key={workflow.name}
            className="border rounded-lg p-4 flex items-center justify-between"
          >
            <div>
              <h3 className="font-medium text-gray-900">{workflow.name}</h3>
              <p className="text-sm text-gray-500 mt-1">{workflow.description}</p>
              <span className="text-xs text-gray-400 mt-1">版本: {workflow.version}</span>
            </div>
            <button
              onClick={() => handleExecute(workflow.name)}
              disabled={executing === workflow.name}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {executing === workflow.name ? '执行中...' : '执行'}
            </button>
          </div>
        ))}
        {workflows.length === 0 && <p className="text-gray-500 text-center py-8">暂无工作流</p>}
      </div>
    </div>
  );
}
