'use client';

import { Message } from '@/types/chat';
import { formatTime, copyToClipboard } from '@/lib/chat';
import { WorkflowStatus } from './WorkflowStatus';
import { WorkflowMessage } from './WorkflowMessage';
import { ToolExecution } from './ToolExecution';
import { KnowledgeCitations, SourceDocuments } from './ChatInterface/index';
import { MessageContent } from './MessageContent';
import { DynamicWorkflowDisplay } from './DynamicWorkflowDisplay';
import { useState, memo } from 'react';

interface MessageListProps {
  messages: Message[];
  currentUserId: string;
  onResend?: (messageId: string) => void;
  onDelete?: (messageId: string) => void;
  workflowExecutions?: Map<string, any>;
  workflowChunks?: Map<string, any[]>;
  showThinkingContent?: boolean; // 是否显示思考内容
}

export const MessageList = memo(function MessageList({
  messages,
  currentUserId,
  onResend,
  onDelete,
  workflowExecutions,
  workflowChunks,
  showThinkingContent = true,
}: MessageListProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = async (messageId: string, content: string) => {
    const success = await copyToClipboard(content);
    if (success) {
      setCopiedId(messageId);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const isOwnMessage = (message: Message) => message.senderId === currentUserId;

  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-4">💬</div>
          <p className="text-lg font-medium mb-2">还没有消息</p>
          <p className="text-sm">开始对话吧！</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 pb-6">
      {messages.map((message, index) => {
        const own = isOwnMessage(message);
        const showActions = own || message.type === 'error';
        const workflowMessageId = message.metadata?.workflowMessageId;
        const isDynamicWorkflow =
          message.metadata?.workflowType === 'dynamic' && Boolean(workflowMessageId);
        const dynamicChunks = isDynamicWorkflow
          ? workflowChunks?.get(workflowMessageId as string) || []
          : [];

        // 确保 key 唯一：使用 message.id + index 组合，避免重复 key
        // 即使有相同的 message.id，index 也会使其唯一
        const messageKey = `${message.id || 'msg'}-${index}`;

        // 检查是否是连续消息（同一发送者，时间间隔小于5分钟）
        const prevMessage = index > 0 ? messages[index - 1] : null;
        const isConsecutive =
          prevMessage &&
          prevMessage.senderId === message.senderId &&
          message.timestamp - prevMessage.timestamp < 5 * 60 * 1000;

        return (
          <div
            key={messageKey}
            className={`flex ${own ? 'justify-end' : 'justify-start'} group ${isConsecutive ? 'mt-2' : 'mt-4'}`}
          >
            <div className={`flex gap-2 max-w-[80%] ${own ? 'flex-row-reverse' : 'flex-row'}`}>
              {/* 头像 - 只在非连续消息时显示 */}
              {!own && !isConsecutive && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-sm">
                  <span className="text-white text-sm font-semibold">
                    {message.sender.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
              {!own && isConsecutive && <div className="w-8 h-8 flex-shrink-0" />}

              {/* 消息气泡 */}
              <div className={`flex flex-col ${own ? 'items-end' : 'items-start'}`}>
                {/* 发送者名称 - 只在非连续消息时显示 */}
                {!own && !isConsecutive && (
                  <div className="text-xs text-gray-500 mb-1 px-2 font-medium">
                    {message.sender}
                  </div>
                )}

                {/* 消息内容 */}
                <div
                  className={`rounded-lg px-4 py-3 shadow-sm transition-all duration-200 ${
                    message.type === 'error'
                      ? 'bg-red-50 border border-red-200 text-red-800'
                      : message.type === 'system'
                        ? 'bg-gray-100 text-gray-700'
                        : own
                          ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white'
                          : 'bg-white border border-gray-200 text-gray-900 hover:shadow-md'
                  }`}
                  style={{
                    maxWidth: '100%',
                    wordBreak: 'break-word',
                  }}
                >
                  {/* 工作流状态 */}
                  {message.type === 'workflow' && message.metadata?.workflowId && (
                    <div className="mt-2 -mx-2">
                      <WorkflowMessage
                        workflowId={message.metadata.workflowId}
                        execution={
                          message.metadata.execution ||
                          workflowExecutions?.get(message.metadata.workflowId)
                        }
                        executing={message.metadata.executing || false}
                      />
                    </div>
                  )}

                  {/* 工具执行状态 */}
                  {message.type === 'tool' && message.metadata?.executionId && (
                    <div className="mt-2">
                      <ToolExecution
                        executionId={message.metadata.executionId}
                        toolName={message.metadata.toolName || '工具'}
                      />
                    </div>
                  )}

                  {/* 对于动态工作流，按照顺序显示：思考内容 → 分析处理内容 → 最终结果 */}
                  {isDynamicWorkflow ? (
                    <div className="mt-2 -mx-2">
                      {dynamicChunks.length === 0 &&
                      (!message.content || message.content.trim().length === 0) ? (
                        <div className="text-xs text-gray-400">（回复加载中或缺失）</div>
                      ) : (
                        <DynamicWorkflowDisplay
                          chunks={dynamicChunks}
                          showThinkingContent={showThinkingContent}
                          fallbackContent={message.content || ''}
                          onComplete={(result) => {
                            if (process.env.NODE_ENV === 'development') {
                              console.log('Dynamic workflow completed:', result);
                            }
                          }}
                        />
                      )}
                    </div>
                  ) : (
                    message.content && (
                      <div>
                        <MessageContent content={message.content} isOwnMessage={own} />
                      </div>
                    )
                  )}

                  {/* 知识库引用 */}
                  {!own &&
                    message.metadata?.knowledgeCitations &&
                    message.metadata.knowledgeCitations.length > 0 && (
                      <KnowledgeCitations
                        citations={message.metadata.knowledgeCitations}
                        onViewSource={(documentId, chunkId) => {
                          console.log('View source:', documentId, chunkId);
                          // TODO: 实现查看源文档功能
                        }}
                      />
                    )}

                  {/* 参考文档 */}
                  {!own &&
                    message.metadata?.sourceDocuments &&
                    message.metadata.sourceDocuments.length > 0 && (
                      <div className="mt-3">
                        <SourceDocuments
                          documentIds={message.metadata.sourceDocuments}
                          onDocumentClick={(document) => {
                            console.log('View document:', document);
                            // TODO: 实现查看文档功能
                          }}
                        />
                      </div>
                    )}

                  {/* 消息状态 */}
                  {own && (
                    <div className="flex items-center gap-1 mt-1">
                      {message.status === 'sending' && (
                        <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      )}
                      {message.status === 'sent' && (
                        <svg
                          className="w-3 h-3 text-blue-200"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                        </svg>
                      )}
                      {message.status === 'failed' && (
                        <svg
                          className="w-3 h-3 text-red-300"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  )}
                </div>

                {/* 时间戳和操作 - 只在非连续消息或悬停时显示 */}
                <div
                  className={`flex items-center gap-2 mt-1 opacity-0 group-hover:opacity-100 transition-opacity ${own ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  <span className="text-xs text-gray-400">{formatTime(message.timestamp)}</span>

                  {/* 操作按钮 */}
                  {showActions && (
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                      {message.status === 'failed' && onResend && (
                        <button
                          onClick={() => onResend(message.id)}
                          className="p-1 text-gray-400 hover:text-blue-600 rounded"
                          title="重发"
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                            />
                          </svg>
                        </button>
                      )}
                      <button
                        onClick={() => handleCopy(message.id, message.content)}
                        className="p-1 text-gray-400 hover:text-blue-600 rounded"
                        title="复制"
                      >
                        {copiedId === message.id ? (
                          <svg
                            className="w-4 h-4 text-green-600"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        ) : (
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                            />
                          </svg>
                        )}
                      </button>
                      {onDelete && (
                        <button
                          onClick={() => onDelete(message.id)}
                          className="p-1 text-gray-400 hover:text-red-600 rounded"
                          title="删除"
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* 自己的头像 - 只在非连续消息时显示 */}
              {own && !isConsecutive && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center flex-shrink-0 shadow-sm">
                  <span className="text-white text-sm font-semibold">
                    {message.sender.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
              {own && isConsecutive && <div className="w-8 h-8 flex-shrink-0" />}
            </div>
          </div>
        );
      })}
    </div>
  );
});
