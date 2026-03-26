#!/bin/bash
# 在服务器上检查各服务在Docker中的测试覆盖率
# 输出JSON格式的覆盖率报告

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"

OUTPUT_FILE="/tmp/.coverage-status.json"
SERVICES=(
    "auth-service"
    "knowledge-base"
    "metadata-service"
    "workflow-engine"
    "mcp-gateway"
    "database"
)

echo "=========================================="
echo "检查各服务测试覆盖率（Docker）"
echo "=========================================="
echo ""

# 初始化结果数组
declare -A results

for service in "${SERVICES[@]}"; do
    echo "检查 $service..."
    
    container_name="enterprise-ai-${service}"
    
    # 检查容器是否运行
    if ! sudo docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo "  容器未运行，跳过"
        service_key=$(echo "$service" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
        export "COV_${service_key}_COVERAGE=0"
        export "COV_${service_key}_STATUS=container_not_running"
        export "COV_${service_key}_TOTAL=0"
        export "COV_${service_key}_COVERED=0"
        export "COV_${service_key}_MISSED=0"
        continue
    fi
    
    # 在容器中执行测试并获取覆盖率
    echo "  在容器中运行测试..."
    
    # 创建临时目录存储覆盖率报告
    sudo docker exec "$container_name" mkdir -p /tmp/coverage 2>/dev/null || true
    
    # 运行测试并生成JSON报告
    if sudo docker exec "$container_name" python3 -m pytest /app/tests/ \
        --cov=/app/src \
        --cov-report=json:/tmp/coverage/.coverage.json \
        --cov-report=term-missing \
        -q 2>&1 | tee /tmp/test_output_${service}.log; then
        
        # 从容器中复制覆盖率JSON文件
        if ! sudo docker cp "${container_name}:/tmp/coverage/.coverage.json" "/tmp/coverage_${service}.json" 2>/dev/null; then
            echo "  无法获取覆盖率JSON文件"
            service_key=$(echo "$service" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
            export "COV_${service_key}_COVERAGE=0"
            export "COV_${service_key}_STATUS=no_coverage_data"
            export "COV_${service_key}_TOTAL=0"
            export "COV_${service_key}_COVERED=0"
            export "COV_${service_key}_MISSED=0"
            continue
        fi
        
        # 解析JSON文件
        if [ -f "/tmp/coverage_${service}.json" ]; then
            total=$(python3 -c "import json; data=json.load(open('/tmp/coverage_${service}.json')); print(data['totals']['num_statements'])" 2>/dev/null || echo "0")
            covered=$(python3 -c "import json; data=json.load(open('/tmp/coverage_${service}.json')); print(data['totals']['covered_lines'])" 2>/dev/null || echo "0")
            missed=$((total - covered))
            
            if [ "$total" -gt 0 ]; then
                coverage=$(python3 -c "print(round(($covered / $total) * 100, 2))" 2>/dev/null || echo "0")
            else
                coverage=0
            fi
            
            # 存储结果到环境变量供Python使用
            service_key=$(echo "$service" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
            export "COV_${service_key}_COVERAGE=$coverage"
            export "COV_${service_key}_STATUS=ok"
            export "COV_${service_key}_TOTAL=$total"
            export "COV_${service_key}_COVERED=$covered"
            export "COV_${service_key}_MISSED=$missed"
            
            echo "  覆盖率: ${coverage}% (总计: $total, 已覆盖: $covered, 缺失: $missed)"
        else
            service_key=$(echo "$service" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
            export "COV_${service_key}_COVERAGE=0"
            export "COV_${service_key}_STATUS=parse_error"
            export "COV_${service_key}_TOTAL=0"
            export "COV_${service_key}_COVERED=0"
            export "COV_${service_key}_MISSED=0"
        fi
    else
        echo "  测试执行失败"
        service_key=$(echo "$service" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
        export "COV_${service_key}_COVERAGE=0"
        export "COV_${service_key}_STATUS=test_failed"
        export "COV_${service_key}_TOTAL=0"
        export "COV_${service_key}_COVERED=0"
        export "COV_${service_key}_MISSED=0"
    fi
    
    echo ""
done

# 生成JSON输出
echo "生成覆盖率报告..."

# 构建Python脚本，从环境变量读取结果
export OUTPUT_FILE
python3 << 'PYEOF'
import json
import os
from datetime import datetime

services = [
    "auth-service",
    "knowledge-base",
    "metadata-service",
    "workflow-engine",
    "mcp-gateway",
    "database"
]

results = {}
all_above_80 = True

# 从环境变量读取
for service in services:
    service_key = service.replace('-', '_').upper()
    coverage = float(os.environ.get(f"COV_{service_key}_COVERAGE", "0"))
    status = os.environ.get(f"COV_{service_key}_STATUS", "not_checked")
    total = int(os.environ.get(f"COV_{service_key}_TOTAL", "0"))
    covered = int(os.environ.get(f"COV_{service_key}_COVERED", "0"))
    missed = int(os.environ.get(f"COV_{service_key}_MISSED", "0"))
    
    results[service] = {
        "coverage": coverage,
        "status": status,
        "total": total,
        "covered": covered,
        "missed": missed
    }
    
    if coverage < 80:
        all_above_80 = False

output = {
    "timestamp": datetime.now().isoformat(),
    "all_above_80": all_above_80,
    "services": results
}

output_file = os.environ.get("OUTPUT_FILE", ".coverage-status.json")
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

print(json.dumps(output, indent=2))
PYEOF

echo ""
echo "覆盖率报告已保存到: $OUTPUT_FILE"
echo ""

# 检查是否所有服务都达到80%
if python3 -c "import json; data=json.load(open('$OUTPUT_FILE')); exit(0 if data['all_above_80'] else 1)"; then
    echo "✓ 所有服务已达到80%覆盖率！"
    exit 0
else
    echo "⚠ 还有服务未达到80%覆盖率"
    exit 1
fi

