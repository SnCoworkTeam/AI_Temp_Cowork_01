FROM python:3.11-slim-bookworm

WORKDIR /app

# 配置 Debian 软件源（使用国内镜像）
RUN sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null || true

# 配置pip国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.timeout 300 && \
    pip config set global.retries 5

# 安装curl用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ ./src/

# 暴露端口
EXPOSE 8080

# 启动服务
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
