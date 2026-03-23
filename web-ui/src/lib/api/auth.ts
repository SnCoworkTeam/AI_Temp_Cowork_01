/**
 * 认证API客户端
 */
// 优先使用 API Gateway，如果没有则使用直接地址
const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || '';
const AUTH_SERVICE_URL = process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://127.0.0.1:8003';

const trimTrailingSlash = (url: string) => url.replace(/\/+$/, '');
const isLoopbackUrl = (url: string) => /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?/i.test(url);

const isBrowser = typeof window !== 'undefined';

const safeGetHost = (url: string) => {
  try {
    return new URL(url).host;
  } catch {
    return '';
  }
};

const shouldUseProxy = () => {
  if (!isBrowser) return false;
  // 为了避免浏览器本地代理/防火墙对 localhost:8080 等端口的干扰，
  // 登录、刷新等认证请求统一通过 Next.js 的 /api/auth 代理转发到网关/认证服务。
  // 这样由服务端发起到网关的请求，行为与 curl / 服务器内部访问保持一致，更稳定。
  return true;
};

const resolveAuthBaseUrl = () => {
  if (shouldUseProxy()) return '/api/auth';
  const gateway = trimTrailingSlash(API_GATEWAY_URL);
  if (gateway) return `${gateway}/api/auth`;
  return trimTrailingSlash(AUTH_SERVICE_URL);
};

const buildAuthUrl = (path: string) => {
  const baseUrl = trimTrailingSlash(resolveAuthBaseUrl());
  const cleanPath = path.replace(/^\/+/, '');
  if (baseUrl.includes('/api/auth') || baseUrl.endsWith('/auth')) {
    return `${baseUrl}/${cleanPath}`;
  }
  return `${baseUrl}/auth/${cleanPath}`;
};

const resolveUsersMeUrl = () => {
  if (shouldUseProxy()) return '/api/users/me';
  const gateway = trimTrailingSlash(API_GATEWAY_URL);
  if (gateway) return `${gateway}/api/users/me`;

  const authBase = trimTrailingSlash(AUTH_SERVICE_URL);
  if (authBase.includes('/api/auth')) {
    const gatewayBase = authBase.replace(/\/api\/auth\/?$/, '');
    return `${gatewayBase}/api/users/me`;
  }
  if (authBase.endsWith('/auth')) {
    const authRoot = authBase.replace(/\/auth\/?$/, '');
    return `${authRoot}/users/me`;
  }
  return `${authBase}/users/me`;
};

// 调试：输出实际使用的 URL
if (typeof window !== 'undefined') {
  console.log('API Gateway URL:', API_GATEWAY_URL || 'not set');
  console.log('Auth Service URL:', AUTH_SERVICE_URL);
  console.log('Auth Base URL (resolved):', resolveAuthBaseUrl());
}

export interface User {
  user_id: string;
  id?: string; // 添加id字段（作为user_id的别名）
  username: string;
  email: string;
  roles: string[];
  session_id?: string;
  display_name?: string;
  permissions?: string[];
  created_at?: string;
  last_login_at?: string; // 添加最后登录时间
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  session_id: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface RegisterResponse {
  user_id: string;
  username: string;
  email: string;
  message: string;
}

class AuthClient {

  /**
   * 用户注册
   */
  async register(request: RegisterRequest): Promise<RegisterResponse> {
    console.log('Register request body:', {
      username: request.username,
      email: request.email,
      password: '***',
      full_name: request.full_name,
    });

    const registerUrl = buildAuthUrl('register');
    const response = await fetch(registerUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: '注册失败' }));
      console.error('Register error response:', errorData);
      throw new Error(errorData.detail || errorData.message || '注册失败');
    }

    const result = await response.json();
    console.log('Register successful:', result);
    return result;
  }

  /**
   * 用户名密码登录
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    const requestBody = { username, password };
    const loginUrl = buildAuthUrl('login');
    console.log('Login request body:', { username, password: '***' });
    console.log('Login URL:', loginUrl);

    try {
      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('Login response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '登录失败' }));
        console.error('Login error response:', errorData);
        const errorMessage =
          errorData.detail || errorData.message || `登录失败 (${response.status})`;
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('Login successful:', result);
      return result;
    } catch (error: any) {
      console.error('Login fetch error:', error);
      if (error.message) {
        throw error;
      }
      throw new Error('网络错误，请检查连接');
    }
  }

  /**
   * 发起SSO登录
   */
  async initiateSSOLogin(): Promise<void> {
    const ssoUrl = buildAuthUrl('sso/login');
    window.location.href = ssoUrl;
  }

  /**
   * 刷新访问令牌
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const refreshUrl = buildAuthUrl('refresh');
    console.log('Refresh token URL:', refreshUrl);

    const response = await fetch(refreshUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      // 401 错误时，静默处理，不抛出错误（由调用方处理）
      if (response.status === 401) {
        const error: any = new Error('Token refresh failed: Unauthorized');
        error.statusCode = 401;
        throw error;
      }
      throw new Error('Failed to refresh token');
    }

    return response.json();
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(accessToken: string): Promise<User> {
    const userMeUrl = resolveUsersMeUrl();

    console.log('Getting current user from:', userMeUrl);

    try {
      const response = await fetch(userMeUrl, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 401 错误时，静默处理，不显示详细错误信息
        if (response.status === 401) {
          const error: any = new Error('Unauthorized');
          error.statusCode = 401;
          throw error;
        }
        const errorData = await response
          .json()
          .catch(() => ({ detail: 'Failed to get user info' }));
        const error: any = new Error(
          errorData.detail || errorData.message || 'Failed to get user info'
        );
        error.statusCode = response.status;
        throw error;
      }

      return response.json();
    } catch (error: any) {
      console.error('getCurrentUser error:', error);
      if (error.statusCode) {
        throw error;
      }
      // 网络错误或其他错误
      const networkError: any = new Error('网络错误，无法获取用户信息');
      networkError.statusCode = 0;
      throw networkError;
    }
  }

  /**
   * 登出
   */
  async logout(accessToken: string): Promise<void> {
    const logoutUrl = buildAuthUrl('logout');
    await fetch(logoutUrl, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }
}

export const authClient = new AuthClient();

