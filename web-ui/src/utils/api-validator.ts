/**
 * API端点验证工具
 * 用于检查后端API端点是否可用
 */

export interface EndpointValidationResult {
  endpoint: string;
  status: number | string;
  exists: boolean | 'unknown';
  message: string;
  responseTime?: number;
}

/**
 * 验证API端点是否可用
 */
export const validateApiEndpoints = async (
  baseUrl: string = ''
): Promise<EndpointValidationResult[]> => {
  const endpoints = [
    {
      path: '/api/workflows/advance',
      method: 'POST',
      body: {
        workflow_id: 'test',
        execution_id: 'test',
        next_node_id: 'test',
      },
    },
    {
      path: '/api/agent/continue',
      method: 'POST',
      body: {
        input: 'test',
        workflow_id: 'test',
        execution_id: 'test',
      },
    },
    {
      path: '/api/workflows/test/start',
      method: 'POST',
      body: {
        input: { content: 'test' },
      },
    },
    {
      path: '/api/health',
      method: 'GET',
      body: null,
    },
  ];

  const results: EndpointValidationResult[] = [];

  for (const endpoint of endpoints) {
    try {
      const startTime = Date.now();

      const response = await fetch(`${baseUrl}${endpoint.path}`, {
        method: endpoint.method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: endpoint.body ? JSON.stringify(endpoint.body) : undefined,
      });

      const responseTime = Date.now() - startTime;

      results.push({
        endpoint: endpoint.path,
        status: response.status,
        exists: response.status !== 404,
        message:
          response.status === 404
            ? '端点未找到 (404)'
            : response.status >= 500
              ? `服务器错误 (${response.status})`
              : response.status >= 400
                ? `客户端错误 (${response.status})，但端点存在`
                : '端点可用',
        responseTime,
      });
    } catch (error: any) {
      results.push({
        endpoint: endpoint.path,
        status: 'error',
        exists: false,
        message: `请求失败: ${error.message || '网络错误'}`,
      });
    }
  }

  // WebSocket端点测试（需要实际连接）
  results.push({
    endpoint: '/api/ws/workflows/{workflowId}',
    status: 'N/A',
    exists: 'unknown',
    message: '需要实际WebSocket连接测试',
  });

  return results;
};

/**
 * 在控制台输出验证结果
 */
export const logValidationResults = (results: EndpointValidationResult[]) => {
  console.group('API端点验证结果');

  results.forEach((result) => {
    const icon = result.exists === true ? '✅' : result.exists === false ? '❌' : '⚠️';
    console.log(`${icon} ${result.endpoint}`);
    console.log(`   状态: ${result.status}`);
    console.log(`   消息: ${result.message}`);
    if (result.responseTime) {
      console.log(`   响应时间: ${result.responseTime}ms`);
    }
  });

  const missingEndpoints = results.filter((r) => r.exists === false);
  if (missingEndpoints.length > 0) {
    console.warn(
      '缺失的端点:',
      missingEndpoints.map((e) => e.endpoint)
    );
  }

  console.groupEnd();
};

/**
 * 验证WebSocket连接
 */
export const validateWebSocketEndpoint = async (
  workflowId: string,
  baseUrl: string = ''
): Promise<{ success: boolean; message: string }> => {
  return new Promise((resolve) => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = baseUrl || window.location.host;
      const wsUrl = `${protocol}//${host}/api/ws/workflows/${workflowId}`;

      const ws = new WebSocket(wsUrl);
      const timeout = setTimeout(() => {
        ws.close();
        resolve({
          success: false,
          message: 'WebSocket连接超时',
        });
      }, 5000);

      ws.onopen = () => {
        clearTimeout(timeout);
        ws.close();
        resolve({
          success: true,
          message: 'WebSocket连接成功',
        });
      };

      ws.onerror = (error) => {
        clearTimeout(timeout);
        resolve({
          success: false,
          message: 'WebSocket连接失败',
        });
      };

      ws.onclose = (event) => {
        clearTimeout(timeout);
        if (event.code === 1006) {
          resolve({
            success: false,
            message: 'WebSocket端点不存在或无法连接',
          });
        }
      };
    } catch (error: any) {
      resolve({
        success: false,
        message: `WebSocket错误: ${error.message}`,
      });
    }
  });
};
