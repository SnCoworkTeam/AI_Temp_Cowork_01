#!/bin/bash
# 在服务器Docker容器中执行测试
# 遍历所有服务，在各自的容器中运行测试并收集覆盖率

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"

SERVICES=(
    "auth-service"
    "knowledge-base"
    "metadata-service"
    "workflow-engine"
    "mcp-gateway"
    "database"
)

RESULTS_FILE="/tmp/.test-results.json"
COVERAGE_FILE="/tmp/.coverage-status.json"

echo "=========================================="
echo "在Docker容器中执行测试"
echo "=========================================="
echo ""

declare -A results

for service in "${SERVICES[@]}"; do
    echo "----------------------------------------"
    echo "服务: $service"
    echo "----------------------------------------"
    
    container_name="enterprise-ai-${service}"
    
    # 检查容器是否运行
    if ! sudo docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo "⚠ 容器未运行: $container_name"
        # 存储容器未运行的结果
        python3 << PYEOF
import json

service = "$service"
temp_file = "/tmp/test_result_${service}.json"

result = {
    "service": service,
    "status": "container_not_running",
    "coverage": 0,
    "passed": 0,
    "failed": 0,
    "errors": 0
}

with open(temp_file, 'w') as f:
    json.dump(result, f)
PYEOF
        continue
    fi
    
    echo "容器: $container_name"
    echo "运行测试..."
    
    # 在容器中执行测试
    # 使用timeout防止测试卡住
    if timeout 600 sudo docker exec "$container_name" python3 -m pytest /app/tests/ \
        --cov=/app/src \
        --cov-report=json:/tmp/coverage.json \
        --cov-report=term-missing \
        -v 2>&1 | tee "/tmp/test_output_${service}.log"; then
        
        test_exit_code=${PIPESTATUS[0]}
        
        # 从容器中复制覆盖率JSON
        sudo docker cp "${container_name}:/tmp/coverage.json" "/tmp/coverage_${service}.json" 2>/dev/null || {
            echo "⚠ 无法获取覆盖率JSON"
        }
        
        # 解析测试结果
        if [ -f "/tmp/test_output_${service}.log" ]; then
            passed=$(grep -oP '\d+(?= passed)' "/tmp/test_output_${service}.log" | head -1 || echo "0")
            failed=$(grep -oP '\d+(?= failed)' "/tmp/test_output_${service}.log" | head -1 || echo "0")
            errors=$(grep -oP '\d+(?= error)' "/tmp/test_output_${service}.log" | head -1 || echo "0")
        else
            passed=0
            failed=0
            errors=0
        fi
        
        # 解析覆盖率
        if [ -f "/tmp/coverage_${service}.json" ]; then
            coverage=$(python3 << 'PYEOF'
import json
import sys
try:
    with open('/tmp/coverage_' + sys.argv[1] + '.json', 'r') as f:
        data = json.load(f)
    total = data['totals']['num_statements']
    covered = data['totals']['covered_lines']
    if total > 0:
        coverage = round((covered / total) * 100, 2)
    else:
        coverage = 0
    print(coverage)
except Exception as e:
    print(0)
PYEOF
"$service" 2>/dev/null || echo "0")
        else
            coverage=0
        fi
        
        if [ "$test_exit_code" -eq 0 ]; then
            test_status="passed"
        else
            test_status="failed"
        fi
        
        # 存储到临时JSON文件
        python3 << PYEOF
import json
import os

service = "$service"
temp_file = "/tmp/test_result_${service}.json"

result = {
    "service": service,
    "status": "$test_status",
    "coverage": $coverage,
    "passed": $passed,
    "failed": $failed,
    "errors": $errors
}

with open(temp_file, 'w') as f:
    json.dump(result, f)
PYEOF
        
        echo "✓ 测试完成"
        echo "  通过: $passed, 失败: $failed, 错误: $errors"
        echo "  覆盖率: ${coverage}%"
        
    else
        echo "✗ 测试执行失败或超时"
        # 存储错误结果
        python3 << PYEOF
import json

service = "$service"
temp_file = "/tmp/test_result_${service}.json"

result = {
    "service": service,
    "status": "error",
    "coverage": 0,
    "passed": 0,
    "failed": 0,
    "errors": 1
}

with open(temp_file, 'w') as f:
    json.dump(result, f)
PYEOF
    fi
    
    echo ""
done

# 生成结果JSON
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
all_passed = True
all_above_80 = True

for service in services:
    service_key = service.replace('-', '_')
    status = os.environ.get(f"{service_key.upper()}_STATUS", "unknown")
    coverage = float(os.environ.get(f"{service_key.upper()}_COVERAGE", "0"))
    passed = int(os.environ.get(f"{service_key.upper()}_PASSED", "0"))
    failed = int(os.environ.get(f"{service_key.upper()}_FAILED", "0"))
    errors = int(os.environ.get(f"{service_key.upper()}_ERRORS", "0"))
    
    results[service] = {
        "status": status,
        "coverage": coverage,
        "passed": passed,
        "failed": failed,
        "errors": errors
    }
    
    if status != "passed":
        all_passed = False
    if coverage < 80:
        all_above_80 = False

output = {
    "timestamp": datetime.now().isoformat(),
    "all_passed": all_passed,
    "all_above_80": all_above_80,
    "services": results
}

results_file = os.environ.get("RESULTS_FILE", ".test-results.json")
with open(results_file, 'w') as f:
    json.dump(output, f, indent=2)

print(json.dumps(output, indent=2))
PYEOF

# 从临时文件收集所有结果
python3 << 'PYEOF'
import json
import os
from datetime import datetime
from pathlib import Path

services = [
    "auth-service",
    "knowledge-base",
    "metadata-service",
    "workflow-engine",
    "mcp-gateway",
    "database"
]

results = {}
all_passed = True
all_above_80 = True

# 从临时文件读取每个服务的结果
for service in services:
    temp_file = f"/tmp/test_result_{service}.json"
    if os.path.exists(temp_file):
        try:
            with open(temp_file, 'r') as f:
                result = json.load(f)
                results[service] = {
                    "status": result.get("status", "unknown"),
                    "coverage": result.get("coverage", 0.0),
                    "passed": result.get("passed", 0),
                    "failed": result.get("failed", 0),
                    "errors": result.get("errors", 0)
                }
        except:
            results[service] = {
                "status": "error",
                "coverage": 0.0,
                "passed": 0,
                "failed": 0,
                "errors": 0
            }
    else:
        results[service] = {
            "status": "not_checked",
            "coverage": 0.0,
            "passed": 0,
            "failed": 0,
            "errors": 0
        }
    
    if results[service]["status"] != "passed":
        all_passed = False
    if results[service]["coverage"] < 80:
        all_above_80 = False

output = {
    "timestamp": datetime.now().isoformat(),
    "all_passed": all_passed,
    "all_above_80": all_above_80,
    "services": results
}

results_file = os.environ.get("RESULTS_FILE", ".test-results.json")
with open(results_file, 'w') as f:
    json.dump(output, f, indent=2)

print(json.dumps(output, indent=2))
PYEOF

echo ""
echo "测试结果已保存到: .test-results.json"
echo ""

if [ "$all_above_80" = "true" ]; then
    echo "✓ 所有服务已达到80%覆盖率！"
    exit 0
else
    echo "⚠ 还有服务未达到80%覆盖率"
    exit 1
fi

