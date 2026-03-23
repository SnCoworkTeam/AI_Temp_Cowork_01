#!/bin/bash
# 收集质量指标

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
METRICS_DIR="$PROJECT_ROOT/code-health/quality-metrics"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "收集质量指标"
echo "=========================================="

# 创建目录
mkdir -p "$METRICS_DIR/coverage-trends"
mkdir -p "$METRICS_DIR/complexity-trends"
mkdir -p "$METRICS_DIR/debt-tracking"
mkdir -p "$METRICS_DIR/bug-density"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 1. 收集代码覆盖率
echo ""
echo "收集代码覆盖率..."
if command -v pytest &> /dev/null && command -v coverage &> /dev/null; then
    # 运行测试并生成覆盖率报告
    pytest --cov=. --cov-report=json --cov-report=html -q || echo "测试失败，但继续收集覆盖率"
    
    if [ -f ".coverage.json" ] || [ -f "coverage.json" ]; then
        COVERAGE_FILE=$(find . -name "coverage.json" -type f | head -1)
        if [ -n "$COVERAGE_FILE" ]; then
            # 提取覆盖率数据
            python3 << EOF
import json
from datetime import datetime

try:
    with open('$COVERAGE_FILE', 'r') as f:
        coverage_data = json.load(f)
    
    total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
    
    metrics = {
        "timestamp": "$TIMESTAMP",
        "overall_coverage": round(total_coverage, 2),
        "lines_covered": coverage_data.get('totals', {}).get('covered_lines', 0),
        "lines_total": coverage_data.get('totals', {}).get('num_statements', 0),
        "branches_covered": coverage_data.get('totals', {}).get('covered_branches', 0),
        "branches_total": coverage_data.get('totals', {}).get('num_branches', 0)
    }
    
    # 保存到历史记录
    history_file = "$METRICS_DIR/coverage-trends/coverage-history.json"
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except:
        history = {"history": []}
    
    history["history"].append(metrics)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"✅ 覆盖率数据已保存: {total_coverage:.2f}%")
except Exception as e:
    print(f"⚠️  覆盖率数据收集失败: {e}")
EOF
        fi
    fi
else
    echo "⚠️  pytest或coverage未安装，跳过覆盖率收集"
fi

# 2. 收集代码复杂度
echo ""
echo "收集代码复杂度..."
if command -v radon &> /dev/null; then
    # 使用radon收集复杂度
    radon cc --json . > "$METRICS_DIR/complexity-trends/complexity-raw.json" 2>/dev/null || echo "复杂度收集失败"
    
    # 处理复杂度数据
    python3 << EOF
import json
from datetime import datetime
from collections import defaultdict

try:
    with open('$METRICS_DIR/complexity-trends/complexity-raw.json', 'r') as f:
        complexity_data = json.load(f)
    
    total_complexity = 0
    function_count = 0
    max_complexity = 0
    complex_functions = []
    
    def analyze_complexity(data, path=""):
        nonlocal total_complexity, function_count, max_complexity, complex_functions
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and 'complexity' in item:
                            comp = item['complexity']
                            total_complexity += comp
                            function_count += 1
                            max_complexity = max(max_complexity, comp)
                            
                            if comp > 15:
                                complex_functions.append({
                                    "file": key,
                                    "function": item.get('name', 'unknown'),
                                    "complexity": comp,
                                    "lines": item.get('endline', 0) - item.get('lineno', 0) + 1
                                })
                else:
                    analyze_complexity(value, f"{path}.{key}")
        elif isinstance(data, list):
            for item in data:
                analyze_complexity(item, path)
    
    analyze_complexity(complexity_data)
    
    avg_complexity = total_complexity / function_count if function_count > 0 else 0
    
    metrics = {
        "timestamp": "$TIMESTAMP",
        "average_complexity": round(avg_complexity, 2),
        "max_complexity": max_complexity,
        "function_count": function_count,
        "complex_functions": sorted(complex_functions, key=lambda x: x['complexity'], reverse=True)[:10]
    }
    
    # 保存到历史记录
    history_file = "$METRICS_DIR/complexity-trends/complexity-history.json"
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except:
        history = {"history": []}
    
    history["history"].append(metrics)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"✅ 复杂度数据已保存: 平均={avg_complexity:.2f}, 最大={max_complexity}")
except Exception as e:
    print(f"⚠️  复杂度数据收集失败: {e}")
EOF
else
    echo "⚠️  radon未安装，跳过复杂度收集"
    echo "  安装方法: pip install radon"
fi

# 3. 收集技术债务（简化版）
echo ""
echo "收集技术债务..."
python3 << EOF
import json
from datetime import datetime
import subprocess
import os

try:
    # 简化的技术债务收集
    # 实际应该使用专门的工具如SonarQube
    
    debt_items = []
    debt_total = 0
    
    # 检查TODO/FIXME注释作为简单的债务指标
    result = subprocess.run(
        ['grep', '-r', '--include=*.py', 'TODO\\|FIXME', '.'],
        capture_output=True,
        text=True,
        cwd='$PROJECT_ROOT'
    )
    
    todo_count = len(result.stdout.splitlines()) if result.stdout else 0
    
    # 估算债务点数（简化）
    debt_total = todo_count * 2  # 每个TODO/FIXME估算2点
    
    metrics = {
        "timestamp": "$TIMESTAMP",
        "total_debt": debt_total,
        "debt_by_type": {
            "code": debt_total * 0.5,
            "test": debt_total * 0.2,
            "documentation": debt_total * 0.2,
            "architecture": debt_total * 0.1
        },
        "todo_count": todo_count
    }
    
    # 保存到历史记录
    history_file = "$METRICS_DIR/debt-tracking/debt-history.json"
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except:
        history = {"history": []}
    
    history["history"].append(metrics)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"✅ 技术债务数据已保存: {debt_total}点 (TODO/FIXME: {todo_count})")
except Exception as e:
    print(f"⚠️  技术债务数据收集失败: {e}")
EOF

# 4. 收集缺陷密度（从GitHub Issues或本地数据）
echo ""
echo "收集缺陷密度..."
python3 << EOF
import json
from datetime import datetime

try:
    # 简化的缺陷密度收集
    # 实际应该从缺陷跟踪系统获取
    
    metrics = {
        "timestamp": "$TIMESTAMP",
        "total_bugs": 0,
        "bugs_by_severity": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "bug_density": 0.0,
        "open_bugs": 0,
        "fixed_bugs": 0,
        "fix_rate": 0.0
    }
    
    # 保存到历史记录
    history_file = "$METRICS_DIR/bug-density/bug-history.json"
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except:
        history = {"history": []}
    
    history["history"].append(metrics)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print("✅ 缺陷密度数据已保存（需要从缺陷跟踪系统获取实际数据）")
except Exception as e:
    print(f"⚠️  缺陷密度数据收集失败: {e}")
EOF

echo ""
echo "=========================================="
echo "质量指标收集完成"
echo "=========================================="









