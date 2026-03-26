#!/bin/bash
# OpenCode 启动失败诊断脚本
# 在服务器上执行：bash diagnose-opencode.sh > diagnose-result.txt 2>&1

echo "=========================================="
echo "OpenCode 启动失败诊断报告"
echo "执行时间: $(date)"
echo "=========================================="
echo

echo "【1. 容器运行状态】"
echo "----------------------------"
docker ps -a | grep -E "CONTAINER ID|opencode"
echo

echo "【2. 容器是否真的在运行】"
echo "----------------------------"
CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' enterprise-ai-opencode 2>&1)
echo "容器状态: $CONTAINER_STATUS"
if [ "$CONTAINER_STATUS" = "running" ]; then
    echo "✓ 容器状态为 running"
    CONTAINER_STARTED_AT=$(docker inspect -f '{{.State.StartedAt}}' enterprise-ai-opencode)
    echo "启动时间: $CONTAINER_STARTED_AT"
else
    echo "✗ 容器未运行！"
fi
echo

echo "【3. 容器日志（最近100行）】"
echo "----------------------------"
docker logs --tail 100 enterprise-ai-opencode 2>&1
echo

echo "【4. 容器内进程】"
echo "----------------------------"
docker exec enterprise-ai-opencode ps aux 2>&1 | head -20
echo

echo "【5. 容器内端口监听】"
echo "----------------------------"
docker exec enterprise-ai-opencode netstat -tlnp 2>&1 || docker exec enterprise-ai-opencode ss -tlnp 2>&1
echo

echo "【6. 容器内环境变量（关键配置）】"
echo "----------------------------"
docker exec enterprise-ai-opencode env 2>&1 | grep -E "OPENCODE|PORT|NODE|PATH" | sort
echo

echo "【7. 构建信息】"
echo "----------------------------"
docker exec enterprise-ai-opencode cat /app-web/build.txt 2>&1
echo

echo "【8. 验证修复代码是否存在】"
echo "----------------------------"
echo "检查 server.ts 是否包含 'local-web-ok':"
docker exec enterprise-ai-opencode grep -n "local-web-ok" /app-web/packages/opencode/src/server/server.ts 2>&1
echo
echo "检查 server.ts 是否包含早处理中间件标记:"
docker exec enterprise-ai-opencode grep -n "本地 Web：最先处理根路径" /app-web/packages/opencode/src/server/server.ts 2>&1
echo

echo "【9. Docker Compose 配置】"
echo "----------------------------"
cat docker-compose.opencode.local-web.yml
echo

echo "【10. 环境变量文件】"
echo "----------------------------"
echo "关键环境变量（脱敏）:"
cat .env | grep -E "OPENCODE|PORT" | sed 's/=.*/=***/' 2>&1
echo

echo "【11. 主机端口占用情况】"
echo "----------------------------"
netstat -tlnp | grep 4096 || ss -tlnp | grep 4096
echo

echo "【12. Docker 网络配置】"
echo "----------------------------"
docker network inspect opencode-server-export_default 2>&1 | head -50
echo

echo "【13. 主机资源使用】"
echo "----------------------------"
echo "CPU 和内存:"
top -bn1 | head -5
echo
echo "磁盘空间:"
df -h | grep -E "Filesystem|/$|/var|/opt"
echo

echo "【14. 从主机测试容器端口】"
echo "----------------------------"
echo "测试 127.0.0.1:4096/local-web-root:"
timeout 3 curl -v http://127.0.0.1:4096/local-web-root 2>&1 | head -20
echo
echo "测试 127.0.0.1:4096/:"
timeout 3 curl -v http://127.0.0.1:4096/ 2>&1 | head -20
echo

echo "=========================================="
echo "诊断完成"
echo "=========================================="
