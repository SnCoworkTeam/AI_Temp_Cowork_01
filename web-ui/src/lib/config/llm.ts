/**
 * LLM配置管理
 * 统一管理LLM模型配置，从配置中心或环境变量读取
 */

// 配置中心API地址（优先使用API Gateway，如果没有则直接访问配置中心）
const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL;

const trimTrailingSlash = (url: string) => url.replace(/\/+$/, '');

const normalizeConfigCenterUrl = (rawUrl: string) => {
  const trimmed = trimTrailingSlash(rawUrl);
  if (trimmed.endsWith('/api/config')) return trimmed;
  if (trimmed.endsWith('/api')) return `${trimmed}/config`;
  if (trimmed.endsWith('/config')) return trimmed;
  return `${trimmed}/api/config`;
};

const getConfigCenterBaseUrl = () => {
  const directFallback =
    process.env.NEXT_PUBLIC_CONFIG_CENTER_URL || 'http://localhost:8090';

  if (!API_GATEWAY_URL) {
    return normalizeConfigCenterUrl(directFallback);
  }

  // 浏览器端：当网关与当前域名不同，使用本地 /api 代理避免跨域问题
  if (typeof window !== 'undefined') {
    const isLocalBrowser =
      window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

    if (!isLocalBrowser) {
      try {
        const gatewayHost = new URL(API_GATEWAY_URL).host;
        if (gatewayHost && gatewayHost !== window.location.host) {
          return '/api/config';
        }
      } catch {
        // ignore invalid URL, fallback to direct
      }
    }
  }

  return normalizeConfigCenterUrl(API_GATEWAY_URL);
};

// 从环境变量读取默认模型（作为fallback）
const DEFAULT_LLM_MODEL_FALLBACK = process.env.NEXT_PUBLIC_LLM_MODEL || 'deepseek-chat';

// 默认可用模型列表（作为fallback）
const DEFAULT_AVAILABLE_MODELS = [
  {
    value: 'deepseek-chat',
    label: 'DeepSeek Chat',
    provider: 'DeepSeek',
  },
  {
    value: 'gpt-4',
    label: 'GPT-4',
    provider: 'OpenAI',
  },
  {
    value: 'gpt-3.5-turbo',
    label: 'GPT-3.5 Turbo',
    provider: 'OpenAI',
  },
  {
    value: 'gpt-4-turbo',
    label: 'GPT-4 Turbo',
    provider: 'OpenAI',
  },
  {
    value: 'claude-3-opus',
    label: 'Claude 3 Opus',
    provider: 'Anthropic',
  },
  {
    value: 'claude-3-sonnet',
    label: 'Claude 3 Sonnet',
    provider: 'Anthropic',
  },
];

// 默认LLM节点配置（作为fallback）
const DEFAULT_LLM_CONFIG_FALLBACK = {
  model: DEFAULT_LLM_MODEL_FALLBACK,
  temperature: 0.7,
  prompt_template: '{input}',
};

// 缓存配置（避免重复请求）
let cachedModels: typeof DEFAULT_AVAILABLE_MODELS | null = null;
let cachedDefaultConfig: typeof DEFAULT_LLM_CONFIG_FALLBACK | null = null;

/**
 * 从配置中心获取可用模型列表
 */
export async function fetchAvailableLLMModels(): Promise<typeof DEFAULT_AVAILABLE_MODELS> {
  if (cachedModels) {
    return cachedModels || DEFAULT_AVAILABLE_MODELS;
  }

  try {
    const response = await fetch(`${getConfigCenterBaseUrl()}/llm/models`);
    if (response.ok) {
      const data = await response.json();
      cachedModels = data.models || DEFAULT_AVAILABLE_MODELS;
      return cachedModels || DEFAULT_AVAILABLE_MODELS;
    }
  } catch (error) {
    console.warn('Failed to fetch LLM models from config center:', error);
  }

  return DEFAULT_AVAILABLE_MODELS;
}

/**
 * 从配置中心获取默认配置
 */
export async function fetchLLMDefaultConfig(): Promise<typeof DEFAULT_LLM_CONFIG_FALLBACK> {
  if (cachedDefaultConfig) {
    return cachedDefaultConfig || DEFAULT_LLM_CONFIG_FALLBACK;
  }

  try {
    const response = await fetch(`${getConfigCenterBaseUrl()}/llm/default`);
    if (response.ok) {
      const data = await response.json();
      cachedDefaultConfig = {
        model: data.default_model || DEFAULT_LLM_MODEL_FALLBACK,
        ...data.default_config,
      };
      return cachedDefaultConfig || DEFAULT_LLM_CONFIG_FALLBACK;
    }
  } catch (error) {
    console.warn('Failed to fetch LLM default config from config center:', error);
  }

  return DEFAULT_LLM_CONFIG_FALLBACK;
}

/**
 * 获取默认模型（同步，使用fallback）
 */
export function getDefaultLLMModel(): string {
  return (
    cachedDefaultConfig?.model || DEFAULT_LLM_CONFIG_FALLBACK?.model || DEFAULT_LLM_MODEL_FALLBACK
  );
}

/**
 * 获取可用模型列表（同步，使用fallback）
 */
export function getAvailableLLMModels() {
  return cachedModels || DEFAULT_AVAILABLE_MODELS || DEFAULT_AVAILABLE_MODELS;
}

/**
 * 清除缓存（配置更新后调用）
 */
export function clearLLMConfigCache() {
  cachedModels = null;
  cachedDefaultConfig = null;
}

/**
 * 根据base_url智能选择默认模型
 */
export function getDefaultModelByBaseUrl(baseUrl?: string): string {
  if (baseUrl && baseUrl.includes('deepseek')) {
    return 'deepseek-chat';
  }
  return getDefaultLLMModel();
}
