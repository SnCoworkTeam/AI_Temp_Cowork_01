/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // 启用standalone输出用于Docker
  // 修复 Server Actions 的 origin 头问题并优化开发模式
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
      allowedOrigins: [
        'localhost:3000',
        '43.143.139.197:3000',
        'http://localhost:3000',
        'http://43.143.139.197:3000',
      ],
    },
    // 优化开发模式下的性能
    optimizeCss: false, // 开发模式下禁用 CSS 优化以加快编译
  },
  env: {
    // 优先使用环境变量，如果没有则使用本地地址（开发环境）
    NEXT_PUBLIC_MCP_GATEWAY_URL: process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://127.0.0.1:8001',
    NEXT_PUBLIC_WORKFLOW_ENGINE_URL: process.env.NEXT_PUBLIC_WORKFLOW_ENGINE_URL || 'http://127.0.0.1:8002',
    NEXT_PUBLIC_AUTH_SERVICE_URL: process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://127.0.0.1:8003',
    NEXT_PUBLIC_KNOWLEDGE_BASE_URL: process.env.NEXT_PUBLIC_KNOWLEDGE_BASE_URL || 'http://127.0.0.1:8004',
    NEXT_PUBLIC_METADATA_SERVICE_URL: process.env.NEXT_PUBLIC_METADATA_SERVICE_URL || 'http://127.0.0.1:8005',
    NEXT_PUBLIC_AGENT_SERVICE_URL: process.env.NEXT_PUBLIC_AGENT_SERVICE_URL || 'http://127.0.0.1:8010',
    NEXT_PUBLIC_AGENT_ORCHESTRATOR_URL: process.env.NEXT_PUBLIC_AGENT_ORCHESTRATOR_URL || 'http://127.0.0.1:8011',
  },
  // 优化静态资源处理
  onDemandEntries: {
    // 页面在内存中保持活动的时间（毫秒）
    maxInactiveAge: 25 * 1000,
    // 同时保持活动的页面数
    pagesBufferLength: 2,
  },
  async rewrites() {
    const opencodeProxy = '/opencode-proxy';
    return [
      { source: '/', has: [{ type: 'query', key: 'opencode', value: '1' }], destination: `${opencodeProxy}` },
      { source: '/:dir([A-Za-z0-9_-]{10,})', destination: `${opencodeProxy}/:dir` },
      { source: '/:dir([A-Za-z0-9_-]{10,})/', destination: `${opencodeProxy}/:dir` },
      { source: '/:dir([A-Za-z0-9_-]{10,})/session/:id', destination: `${opencodeProxy}/:dir/session/:id` },
      { source: '/:dir([A-Za-z0-9_-]{10,})/session', destination: `${opencodeProxy}/:dir/session` },
      { source: '/assets/:path*', destination: `${opencodeProxy}/assets/:path*` },
      { source: '/site.webmanifest', destination: `${opencodeProxy}/site.webmanifest` },
      { source: '/global/:path*', destination: `${opencodeProxy}/global/:path*` },
      { source: '/provider/:path*', destination: `${opencodeProxy}/provider/:path*` },
      { source: '/agent/:path*', destination: `${opencodeProxy}/agent/:path*` },
      { source: '/config', destination: `${opencodeProxy}/config` },
      { source: '/project/:path*', destination: `${opencodeProxy}/project/:path*` },
      { source: '/file', destination: `${opencodeProxy}/file` },
      { source: '/find/:path*', destination: `${opencodeProxy}/find/:path*` },
      { source: '/pty/:path*', destination: `${opencodeProxy}/pty/:path*` },
      { source: '/session/:path*', destination: `${opencodeProxy}/session/:path*` },
      { source: '/experimental/:path*', destination: `${opencodeProxy}/experimental/:path*` },
    ];
  },
  // 开发模式配置
  devIndicators: {
    buildActivity: false, // 禁用构建活动指示器以减少日志
  },
  webpack: (config, { isServer }) => {
    // 排除不需要的VR相关依赖
    if (!isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        'aframe': false,
        'aframe-extras': false,
        '3d-force-graph-vr': false,
        '3d-force-graph-ar': false,
      };
      
      // 使用externals来排除这些模块
      config.externals = config.externals || [];
      if (typeof config.externals === 'function') {
        const originalExternals = config.externals;
        config.externals = [
          originalExternals,
          ({ request }, callback) => {
            if (/^(aframe|aframe-extras|3d-force-graph-vr|3d-force-graph-ar)/.test(request)) {
              return callback(null, `commonjs ${request}`);
            }
            callback();
          }
        ];
      }
    }
    
    return config;
  },
}

module.exports = nextConfig
