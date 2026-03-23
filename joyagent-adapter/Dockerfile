# JoyAgent Adapter Service Dockerfile
# Multi-stage build for optimized production image

# Build stage for JoyAgent-JDGenie using Debian Bookworm (与项目其他服务一致，避免拉取 Ubuntu)
FROM debian:bookworm-slim as joyagent-builder

# 设置非交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 使用国内镜像源（直接写入 sources.list，避免 sed 对 DEB822 格式无效）
RUN rm -f /etc/apt/sources.list.d/debian.sources 2>/dev/null; \
    echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm main contrib non-free non-free-firmware' > /etc/apt/sources.list && \
    echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware' >> /etc/apt/sources.list && \
    echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware' >> /etc/apt/sources.list

# 安装必要的系统依赖，使用步骤化安装避免冲突
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    gnupg \
    git \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 安装OpenJDK 17
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    maven \
    && rm -rf /var/lib/apt/lists/*

# 安装Node.js 18 from NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pnpm && \
    npm config set registry https://registry.npmmirror.com

# 设置工作目录
WORKDIR /app

# 复制JoyAgent-JDGenie源码
COPY joyagent-jdgenie/ ./joyagent-jdgenie/

# 构建JoyAgent-JDGenie组件
WORKDIR /app/joyagent-jdgenie

# 构建前端(UI)
WORKDIR /app/joyagent-jdgenie/ui
RUN pnpm install && \
    sed -i 's/import React, { useState, useEffect }/import React, { useState }/g' src/components/ActionView/FileList.tsx && \
    pnpm build

# 构建后端(Java)
WORKDIR /app/joyagent-jdgenie/genie-backend
RUN chmod +x build.sh start.sh && ./build.sh

# 准备Python客户端环境
WORKDIR /app/joyagent-jdgenie/genie-client
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple uv && \
    uv venv .venv && \
    . .venv/bin/activate && \
    export UV_DEFAULT_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple" && \
    uv sync

# 准备Python工具环境
WORKDIR /app/joyagent-jdgenie/genie-tool
RUN uv venv .venv && \
    . .venv/bin/activate && \
    export UV_DEFAULT_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple" && \
    uv sync && \
    mkdir -p /data/genie-tool && \
    cp .env_template .env && \
    python3 -m genie_tool.db.db_engine

# Production stage - 使用 Debian Bookworm 作为运行时基础镜像
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# 使用国内镜像源（直接写入 sources.list，避免 sed 对 DEB822 格式无效）
RUN rm -f /etc/apt/sources.list.d/debian.sources 2>/dev/null; \
    echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm main contrib non-free non-free-firmware' > /etc/apt/sources.list && \
    echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware' >> /etc/apt/sources.list && \
    echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware' >> /etc/apt/sources.list

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    openjdk-17-jre-headless \
    nodejs \
    npm \
    curl \
    netcat \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g pnpm

# 创建应用用户
RUN useradd --create-home --shell /bin/bash app

# 设置工作目录
WORKDIR /app

# 安装Python依赖管理工具
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple uv

# 复制requirements并安装适配器依赖
COPY joyagent-adapter/requirements.txt ./
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制已构建的JoyAgent-JDGenie组件
COPY --from=joyagent-builder /app/joyagent-jdgenie /app/joyagent-jdgenie

# 复制适配器服务源码
COPY joyagent-adapter/src/ ./src/

# 安装platform的shared_libs
COPY shared_libs/ ./shared_libs/
RUN . .venv/bin/activate && \
    uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -e ./shared_libs/

# 创建启动脚本
COPY joyagent-adapter/start_combined.sh ./
RUN chmod +x start_combined.sh

# 创建数据目录
RUN mkdir -p /data/joyagent-adapter /data/genie-tool && \
    chown -R app:app /app /data

# 切换到应用用户
USER app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8007/health && \
        curl -f http://localhost:8080/health && \
        curl -f http://localhost:3000/ || exit 1

# 暴露端口
# 8007: JoyAgent Adapter Service
# 8080: JoyAgent Backend (Java)
# 3000: JoyAgent Frontend (Node.js)
# 1601: JoyAgent Python Client
EXPOSE 8007 8080 3000 1601

# 启动组合服务
CMD ["./start_combined.sh"]