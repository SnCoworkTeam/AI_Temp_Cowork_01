#!/bin/bash
# 页面不显示时在服务器上执行。
# 若报 $'\r': command not found，先执行: sed -i 's/\r$//' check-page-load.sh
# 用法: cd opencode-server-export && bash check-page-load.sh
# 若本机 curl 127.0.0.1 全是 000，可改下面 BASE 为 http://10.24.20.56:4096 再测

BASE="http://127.0.0.1:4096"
echo "=========================================="
echo "OpenCode 页面加载检查 - $(date)"
echo "=========================================="
echo ""
echo "【0】容器与端口"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|opencode" || true
echo ""
echo "【1】根路径 GET /"
curl -s -o /dev/null -w "  GET / -> %{http_code}\n" -m 5 "$BASE/" || echo "  失败(超时/未连上)"
echo ""
echo "【2】静态资源"
curl -s -o /dev/null -w "  site.webmanifest -> %{http_code}\n" -m 5 "$BASE/site.webmanifest" || echo "  失败"
curl -s -o /dev/null -w "  favicon -> %{http_code}\n" -m 5 "$BASE/favicon-v3.ico" || echo "  失败"
echo ""
echo "【3】健康检查"
curl -s -o /dev/null -w "  /global/health -> %{http_code}\n" -m 5 "$BASE/global/health" || echo "  失败"
echo ""
echo "【4】构建标记"
docker exec enterprise-ai-opencode cat /app-web/build.txt 2>/dev/null || echo "  无法读取(容器未运行?)"
echo "=========================================="
