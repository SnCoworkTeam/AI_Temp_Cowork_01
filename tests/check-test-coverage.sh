#!/bin/bash
# 检查测试覆盖情况的脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "测试覆盖情况检查"
echo "=========================================="
echo ""

python3 << 'PYEOF'
import os
from pathlib import Path
from collections import defaultdict

project_root = Path('.')

# 主要服务模块
services = {
    'mcp-gateway': ['src'],
    'workflow-engine': ['src'],
    'auth-service': ['src'],
    'knowledge-base': ['src'],
    'metadata-service': ['src'],
    'database': ['src'],
    'shared_libs': []
}

coverage_report = defaultdict(dict)

print('=' * 70)
print('各服务测试覆盖统计')
print('=' * 70)
print()

total_src_files = 0
total_test_files = 0

for service, src_dirs in services.items():
    service_path = project_root / service
    if not service_path.exists():
        continue
    
    # 统计源代码文件
    src_files = []
    for src_dir in src_dirs:
        src_path = service_path / src_dir
        if src_path.exists():
            for py_file in src_path.rglob('*.py'):
                if '__pycache__' not in str(py_file) and 'test' not in str(py_file):
                    src_files.append(py_file)
    
    # 统计测试文件
    test_path = service_path / 'tests'
    test_files = []
    unit_tests = []
    integration_tests = []
    
    if test_path.exists():
        for test_file in test_path.rglob('test_*.py'):
            test_files.append(test_file)
            if 'unit' in str(test_file):
                unit_tests.append(test_file)
            elif 'integration' in str(test_file):
                integration_tests.append(test_file)
    
    total_src_files += len(src_files)
    total_test_files += len(test_files)
    
    coverage = (len(test_files) / len(src_files) * 100) if src_files else 0
    
    coverage_report[service] = {
        'src_files': len(src_files),
        'test_files': len(test_files),
        'unit_tests': len(unit_tests),
        'integration_tests': len(integration_tests),
        'coverage': coverage
    }
    
    # 输出报告
    status = "✓" if coverage >= 50 else "⚠" if coverage > 0 else "✗"
    print(f'{status} {service:20s} | 源码: {len(src_files):3d} | 测试: {len(test_files):3d} | 单元: {len(unit_tests):2d} | 集成: {len(integration_tests):2d} | 覆盖率: {coverage:5.1f}%')

print()
print('=' * 70)
print('全局测试统计')
print('=' * 70)

global_tests = project_root / 'tests'
if global_tests.exists():
    test_dirs = {
        'test-architecture': '架构测试',
        'test-integration': '集成测试',
        'test-performance': '性能测试',
        'test-security': '安全测试'
    }
    
    for test_dir, desc in test_dirs.items():
        test_path = global_tests / test_dir
        if test_path.exists():
            test_files = list(test_path.glob('test_*.py'))
            print(f'  {desc:10s}: {len(test_files):3d} 个测试文件')

print()
print('=' * 70)
print('总体统计')
print('=' * 70)
overall_coverage = (total_test_files / total_src_files * 100) if total_src_files else 0
print(f'总源代码文件: {total_src_files}')
print(f'总测试文件: {total_test_files}')
print(f'总体覆盖率: {overall_coverage:.1f}%')
print()

# 覆盖率评估
if overall_coverage >= 80:
    print('✓ 测试覆盖率优秀 (>= 80%)')
elif overall_coverage >= 50:
    print('⚠ 测试覆盖率一般 (50-80%)，建议增加测试')
else:
    print('✗ 测试覆盖率不足 (< 50%)，需要大量增加测试')

print()
print('=' * 70)
print('建议')
print('=' * 70)

low_coverage = [s for s, d in coverage_report.items() if d['coverage'] < 50]
if low_coverage:
    print('以下服务测试覆盖率不足，建议优先添加测试:')
    for service in low_coverage:
        print(f'  - {service} ({coverage_report[service]["coverage"]:.1f}%)')
else:
    print('所有服务的测试覆盖率都达到了基本要求！')

PYEOF

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

