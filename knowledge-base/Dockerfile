# 多阶段构建 - 生产环境
FROM python:3.11-slim-bookworm-bookworm as builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 先安装shared-libs依赖（如果存在）
COPY shared-libs/requirements.txt* /tmp/shared-libs-requirements.txt
RUN if [ -f /tmp/shared-libs-requirements.txt ]; then \
        pip install --no-cache-dir --upgrade pip -i https://mirrors.cloud.tencent.com/pypi/simple && \
        pip install --no-cache-dir -i https://mirrors.cloud.tencent.com/pypi/simple -r /tmp/shared-libs-requirements.txt; \
    fi

# 复制依赖文件
COPY knowledge-base/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.cloud.tencent.com/pypi/simple && \
    pip install --no-cache-dir -i https://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt

# 生产阶段
FROM python:3.11-slim-bookworm

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制shared_libs
COPY shared_libs /app/../shared_libs

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/documents /app/chroma_db && \
    chown -R appuser:appuser /app

# 复制应用代码
COPY --chown=appuser:appuser knowledge-base/ .

# 设置PYTHONPATH
ENV PYTHONPATH=/app:/app/../shared_libs:${PYTHONPATH}

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8004

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8004/api/health')"

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]

