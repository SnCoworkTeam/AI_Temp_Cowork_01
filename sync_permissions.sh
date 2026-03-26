#!/bin/bash
# 权限同步脚本 - 使用curl直接调用API

API_BASE_URL="http://43.143.139.197:8080"
AUTH_URL="${API_BASE_URL}/api/auth/login"

# 管理员账号（需要根据实际情况修改）
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

echo "============================================================"
echo "权限同步到Redis脚本"
echo "============================================================"

# 获取认证token
echo ""
echo "正在获取认证token..."
TOKEN_RESPONSE=$(curl -s -X POST "${AUTH_URL}" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${ADMIN_USERNAME}\",\"password\":\"${ADMIN_PASSWORD}\"}")

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "✗ 无法获取认证token，请检查管理员账号和密码"
  echo "响应: $TOKEN_RESPONSE"
  exit 1
fi

echo "✓ 认证成功"

# 权限列表
PERMISSIONS=(
  '{"name":"查看用户","code":"user:read","resource_type":"user","permission_type":"read","description":"查看用户信息"}'
  '{"name":"创建用户","code":"user:create","resource_type":"user","permission_type":"write","description":"创建新用户"}'
  '{"name":"更新用户","code":"user:update","resource_type":"user","permission_type":"write","description":"更新用户信息"}'
  '{"name":"删除用户","code":"user:delete","resource_type":"user","permission_type":"delete","description":"删除用户"}'
  '{"name":"查看角色","code":"role:read","resource_type":"admin","permission_type":"read","description":"查看角色信息"}'
  '{"name":"创建角色","code":"role:create","resource_type":"admin","permission_type":"write","description":"创建新角色"}'
  '{"name":"更新角色","code":"role:update","resource_type":"admin","permission_type":"write","description":"更新角色信息"}'
  '{"name":"删除角色","code":"role:delete","resource_type":"admin","permission_type":"delete","description":"删除角色"}'
  '{"name":"查看权限","code":"permission:read","resource_type":"admin","permission_type":"read","description":"查看权限信息"}'
  '{"name":"创建权限","code":"permission:create","resource_type":"admin","permission_type":"write","description":"创建新权限"}'
  '{"name":"更新权限","code":"permission:update","resource_type":"admin","permission_type":"write","description":"更新权限信息"}'
  '{"name":"删除权限","code":"permission:delete","resource_type":"admin","permission_type":"delete","description":"删除权限"}'
  '{"name":"查看项目","code":"project:read","resource_type":"user","permission_type":"read","description":"查看项目信息"}'
  '{"name":"创建项目","code":"project:create","resource_type":"user","permission_type":"write","description":"创建新项目"}'
  '{"name":"更新项目","code":"project:update","resource_type":"user","permission_type":"write","description":"更新项目信息"}'
  '{"name":"删除项目","code":"project:delete","resource_type":"user","permission_type":"delete","description":"删除项目"}'
  '{"name":"查看工作流","code":"workflow:read","resource_type":"workflow","permission_type":"read","description":"查看工作流信息"}'
  '{"name":"创建工作流","code":"workflow:create","resource_type":"workflow","permission_type":"write","description":"创建新工作流"}'
  '{"name":"更新工作流","code":"workflow:update","resource_type":"workflow","permission_type":"write","description":"更新工作流信息"}'
  '{"name":"删除工作流","code":"workflow:delete","resource_type":"workflow","permission_type":"delete","description":"删除工作流"}'
  '{"name":"执行工作流","code":"workflow:execute","resource_type":"workflow","permission_type":"execute","description":"执行工作流"}'
  '{"name":"查看知识库","code":"knowledge:read","resource_type":"user","permission_type":"read","description":"查看知识库信息"}'
  '{"name":"创建知识库","code":"knowledge:create","resource_type":"user","permission_type":"write","description":"创建新知识库"}'
  '{"name":"更新知识库","code":"knowledge:update","resource_type":"user","permission_type":"write","description":"更新知识库信息"}'
  '{"name":"删除知识库","code":"knowledge:delete","resource_type":"user","permission_type":"delete","description":"删除知识库"}'
  '{"name":"查看工具","code":"tool:read","resource_type":"tool","permission_type":"read","description":"查看工具信息"}'
  '{"name":"创建工具","code":"tool:create","resource_type":"tool","permission_type":"write","description":"创建新工具"}'
  '{"name":"更新工具","code":"tool:update","resource_type":"tool","permission_type":"write","description":"更新工具信息"}'
  '{"name":"删除工具","code":"tool:delete","resource_type":"tool","permission_type":"delete","description":"删除工具"}'
  '{"name":"执行工具","code":"tool:execute","resource_type":"tool","permission_type":"execute","description":"执行工具"}'
  '{"name":"查看系统","code":"system:read","resource_type":"system","permission_type":"read","description":"查看系统信息"}'
  '{"name":"更新系统","code":"system:update","resource_type":"system","permission_type":"write","description":"更新系统配置"}'
  '{"name":"监控系统","code":"system:monitor","resource_type":"system","permission_type":"read","description":"监控系统状态"}'
)

echo ""
echo "开始创建权限（共 ${#PERMISSIONS[@]} 个）..."

SUCCESS_COUNT=0
for PERM in "${PERMISSIONS[@]}"; do
  CODE=$(echo $PERM | grep -o '"code":"[^"]*' | cut -d'"' -f4)
  NAME=$(echo $PERM | grep -o '"name":"[^"]*' | cut -d'"' -f4)
  
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE_URL}/api/auth/admin/permissions" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${PERM}")
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | sed '$d')
  
  if [ "$HTTP_CODE" = "201" ]; then
    echo "  ✓ 创建权限: ${CODE} - ${NAME}"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  elif [ "$HTTP_CODE" = "400" ]; then
    if echo "$BODY" | grep -q "already exists\|已存在"; then
      echo "  - 权限已存在: ${CODE}"
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
      echo "  ✗ 创建失败: ${CODE} - ${BODY}"
    fi
  else
    echo "  ✗ 创建失败: ${CODE} - HTTP ${HTTP_CODE} - ${BODY}"
  fi
done

echo ""
echo "权限创建完成: ${SUCCESS_COUNT}/${#PERMISSIONS[@]}"
echo ""
echo "✓ 权限同步完成！"
echo "============================================================"

