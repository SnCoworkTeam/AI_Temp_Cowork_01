#!/bin/bash
# 构建状态监控脚本
# 在服务器上执行: bash /opt/enterprise-ai-platform/scripts/deployment/monitor-build-status.sh

cd /opt/enterprise-ai-platform

echo "=========================================="
echo "构建和部署状态监控"
echo "=========================================="
echo ""

echo "1. 构建进程状态:"
BUILD_PROCESSES=$(ps aux | grep "[d]ocker compose.*up.*build" | wc -l)
echo "   运行中的构建进程: $BUILD_PROCESSES"
if [ $BUILD_PROCESSES -gt 0 ]; then
    echo "   ✓ 构建正在进行中"
else
    echo "   - 没有运行中的构建进程"
fi
echo ""

echo "2. 服务状态:"
sudo docker compose -f docker-compose.prod.yml ps 2>&1 | head -20
echo ""

echo "3. 所有容器状态:"
sudo docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | head -15
echo ""

echo "4. 构建日志检查:"
if [ -f /tmp/docker-build-full.log ]; then
    echo "   日志文件大小: $(ls -lh /tmp/docker-build-full.log | awk '{print $5}')"
    echo "   最后更新时间: $(stat -c %y /tmp/docker-build-full.log 2>/dev/null || stat -f %Sm /tmp/docker-build-full.log 2>/dev/null)"
    echo ""
    echo "   最新日志（最后15行）:"
    tail -15 /tmp/docker-build-full.log
    echo ""
    echo "   检查错误:"
    ERRORS=$(tail -300 /tmp/docker-build-full.log | grep -iE "error|failed|exit code [1-9]" | tail -5)
    if [ -z "$ERRORS" ]; then
        echo "   ✓ 未发现错误"
    else
        echo "   ⚠ 发现错误:"
        echo "$ERRORS"
    fi
    echo ""
    echo "   检查成功构建:"
    tail -500 /tmp/docker-build-full.log | grep -iE "successfully built|creating.*container|started" | tail -5 || echo "   构建进行中..."
else
    echo "   ⚠ 构建日志文件不存在"
fi
echo ""

echo "5. 镜像检查:"
sudo docker images | grep -E "enterprise-ai-platform|mcp-gateway|workflow-engine|auth-service|knowledge-base" | head -10 || echo "   未找到相关镜像"
echo ""

echo "6. 镜像源配置验证:"
echo "   检查 Dockerfile 中的腾讯云镜像源:"
grep -h "mirrors.cloud.tencent.com" */Dockerfile 2>/dev/null | head -3 || echo "   未找到腾讯云镜像源配置"
echo ""

echo "=========================================="
echo "建议操作:"
echo "=========================================="
if [ $BUILD_PROCESSES -gt 0 ]; then
    echo "构建正在进行中，请稍候..."
    echo "查看实时日志: tail -f /tmp/docker-build-full.log"
else
    echo "如果构建已完成但服务未启动，执行:"
    echo "  sudo docker compose -f docker-compose.prod.yml up -d"
    echo ""
    echo "如果构建失败，查看完整日志:"
    echo "  cat /tmp/docker-build-full.log"
    echo ""
    echo "重新构建并启动:"
    echo "  sudo docker compose -f docker-compose.prod.yml up -d --build"
fi
echo "=========================================="

