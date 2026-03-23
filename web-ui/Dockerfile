# 生产环境Dockerfile - 多阶段构建，优化镜像大小
ARG NODE_VERSION=20

# ============================================
# 阶段1: 依赖安装
# ============================================
FROM node:${NODE_VERSION}-alpine AS deps

WORKDIR /app

# 安装系统依赖
RUN apk add --no-cache libc6-compat

# 复制包文件
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm ci

# ============================================
# 阶段2: 构建应用
# ============================================
FROM node:${NODE_VERSION}-alpine AS builder

WORKDIR /app

# 从deps复制node_modules
COPY --from=deps /app/node_modules ./node_modules

# 复制源代码
COPY . .

# 设置环境变量
ENV NEXT_TELEMETRY_DISABLED=1

# 构建应用
RUN npm run build

# ============================================
# 阶段3: 运行时镜像
# ============================================
FROM node:${NODE_VERSION}-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# 创建非root用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制必要文件
COPY --from=builder /app/public ./public

# 复制standalone构建（如果启用）
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 切换到非root用户
USER nextjs

# 暴露端口
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

# 启动应用
CMD ["node", "server.js"]

