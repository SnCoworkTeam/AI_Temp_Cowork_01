/**
 * 动态工作流API客户端
 */
const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';

export interface DynamicWorkflowRequest {
  user_input: string;
  context?: Record<string, any>;
  stream?: boolean;
}

export interface WorkflowChunk {
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
  total_layers?: number;
  total_agents?: number; // 添加total_agents字段
  final_result?: any;
  error?: string;
  error_type?: string; // 添加error_type字段
}

/**
 * 执行动态工作流（流式）
 */
export async function* executeDynamicWorkflow(
  request: DynamicWorkflowRequest
): AsyncGenerator<WorkflowChunk, void, unknown> {
  const url = `${API_GATEWAY_URL}/api/v1/dynamic-workflow/execute`;

  try {
    // 添加超时控制（增加到120秒，因为动态工作流可能需要更长时间）
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 120秒超时

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream', // 明确指定接受 SSE 格式
        },
        body: JSON.stringify({
          user_input: request.user_input,
          context: request.context || {},
          stream: true,
        }),
        signal: controller.signal,
        // 禁用自动处理，手动处理流式响应
        cache: 'no-cache',
        keepalive: false,
      });
    } catch (fetchError: any) {
      clearTimeout(timeoutId);

      // 处理网络错误
      if (fetchError.name === 'AbortError') {
        throw new Error('请求超时：服务器响应时间过长，请稍后重试');
      } else if (
        fetchError.message?.includes('Failed to fetch') ||
        fetchError.message?.includes('NetworkError') ||
        fetchError.message?.includes('connection') ||
        fetchError.message?.includes('ERR_INCOMPLETE_CHUNKED_ENCODING')
      ) {
        throw new Error(
          `无法连接到服务器：${API_GATEWAY_URL}。请检查：\n1. 后端服务是否正在运行\n2. API Gateway URL 是否正确\n3. 网络连接是否正常`
        );
      } else {
        throw new Error(`网络请求失败：${fetchError.message || '未知错误'}`);
      }
    }

    clearTimeout(timeoutId);

    console.log('[DynamicWorkflow] Response received:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok,
      headers: Object.fromEntries(response.headers.entries()),
      hasBody: !!response.body,
    });

    if (!response.ok) {
      let errorMessage = `HTTP错误 ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorData.error || errorMessage;
      } catch {
        // 忽略JSON解析错误
      }
      throw new Error(errorMessage);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      console.error('[DynamicWorkflow] Response body is not readable');
      throw new Error('Response body is not readable');
    }

    console.log('[DynamicWorkflow] Stream reader obtained, starting to read...');

    let buffer = '';
    let hasReceivedExecutionComplete = false; // 跟踪是否已收到执行完成信号
    let chunkCount = 0; // 跟踪接收的chunk数量
    const receivedChunks: WorkflowChunk[] = []; // 跟踪已接收的chunk，用于错误处理

    console.log('[DynamicWorkflow] Starting to read stream...');

    try {
      while (true) {
        const { done, value } = await reader.read();

        console.log(
          `[DynamicWorkflow] Stream read: done=${done}, hasValue=${!!value}, valueLength=${value?.length || 0}`
        );

        if (done) {
          console.log('[DynamicWorkflow] Stream reading done, total chunks received:', chunkCount);
          break;
        }

        if (!value || value.length === 0) {
          console.warn('[DynamicWorkflow] Received empty chunk, continuing...');
          continue;
        }

        chunkCount++;
        console.log(
          `[DynamicWorkflow] Processing chunk ${chunkCount}, buffer length: ${buffer.length}, new data length: ${value.length}`
        );

        buffer += decoder.decode(value, { stream: true });

        // SSE格式：每行以\n结尾，每个事件以\n\n分隔
        // 格式: data: {...}\n\n
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留最后一个不完整的行

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue; // 跳过空行

          if (trimmedLine.startsWith('data: ')) {
            try {
              const jsonStr = trimmedLine.slice(6); // 移除 "data: " 前缀
              if (jsonStr) {
                console.log(
                  `[DynamicWorkflow] Parsing SSE data line, length: ${jsonStr.length}, preview: ${jsonStr.substring(0, 100)}`
                );
                const data = JSON.parse(jsonStr) as WorkflowChunk;
                console.log(
                  `[DynamicWorkflow] Parsed chunk type: ${data.type}, stage: ${data.stage || 'none'}`
                );

                // 检查是否收到执行完成信号
                if (
                  (data.type === 'execution' && data.stage === 'execution_complete') ||
                  data.type === 'execution_complete'
                ) {
                  hasReceivedExecutionComplete = true;
                }

                // 改进日志记录，包含更多错误信息
                if (data.type === 'error') {
                  console.error('[DynamicWorkflow] Error chunk parsed:', {
                    type: data.type,
                    stage: data.stage,
                    message: data.message,
                    error: data.error,
                  });

                  // 检查是否是网络错误
                  const errorMsg =
                    (data.message && data.message.trim()) ||
                    (data.error && data.error.trim()) ||
                    data.error_type ||
                    '';
                  const isNetworkError =
                    /network error|ERR_INCOMPLETE_CHUNKED_ENCODING|连接中断|连接失败/i.test(
                      errorMsg
                    );

                  // 检查是否已经收到有效数据（非错误类型）
                  // 注意：在push之前检查，因为这是当前chunk
                  const hasValidData = receivedChunks.some(
                    (c) => c.type === 'execution' || c.type === 'design' || c.type === 'thinking'
                  );

                  // 如果是网络错误，且没有其他有效数据，不yield（静默忽略）
                  // 因为可能是连接提前关闭，但服务器已经处理了请求（响应状态可能是200）
                  if (isNetworkError && !hasValidData) {
                    console.warn(
                      '[DynamicWorkflow] Network error chunk received without valid data, likely connection close, ignoring (not yielding):',
                      errorMsg,
                      `(received ${receivedChunks.length} chunks before this, all errors)`
                    );
                    // 不push，不yield，继续处理下一个chunk
                    continue;
                  }

                  // 如果是网络错误但已有有效数据，记录但继续yield（让前端处理）
                  if (isNetworkError && hasValidData) {
                    console.warn(
                      '[DynamicWorkflow] Network error chunk received but has valid data, will yield for frontend handling:',
                      errorMsg
                    );
                  }
                } else {
                  console.log('[DynamicWorkflow] Parsed chunk:', data.type, data.stage);
                }

                // 记录已接收的chunk（在决定yield之后）
                receivedChunks.push(data);
                yield data;
              }
            } catch (e) {
              console.error(
                '[DynamicWorkflow] Failed to parse chunk:',
                e,
                trimmedLine.substring(0, 100)
              );
            }
          }
        }
      }

      // 处理剩余的buffer
      const trimmedBuffer = buffer.trim();
      if (trimmedBuffer && trimmedBuffer.startsWith('data: ')) {
        try {
          const jsonStr = trimmedBuffer.slice(6);
          if (jsonStr) {
            const data = JSON.parse(jsonStr) as WorkflowChunk;

            // 检查是否收到执行完成信号
            if (
              (data.type === 'execution' && data.stage === 'execution_complete') ||
              data.type === 'execution_complete'
            ) {
              hasReceivedExecutionComplete = true;
            }

            // 记录已接收的chunk
            receivedChunks.push(data);

            // 如果是错误chunk，检查是否是网络错误
            if (data.type === 'error') {
              const errorMsg =
                (data.message && data.message.trim()) ||
                (data.error && data.error.trim()) ||
                data.error_type ||
                '';
              const isNetworkError =
                /network error|ERR_INCOMPLETE_CHUNKED_ENCODING|连接中断|连接失败/i.test(errorMsg);

              // 检查是否已经收到有效数据（非错误类型）
              const hasValidData = receivedChunks.some(
                (c) => c.type === 'execution' || c.type === 'design' || c.type === 'thinking'
              );

              // 如果是网络错误，且没有其他有效数据，不yield（静默忽略）
              if (isNetworkError && !hasValidData) {
                console.warn(
                  '[DynamicWorkflow] Network error chunk received in final buffer without valid data, likely connection close, ignoring:',
                  errorMsg,
                  `(received ${receivedChunks.length} chunks, all errors)`
                );
                // 不yield，直接返回
                return;
              }
            }

            console.log('[DynamicWorkflow] Parsed final chunk:', data.type);
            yield data;
          }
        } catch (e) {
          console.error(
            '[DynamicWorkflow] Failed to parse final chunk:',
            e,
            trimmedBuffer.substring(0, 100)
          );
        }
      }
    } catch (streamError: any) {
      // 处理流读取过程中的错误（如网络中断）
      const errorMessage = streamError?.message || String(streamError);
      const isNetworkError =
        errorMessage.includes('network error') ||
        errorMessage.includes('ERR_INCOMPLETE_CHUNKED_ENCODING') ||
        errorMessage.includes('incomplete') ||
        errorMessage.includes('connection') ||
        errorMessage.includes('aborted') ||
        errorMessage.includes('chunked') ||
        streamError?.name === 'AbortError' ||
        streamError?.name === 'TypeError';

      // 检查是否收到了有效的执行数据（非错误类型）
      const hasValidExecutionChunks = receivedChunks.some(
        (c: WorkflowChunk) => c.type === 'execution' || c.type === 'design' || c.type === 'thinking'
      );

      // 检查是否只收到了错误 chunk（没有其他有效数据）
      const onlyErrorChunks =
        receivedChunks.length > 0 && receivedChunks.every((c: WorkflowChunk) => c.type === 'error');

      // 如果响应状态是200，且已经收到有效数据，即使连接中断也视为可能正常完成
      if (response && response.ok && response.status === 200) {
        // 如果流在开始读取之前就中断了（chunkCount === 0），视为正常完成
        // 因为200状态码表示服务器已经处理了请求，只是连接提前关闭
        if (chunkCount === 0 && isNetworkError) {
          console.warn(
            '[DynamicWorkflow] Stream interrupted before any data received (status 200), likely connection close, treating as normal completion:',
            errorMessage
          );
          return; // 正常结束，不抛出错误，不yield错误chunk
        }

        // 如果已经收到执行完成的信号，且是网络错误，只记录警告，不yield错误chunk
        if (hasReceivedExecutionComplete && isNetworkError) {
          console.warn(
            '[DynamicWorkflow] Network error after execution completed (status 200), treating as normal completion:',
            errorMessage
          );
          return; // 正常结束，不抛出错误
        }

        // 如果已经收到有效的执行数据，且是网络错误，视为正常完成
        if (hasValidExecutionChunks && isNetworkError) {
          console.warn(
            `[DynamicWorkflow] Stream interrupted after receiving ${chunkCount} chunks with valid execution data (status 200), treating as normal completion:`,
            errorMessage
          );
          return; // 正常结束，不抛出错误
        }

        // 如果响应是200 OK，即使只收到网络错误chunk，也视为正常完成（可能是连接提前关闭）
        // 因为200状态码表示服务器已经处理了请求
        if (onlyErrorChunks && isNetworkError) {
          console.warn(
            '[DynamicWorkflow] Only network error chunk received with 200 OK status (likely connection close), treating as normal completion:',
            errorMessage
          );
          return; // 正常结束，不抛出错误，不yield错误chunk
        }
      }

      // 如果已经收到执行完成的信号，且是网络错误，只记录警告，不yield错误chunk
      if (hasReceivedExecutionComplete && isNetworkError) {
        console.warn(
          '[DynamicWorkflow] Network error after execution completed, ignoring:',
          errorMessage
        );
        return; // 正常结束，不抛出错误
      }

      // 如果已经收到有效的执行数据，且是网络错误，视为正常完成
      if (hasValidExecutionChunks && isNetworkError) {
        console.warn(
          `[DynamicWorkflow] Stream interrupted after receiving ${chunkCount} chunks with valid execution data, treating as normal completion:`,
          errorMessage
        );
        return; // 正常结束，不抛出错误
      }

      // 如果流在开始读取之前就中断了（chunkCount === 0），且是网络错误，静默忽略
      // 这通常意味着连接在服务器发送数据之前就关闭了，但服务器可能已经处理了请求
      if (chunkCount === 0 && isNetworkError) {
        console.warn(
          '[DynamicWorkflow] Stream interrupted before any data received, likely connection issue, ignoring:',
          errorMessage
        );
        return; // 静默忽略，不抛出错误，不yield错误chunk
      }

      // 如果只收到了错误 chunk，且没有其他有效数据
      // 但如果是网络错误，且没有收到任何有效数据，可能是连接问题，静默忽略
      if (onlyErrorChunks && isNetworkError) {
        console.warn(
          '[DynamicWorkflow] Only network error chunk received (no valid data), likely connection issue, ignoring:',
          errorMessage
        );
        return; // 静默忽略，不抛出错误，不yield错误chunk
      }

      // 如果只收到了非网络错误chunk，需要抛出错误
      if (onlyErrorChunks && !isNetworkError) {
        console.error(
          '[DynamicWorkflow] Only non-network error chunks received, no valid execution data:',
          errorMessage
        );
        throw streamError; // 抛出错误，让外层处理
      }

      // 如果流被中断但已经接收了足够多的chunk，可能是正常完成但连接提前关闭
      // 降低阈值，允许在收到5个chunk后正常完成（更宽容）
      if (isNetworkError && chunkCount >= 5 && hasValidExecutionChunks) {
        console.warn(
          `[DynamicWorkflow] Stream interrupted after receiving ${chunkCount} chunks with valid data, may be normal completion:`,
          errorMessage
        );
        return; // 正常结束，不抛出错误
      }

      // 否则，抛出错误让外层catch处理
      throw streamError;
    }
  } catch (error) {
    console.error('Dynamic workflow execution failed:', error);

    // 检查错误类型，提供更友好的错误消息
    const errorMessage = error instanceof Error ? error.message : String(error);
    const isNetworkError =
      errorMessage.includes('network error') ||
      errorMessage.includes('ERR_INCOMPLETE_CHUNKED_ENCODING') ||
      errorMessage.includes('Failed to fetch') ||
      errorMessage.includes('connection') ||
      errorMessage.includes('aborted');

    // 如果是网络错误，且响应可能是200 OK（从错误信息中无法直接判断，但通常ERR_INCOMPLETE_CHUNKED_ENCODING表示200响应）
    // 静默忽略，不yield错误chunk
    if (isNetworkError && errorMessage.includes('ERR_INCOMPLETE_CHUNKED_ENCODING')) {
      console.warn(
        '[DynamicWorkflow] Network error (ERR_INCOMPLETE_CHUNKED_ENCODING) caught in outer catch, likely 200 OK response with connection close, ignoring:',
        errorMessage
      );
      // 不yield错误chunk，直接返回
      return;
    }

    // 只有在真正的执行错误时才yield错误chunk
    yield {
      type: 'error',
      message: isNetworkError ? `网络连接中断: ${errorMessage}` : `执行失败: ${errorMessage}`,
      error: String(error),
      error_type: isNetworkError ? 'network_error' : 'execution_error',
    };
  }
}

/**
 * 仅设计工作流（不执行）
 */
export async function designWorkflow(
  request: DynamicWorkflowRequest
): Promise<{ success: boolean; design: any }> {
  const url = `${API_GATEWAY_URL}/api/v1/dynamic-workflow/design`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_input: request.user_input,
      context: request.context || {},
      stream: false,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}
