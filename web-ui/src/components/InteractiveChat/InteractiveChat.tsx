/**
 * 交互式聊天组件
 * 支持实时交互、执行控制、用户反馈
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  InteractiveMessage,
  UserAction,
  InteractionType,
  ExecutionStatus,
} from '@/types/interaction';

interface InteractiveChatProps {
  sessionId: string;
  onExecutionComplete?: (result: any) => void;
  apiGatewayUrl?: string;
}

export const InteractiveChat: React.FC<InteractiveChatProps> = ({
  sessionId,
  onExecutionComplete,
  apiGatewayUrl = 'http://localhost:8080',
}) => {
  const [messages, setMessages] = useState<InteractiveMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [currentExecutionId, setCurrentExecutionId] = useState<string | null>(null);
  const websocket = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    connectWebSocket();
    return () => {
      disconnectWebSocket();
    };
  }, [sessionId]);

  const connectWebSocket = useCallback(() => {
    try {
      // WebSocket通过API Gateway代理
      const wsUrl = `${apiGatewayUrl.replace('http', 'ws')}/api/v1/ws/${sessionId}`;
      console.log('Connecting to WebSocket:', wsUrl);

      websocket.current = new WebSocket(wsUrl);

      websocket.current.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0;
        console.log('WebSocket connected');
      };

      websocket.current.onmessage = (event) => {
        try {
          const message: InteractiveMessage = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      websocket.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');

        // 自动重连
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          setTimeout(() => {
            console.log(`Reconnecting... (attempt ${reconnectAttempts.current})`);
            connectWebSocket();
          }, 3000 * reconnectAttempts.current);
        }
      };

      websocket.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [sessionId, apiGatewayUrl]);

  const disconnectWebSocket = useCallback(() => {
    if (websocket.current) {
      websocket.current.close();
      websocket.current = null;
    }
  }, []);

  const handleWebSocketMessage = (message: InteractiveMessage) => {
    setMessages((prev) => [...prev, message]);

    switch (message.type) {
      case InteractionType.EXECUTION_START:
        setCurrentExecutionId(message.execution_id);
        break;
      case InteractionType.EXECUTION_COMPLETED:
        setCurrentExecutionId(null);
        if (onExecutionComplete) {
          onExecutionComplete(message.data);
        }
        break;
      case InteractionType.EXECUTION_CANCELLED:
      case InteractionType.EXECUTION_ERROR:
        setCurrentExecutionId(null);
        break;
      default:
        break;
    }
  };

  const sendAction = useCallback(
    (action: string, parameters: any = {}) => {
      if (!websocket.current || !currentExecutionId || !isConnected) {
        console.warn('Cannot send action: WebSocket not ready');
        return;
      }

      const userAction: UserAction = {
        action,
        execution_id: currentExecutionId,
        session_id: sessionId,
        parameters,
        timestamp: new Date().toISOString(),
      };

      try {
        websocket.current.send(JSON.stringify(userAction));
      } catch (error) {
        console.error('Failed to send action:', error);
      }
    },
    [currentExecutionId, sessionId, isConnected]
  );

  const handlePause = useCallback(() => {
    sendAction('pause_execution');
  }, [sendAction]);

  const handleResume = useCallback(() => {
    sendAction('resume_execution');
  }, [sendAction]);

  const handleCancel = useCallback(() => {
    sendAction('cancel_execution');
  }, [sendAction]);

  const handleConfirm = useCallback(
    (confirmed: boolean) => {
      sendAction('confirm_action', { confirmed });
    },
    [sendAction]
  );

  const handleUserInput = useCallback(
    (input: any) => {
      sendAction('provide_input', { input });
    },
    [sendAction]
  );

  return (
    <div className="interactive-chat">
      <div className="chat-status">
        <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 已连接' : '🔴 未连接'}
        </span>
      </div>

      <div className="chat-messages">
        {messages.map((message, index) => (
          <InteractiveMessageComponent
            key={`${message.execution_id}-${index}`}
            message={message}
            onConfirm={handleConfirm}
            onUserInput={handleUserInput}
          />
        ))}
      </div>

      <div className="chat-controls">
        {currentExecutionId && (
          <>
            <button onClick={handlePause} disabled={!isConnected} className="btn btn-pause">
              暂停
            </button>
            <button onClick={handleResume} disabled={!isConnected} className="btn btn-resume">
              继续
            </button>
            <button onClick={handleCancel} disabled={!isConnected} className="btn btn-cancel">
              取消
            </button>
          </>
        )}
      </div>
    </div>
  );
};

// 交互消息组件
const InteractiveMessageComponent: React.FC<{
  message: InteractiveMessage;
  onConfirm: (confirmed: boolean) => void;
  onUserInput: (input: any) => void;
}> = ({ message, onConfirm, onUserInput }) => {
  const [userInput, setUserInput] = useState('');

  const renderMessageContent = () => {
    switch (message.type) {
      case InteractionType.EXECUTION_START:
        return (
          <div className="message execution-start">
            <h4>🔄 开始执行任务</h4>
            <p>{message.data.user_input}</p>
          </div>
        );

      case InteractionType.EXECUTION_PROGRESS:
        return (
          <div className="message execution-progress">
            <div className="progress-header">
              <span>{message.data.message}</span>
              <span className="progress-text">
                步骤 {message.data.current_step}/{message.data.total_steps}
              </span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${(message.progress || 0) * 100}%` }}
              />
            </div>
            {message.progress !== undefined && (
              <span className="progress-percentage">{Math.round(message.progress * 100)}%</span>
            )}
          </div>
        );

      case InteractionType.EXECUTION_STEP:
        return (
          <div className="message execution-step">
            <h4>📋 {message.data.step_type}</h4>
            <p>{message.data.description}</p>
            {message.data.subtasks && (
              <ul>
                {message.data.subtasks.map((task: string, idx: number) => (
                  <li key={idx}>{task}</li>
                ))}
              </ul>
            )}
          </div>
        );

      case InteractionType.CONFIRMATION_REQUIRED:
        return (
          <div className="message confirmation-required">
            <h4>⚠️ 需要确认</h4>
            <p>
              <strong>{message.data.subtask}</strong>
            </p>
            <p>{message.data.description}</p>
            <div className="confirmation-actions">
              <button onClick={() => onConfirm(true)} className="btn btn-confirm">
                确认
              </button>
              <button onClick={() => onConfirm(false)} className="btn btn-cancel">
                取消
              </button>
            </div>
          </div>
        );

      case InteractionType.USER_INTERACTION_REQUIRED:
        return (
          <div className="message user-input-required">
            <h4>📝 需要输入</h4>
            <p>
              <strong>{message.data.subtask}</strong>
            </p>
            <p>{message.data.input_description}</p>
            {message.data.required_parameters && (
              <ul>
                {message.data.required_parameters.map((param: string, idx: number) => (
                  <li key={idx}>{param}</li>
                ))}
              </ul>
            )}
            <div className="input-section">
              <input
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="请输入..."
                className="input-field"
              />
              <button onClick={() => onUserInput({ input: userInput })} className="btn btn-submit">
                提交
              </button>
            </div>
          </div>
        );

      case InteractionType.EXECUTION_COMPLETED:
        return (
          <div className="message execution-completed">
            <h4>✅ 任务完成</h4>
            <pre className="result-preview">{JSON.stringify(message.data, null, 2)}</pre>
          </div>
        );

      case InteractionType.EXECUTION_ERROR:
        return (
          <div className="message execution-error">
            <h4>❌ 执行错误</h4>
            <p>{message.data.error}</p>
          </div>
        );

      case InteractionType.EXECUTION_PAUSED:
        return (
          <div className="message execution-paused">
            <h4>⏸️ 执行已暂停</h4>
          </div>
        );

      case InteractionType.EXECUTION_RESUMED:
        return (
          <div className="message execution-resumed">
            <h4>▶️ 执行已继续</h4>
          </div>
        );

      case InteractionType.EXECUTION_CANCELLED:
        return (
          <div className="message execution-cancelled">
            <h4>🚫 执行已取消</h4>
          </div>
        );

      default:
        return (
          <div className="message default">
            <pre>{JSON.stringify(message, null, 2)}</pre>
          </div>
        );
    }
  };

  return <div className={`interactive-message ${message.type}`}>{renderMessageContent()}</div>;
};

export default InteractiveChat;
