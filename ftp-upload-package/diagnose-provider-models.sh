#!/bin/bash
# 供应商/模型数据为空时在服务器上执行，用于定位问题
# 用法: cd opencode-server-export && bash diagnose-provider-models.sh
# 若报 $'\r': command not found，先执行: sed -i 's/\r$//' diagnose-provider-models.sh

set -e
BASE="${OPENCODE_BASE_URL:-http://127.0.0.1:4096}"
# 从 .env 读密码（若存在）
if [ -f .env ]; then
  set -a
  source .env 2>/dev/null || true
  set +a
fi
USER="${OPENCODE_SERVER_USERNAME:-opencode}"
PASS="${OPENCODE_SERVER_PASSWORD:-}"
CURL_AUTH=""
if [ -n "$PASS" ]; then
  CURL_AUTH="-u ${USER}:${PASS}"
fi

echo "=========================================="
echo "OpenCode 供应商/模型 诊断 - $(date)"
echo "=========================================="
echo ""

echo "【1】容器与卷"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Mounts}}" | grep -E "NAMES|opencode" || true
echo ""

echo "【2】容器内数据目录（auth、models 是否存在）"
docker exec enterprise-ai-opencode sh -c '
  echo "HOME=$HOME"
  for d in "$HOME/.local/share/opencode" "$HOME/.cache/opencode" "/opencode-home/.local/share/opencode" "/opencode-home/.cache/opencode"; do
    if [ -d "$d" ]; then
      echo "  $d:"
      ls -la "$d" 2>/dev/null || true
    else
      echo "  $d: 不存在"
    fi
  done
  if [ -f "$HOME/.local/share/opencode/auth.json" ]; then
    echo "  auth.json 前 200 字符（脱敏）:"
    head -c 200 "$HOME/.local/share/opencode/auth.json" | sed "s/\"key\":\"[^\"]*\"/\"key\":\"***\"/g"
    echo ""
  fi
  if [ -f "$HOME/.cache/opencode/models.json" ]; then
    echo "  models.json 大小: $(wc -c < "$HOME/.cache/opencode/models.json") 字节"
    echo "  前 300 字符:"
    head -c 300 "$HOME/.cache/opencode/models.json"
    echo ""
  fi
' 2>/dev/null || echo "  (无法执行，检查容器是否运行)"
echo ""

echo "【3】环境变量（与 models 相关）"
docker exec enterprise-ai-opencode env 2>/dev/null | grep -E "OPENCODE_MODELS|OPENCODE_DISABLE_MODELS|HOME" || echo "  无相关变量或容器未运行"
echo ""

echo "【4】接口 /provider/list 响应"
RESP=$(curl -s -w "\n%{http_code}" $CURL_AUTH -m 10 "$BASE/provider/list" 2>/dev/null || echo -e "\n000")
BODY=$(echo "$RESP" | head -n -1)
CODE=$(echo "$RESP" | tail -n 1)
echo "  HTTP 状态: $CODE"
if [ "$CODE" = "200" ]; then
  ALL_COUNT=$(echo "$BODY" | grep -o '"all":\s*\[' | head -1)
  echo "  响应片段: ${BODY:0:500}..."
  if echo "$BODY" | grep -q '"all":\[\]'; then
    echo "  >>> all 数组为空，说明供应商列表为空"
  fi
else
  echo "  响应: $BODY"
fi
echo ""

echo "【5】容器内能否访问 models.dev"
docker exec enterprise-ai-opencode sh -c 'curl -s -o /dev/null -w "%{http_code}" -m 5 https://models.dev/api.json 2>/dev/null || echo "000"' 2>/dev/null && echo "  (上行为 HTTP 状态码，200 表示可访问)" || echo "  无法执行或超时"
echo ""

echo "【6】日志中与 models / provider 相关的最近行"
docker logs --tail 200 enterprise-ai-opencode 2>&1 | grep -iE "models|provider|ModelsDev|fetch|auth\.json" || echo "  无匹配"
echo ""

echo "=========================================="
echo "结论建议:"
echo "  - 若【2】中 auth.json/models.json 不存在或目录为空: 未挂载数据卷或首次运行未拉取到；需挂载卷并确保能访问 models.dev 或挂载本地 models.json"
echo "  - 若【4】返回 401: 请带认证 curl -u 用户:密码 $BASE/provider/list"
echo "  - 若【4】返回 200 但 all 为空: 多为 ModelsDev.get() 为空（无法拉 models.dev 且无缓存）；可设 OPENCODE_MODELS_PATH 指向宿主机上的 models.json"
echo "  - 若【5】非 200: 容器无法访问外网，需在能出网机器下载 https://models.dev/api.json 后挂载进容器"
echo "=========================================="
