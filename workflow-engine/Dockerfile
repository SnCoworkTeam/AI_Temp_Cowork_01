# 生产环境Dockerfile - 多阶段构建，优化镜像大小
ARG PYTHON_VERSION=3.11

# ============================================
# 阶段1: 依赖安装
# ============================================
FROM python:${PYTHON_VERSION}-slim-bookworm as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 先安装shared_libs依赖
COPY shared_libs/requirements.txt ../shared_libs/requirements.txt
RUN pip install --user --no-cache-dir -i https://mirrors.cloud.tencent.com/pypi/simple -r ../shared_libs/requirements.txt

# 安装服务依赖
COPY requirements.txt .
RUN pip install --user --no-cache-dir -i https://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt

# ============================================
# 阶段2: 运行时镜像
# ============================================
FROM python:${PYTHON_VERSION}-slim-bookworm as runtime

WORKDIR /app

# 安装运行时依赖（仅curl用于健康检查）
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从builder复制Python包
COPY --from=builder /root/.local /root/.local

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/../shared_libs \
    PATH=/root/.local/bin:$PATH

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# 复制源代码
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser shared_libs/ ../shared_libs/

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8002

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8002/api/health || exit 1

# 启动应用
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "4"]
