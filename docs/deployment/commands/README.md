# 部署命令文档

本目录包含所有服务器端执行的部署命令文档。

## 文档分类

### 启动服务命令
- `启动*.txt` - 各种服务的启动命令
- `快速启动*.txt` - 快速启动脚本
- `正确启动*.txt` - 正确的启动顺序和步骤

### 服务器命令
- `服务器启动命令*.txt` - 服务器端启动命令
- `服务器修复命令.txt` - 服务器端修复命令
- `所有服务名称和启动命令.txt` - 所有服务的启动命令

### 修复命令
- `修复*.txt` - 各种修复命令（上传文件后的执行步骤）

### 其他命令
- `创建*.txt` - 创建服务相关命令
- `解决*.txt` - 解决问题相关命令
- `绕过*.txt` - 绕过问题相关命令

## 使用说明

1. 根据需求选择相应的命令文档
2. 复制命令到服务器执行
3. 按照文档中的步骤逐步执行

## 快速参考

### 启动所有服务
```bash
cd /opt/enterprise-ai-platform
sudo docker compose up -d
```

### 启动单个服务
```bash
sudo docker compose up -d --build <service-name>
```

### 检查服务状态
```bash
sudo docker compose ps
```

### 查看服务日志
```bash
sudo docker compose logs --tail=30 <service-name>
```

### 测试服务
```bash
curl http://localhost:<port>/api/health
```

## 服务端口

- mcp-gateway: 8001
- workflow-engine: 8002
- auth-service: 8003
- knowledge-base: 8004
- metadata-service: 8005
- web-ui: 3000
- redis-commander: 8081

