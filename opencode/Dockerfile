# OpenCode 同机部署：无头 serve 模式，与 19 服务共用代码目录
# 使用: docker compose --profile optional build opencode
# 参考: docs/deployment/OpenCode同机部署实施方案.md

FROM node:20-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# 使用非 root 用户运行（可选，opencode 无特殊要求时可保留 root 以简化挂载）
RUN npm install -g opencode-ai@latest

WORKDIR /workspace

EXPOSE 4096

# 默认以 serve 模式启动；hostname 在 compose 的 command 中覆盖
CMD ["opencode", "serve", "--hostname", "0.0.0.0", "--port", "4096"]
