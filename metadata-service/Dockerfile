# 多阶段构建 - 生产环境
FROM python:3.11-slim-bookworm-bookworm as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY metadata-service/requirements.txt .
COPY shared_libs/requirements.txt ./shared_libs-requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir --user -i https://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt
RUN pip install --no-cache-dir --user -i https://mirrors.cloud.tencent.com/pypi/simple -r shared_libs-requirements.txt

# 安装共享库包
COPY shared_libs ./shared_libs
RUN pip install --user -e ./shared_libs

# 生产阶段
FROM python:3.11-slim-bookworm

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY metadata-service/src ./src

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8005

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/api/health')"

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005"]

