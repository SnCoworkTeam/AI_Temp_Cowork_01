'use client';

import React, { useState, useEffect } from 'react';
import { useChat } from '@/hooks/useChat';
import { MessageList } from '@/components/MessageList';
import { MessageInput } from '@/components/MessageInput';
import { WorkflowProgress } from './WorkflowProgress';
import { useAuth } from '@/contexts/AuthContext';
import { AuthGuard } from '@/components/AuthGuard';
import { listWorkflows, executeWorkflowById, WorkflowListItem } from '@/lib/api/workflow';

interface WorkflowInChatProps {
  sessionId?: string;
}

export const WorkflowInChat: React.FC<WorkflowInChatProps> = ({ sessionId }) => {
  const { user } = useAuth();
  const {
    sessions,
    currentSessionId,
    messages,
    sending,
    messagesEndRef,
    sendMessage,
    createNewSession,
    switchSession,
    removeSession,
    resendMessage,
    removeMessage,
  } = useChat({ sessionId, autoScroll: true });

  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  const [workflowExecution, setWorkflowExecution] = useState<any>(null);
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [showWorkflowSelector, setShowWorkflowSelector] = useState(false);
  const [executing, setExecuting] = useState(false);

  // 加载工作流列表
  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await listWorkflows();
      setWorkflows(response.workflows || []);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    }
  };

  // 处理消息发送
  const handleSend = async (content: string) => {
    if (!user) return;

    // 检查是否是工作流命令
    if (content.startsWith('/workflow ') || content.startsWith('/wf ')) {
      const workflowNameOrId = content.replace(/^\/workflow\s+|\/wf\s+/, '').trim();

      // 先发送用户消息
      sendMessage(content, user.user_id, user.username);

      // 查找工作流
      const workflow = workflows.find(
        (w) =>
          w.workflow_id === workflowNameOrId ||
          w.name === workflowNameOrId ||
          w.name.toLowerCase().includes(workflowNameOrId.toLowerCase())
      );

      if (workflow) {
        setCurrentWorkflowId(workflow.workflow_id);
        // 显示工作流输入对话框
        setShowWorkflowSelector(true);
      } else {
        // 工作流未找到，发送错误消息
        const availableWorkflows = workflows
          .slice(0, 5)
          .map((w) => `- ${w.name} (ID: ${w.workflow_id.substring(0, 8)}...)`)
          .join('\n');
        sendMessage(
          `❌ 未找到工作流: ${workflowNameOrId}\n\n可用工作流:\n${availableWorkflows || '暂无可用工作流'}`,
          'system',
          '系统'
        );
      }
    } else {
      // 普通消息
      sendMessage(content, user.user_id, user.username);
    }
  };

  // 执行工作流
  const handleExecuteWorkflow = async (workflowId: string, inputData: Record<string, any>) => {
    if (!user) return;

    setExecuting(true);
    setCurrentWorkflowId(workflowId);
    setShowWorkflowSelector(false);

    try {
      // 发送执行开始消息
      sendMessage('⏳ 正在执行工作流...', 'system', '系统');

      // 执行工作流
      const result = await executeWorkflowById(workflowId, inputData);

      setWorkflowExecution(result);

      // 发送执行结果消息
      const formatWorkflowResult = (result: any): string => {
        if (typeof result === 'string') return result;
        if (typeof result === 'object') return JSON.stringify(result, null, 2);
        return String(result);
      };

      const resultContent = result.success
        ? `✅ 工作流执行成功！\n\n${formatWorkflowResult(result.result)}`
        : `❌ 工作流执行失败: ${result.error || '未知错误'}`;

      sendMessage(resultContent, 'system', '系统');
    } catch (error: any) {
      console.error('Workflow execution failed:', error);
      sendMessage(`❌ 工作流执行失败: ${error?.message || '未知错误'}`, 'system', '系统');
    } finally {
      setExecuting(false);
    }
  };

  // 处理工作流步骤交互
  const handleStepAction = (stepId: string, action: string, data?: any) => {
    console.log('Step action:', stepId, action, data);
    // TODO: 实现步骤交互逻辑
  };

  return (
    <AuthGuard requireAuth>
      <div className="flex h-full bg-gray-50">
        {/* 左侧：对话界面 */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* 消息列表 */}
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="flex-1 overflow-y-auto">
              <MessageList
                messages={messages}
                currentUserId={user?.user_id || ''}
                onResend={resendMessage}
                onDelete={removeMessage}
              />
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* 消息输入 */}
          <MessageInput
            onSend={handleSend}
            disabled={sending || executing || !currentSessionId}
            placeholder={
              executing
                ? '工作流执行中...'
                : currentSessionId
                  ? '输入消息或 /workflow 工作流名称...'
                  : '请先创建或选择会话'
            }
            enableKnowledgeSearch={true}
          />
        </div>

        {/* 右侧：工作流进度 */}
        {currentWorkflowId && (
          <div className="w-80 border-l border-gray-200 bg-white flex flex-col">
            <WorkflowProgress
              workflowId={currentWorkflowId}
              execution={workflowExecution}
              executing={executing}
              onStepInteraction={handleStepAction}
              onClose={() => {
                setCurrentWorkflowId(null);
                setWorkflowExecution(null);
              }}
            />
          </div>
        )}

        {/* 工作流选择对话框 */}
        {showWorkflowSelector && currentWorkflowId && (
          <WorkflowInputDialog
            workflowId={currentWorkflowId}
            workflow={workflows.find((w) => w.workflow_id === currentWorkflowId)}
            onExecute={handleExecuteWorkflow}
            onCancel={() => {
              setShowWorkflowSelector(false);
              setCurrentWorkflowId(null);
            }}
          />
        )}
      </div>
    </AuthGuard>
  );
};

// 工作流输入对话框组件
interface WorkflowInputDialogProps {
  workflowId: string;
  workflow?: WorkflowListItem;
  onExecute: (workflowId: string, inputData: Record<string, any>) => void;
  onCancel: () => void;
}

const WorkflowInputDialog: React.FC<WorkflowInputDialogProps> = ({
  workflowId,
  workflow,
  onExecute,
  onCancel,
}) => {
  const [inputData, setInputData] = useState('{\n  "input": ""\n}');
  const [error, setError] = useState<string | null>(null);

  const handleExecute = () => {
    try {
      const parsed = JSON.parse(inputData);
      onExecute(workflowId, parsed);
    } catch (e) {
      setError('无效的 JSON 格式');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            执行工作流: {workflow?.name || workflowId}
          </h2>
          {workflow?.description && (
            <p className="text-sm text-gray-600 mt-1">{workflow.description}</p>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">输入参数 (JSON)</label>
            <textarea
              value={inputData}
              onChange={(e) => {
                setInputData(e.target.value);
                setError(null);
              }}
              rows={12}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              placeholder='{\n  "input": "您的输入内容"\n}'
            />
            {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
            <div className="mt-2 text-xs text-gray-500">
              <p>示例:</p>
              <pre className="bg-gray-50 p-2 rounded mt-1">
                {`{
  "input": "请帮我写一首关于春天的诗"
}`}
              </pre>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleExecute}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            执行
          </button>
        </div>
      </div>
    </div>
  );
};
