#!/bin/bash
# 收集性能指标

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
METRICS_DIR="$PROJECT_ROOT/code-health/performance-metrics"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "收集性能指标"
echo "=========================================="

# 创建目录
mkdir -p "$METRICS_DIR/build-times"
mkdir -p "$METRICS_DIR/test-times"
mkdir -p "$METRICS_DIR/startup-times"
mkdir -p "$METRICS_DIR/memory-usage"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 1. 收集构建时间
echo ""
echo "收集构建时间..."
if command -v docker &> /dev/null; then
    START_TIME=$(date +%s)
    docker-compose build --no-cache > /dev/null 2>&1 || echo "构建失败，但继续"
    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))
    
    python3 << EOF
import json
from datetime import datetime

try:
    metrics = {
        "timestamp": "$TIMESTAMP",
        "total_build_time_seconds": $BUILD_TIME,
        "services": {}
    }
    
    # 保存到历史记录
    history_file = "$METRICS_DIR/build-times/build-history.json"
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except:
        history = {"history": []}
    
    history["history"].append(metrics)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"✅ 构建时间数据已保存: {$BUILD_TIME}秒")
except Exception as e:
    print(f"⚠️  构建时间数据收集失败: {e}")
EOF
else
    echo "⚠️  Docker未安装，跳过构建时间收集"
fi

# 2. 收集测试时间
echo ""
echo "收集测试时间..."
if command -v pytest &> /dev/null; then
    START_TIME=$(date +%s)
    pytest tests/ -q > /dev/null 2>&1 || echo "测试失败，但继续"
    END_TIME=$(date +%s)
    TEST_TIME=$((END_TIME - START_TIME))
    
    python3 << EOF
import json

try:
    metrics = {
        "timestamp": "$TIMESTAMP",
        "total_test_time_seconds": $TEST_TIME,
        "test_types": {
            "unit": 0,
            "integration": 0,
            "performance": 0
        }
    }
    
    # 保存到历史记录
    history_file = "$METRICS_DIR/test-times/test-history.json"
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except:
        history = {"history": []}
    
    history["history"].append(metrics)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"✅ 测试时间数据已保存: {$TEST_TIME}秒")
except Exception as e:
    print(f"⚠️  测试时间数据收集失败: {e}")
EOF
else
    echo "⚠️  pytest未安装，跳过测试时间收集"
fi

# 3. 收集启动时间（如果服务运行）
echo ""
echo "收集启动时间..."
if docker ps | grep -q "mcp-gateway"; then
    python3 << EOF
import json
import time

try:
    # 简化的启动时间收集
    # 实际应该测量服务从启动到就绪的时间
    
    metrics = {
        "timestamp": "$TIMESTAMP",
        "services": {
            "mcp-gateway": 0,
            "workflow-engine": 0,
            "auth-service": 0,
            "knowledge-base": 0
        }
    }
    
    # 保存到历史记录
    history_file = "$METRICS_DIR/startup-times/startup-history.json"
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except:
        history = {"history": []}
    
    history["history"].append(metrics)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print("✅ 启动时间数据已保存（需要实际测量）")
except Exception as e:
    print(f"⚠️  启动时间数据收集失败: {e}")
EOF
else
    echo "⚠️  服务未运行，跳过启动时间收集"
fi

# 4. 收集内存使用（如果服务运行）
echo ""
echo "收集内存使用..."
if docker ps | grep -q "mcp-gateway"; then
    python3 << EOF
import json
import subprocess

try:
    # 使用docker stats收集内存使用
    result = subprocess.run(
        ['docker', 'stats', '--no-stream', '--format', '{{.Name}} {{.MemUsage}}'],
        capture_output=True,
        text=True
    )
    
    memory_data = {}
    for line in result.stdout.splitlines():
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                service = parts[0]
                memory = parts[1]
                memory_data[service] = memory
    
    metrics = {
        "timestamp": "$TIMESTAMP",
        "services": memory_data,
        "total_memory_mb": 0
    }
    
    # 保存到历史记录
    history_file = "$METRICS_DIR/memory-usage/memory-history.json"
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except:
        history = {"history": []}
    
    history["history"].append(metrics)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print("✅ 内存使用数据已保存")
except Exception as e:
    print(f"⚠️  内存使用数据收集失败: {e}")
EOF
else
    echo "⚠️  服务未运行，跳过内存使用收集"
fi

echo ""
echo "=========================================="
echo "性能指标收集完成"
echo "=========================================="









