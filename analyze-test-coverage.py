#!/usr/bin/env python3
"""
分析各服务的测试覆盖率，识别缺失的测试
"""
import os
from pathlib import Path
from collections import defaultdict

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 服务列表
SERVICES = {
    "auth-service": {
        "src": ["src"],
        "exclude": ["__pycache__", "migrations"]
    },
    "knowledge-base": {
        "src": ["src"],
        "exclude": ["__pycache__"]
    },
    "metadata-service": {
        "src": ["src"],
        "exclude": ["__pycache__"]
    },
    "workflow-engine": {
        "src": ["src"],
        "exclude": ["__pycache__"]
    },
    "mcp-gateway": {
        "src": ["src"],
        "exclude": ["__pycache__"]
    },
    "database": {
        "src": ["src"],
        "exclude": ["__pycache__", "migrations"]
    }
}

def get_python_files(directory, exclude_patterns=None):
    """获取目录下所有Python文件"""
    if exclude_patterns is None:
        exclude_patterns = []
    
    files = []
    for root, dirs, filenames in os.walk(directory):
        # 排除目录
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
        
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                files.append(filepath)
    
    return files

def get_module_name(filepath, service_root):
    """获取模块名称"""
    rel_path = os.path.relpath(filepath, service_root)
    module_name = rel_path.replace(os.sep, '.').replace('.py', '')
    return module_name

def analyze_service(service_name, config):
    """分析单个服务的测试覆盖情况"""
    service_path = PROJECT_ROOT / service_name
    
    if not service_path.exists():
        return None
    
    # 获取源代码文件
    src_files = []
    for src_dir in config["src"]:
        src_path = service_path / src_dir
        if src_path.exists():
            files = get_python_files(src_path, config["exclude"])
            src_files.extend(files)
    
    # 获取测试文件
    test_path = service_path / "tests"
    test_files = []
    if test_path.exists():
        test_files = get_python_files(test_path)
    
    # 分析模块覆盖
    src_modules = set()
    for src_file in src_files:
        module = get_module_name(src_file, service_path)
        if module and not module.endswith('__init__'):
            src_modules.add(module)
    
    # 分析测试覆盖的模块
    tested_modules = set()
    for test_file in test_files:
        # 从测试文件名推断被测试的模块
        test_name = os.path.basename(test_file)
        if test_name.startswith('test_'):
            # test_module_name.py -> module_name
            module_name = test_name[5:-3]  # 去掉 'test_' 和 '.py'
            # 尝试匹配源模块
            for src_module in src_modules:
                if module_name in src_module or src_module.endswith(module_name):
                    tested_modules.add(src_module)
    
    # 计算覆盖率
    coverage = (len(tested_modules) / len(src_modules) * 100) if src_modules else 0
    
    return {
        "service": service_name,
        "src_files": len(src_files),
        "src_modules": len(src_modules),
        "test_files": len(test_files),
        "tested_modules": len(tested_modules),
        "coverage": coverage,
        "missing_modules": src_modules - tested_modules
    }

def main():
    """主函数"""
    print("=" * 80)
    print("测试覆盖率分析报告")
    print("=" * 80)
    print()
    
    results = []
    for service_name, config in SERVICES.items():
        result = analyze_service(service_name, config)
        if result:
            results.append(result)
    
    # 打印汇总
    print(f"{'服务':<20} {'源码文件':<10} {'源码模块':<10} {'测试文件':<10} {'已测试模块':<12} {'覆盖率':<10}")
    print("-" * 80)
    
    for result in results:
        status = "✓" if result["coverage"] >= 80 else "⚠" if result["coverage"] >= 50 else "✗"
        print(f"{status} {result['service']:<18} {result['src_files']:<10} {result['src_modules']:<10} "
              f"{result['test_files']:<10} {result['tested_modules']:<12} {result['coverage']:.1f}%")
    
    print()
    print("=" * 80)
    print("需要改进的服务")
    print("=" * 80)
    
    for result in results:
        if result["coverage"] < 80:
            print(f"\n{result['service']} (覆盖率: {result['coverage']:.1f}%)")
            print(f"  缺失测试的模块 ({len(result['missing_modules'])} 个):")
            for module in sorted(result['missing_modules'])[:10]:  # 只显示前10个
                print(f"    - {module}")
            if len(result['missing_modules']) > 10:
                print(f"    ... 还有 {len(result['missing_modules']) - 10} 个模块")
    
    # 生成改进建议
    print()
    print("=" * 80)
    print("改进建议")
    print("=" * 80)
    
    for result in results:
        if result["coverage"] < 80:
            gap = 80 - result["coverage"]
            needed_tests = int((gap / 100) * result["src_modules"])
            print(f"\n{result['service']}:")
            print(f"  当前覆盖率: {result['coverage']:.1f}%")
            print(f"  目标覆盖率: 80%")
            print(f"  需要增加: {gap:.1f}% (约 {needed_tests} 个模块的测试)")
            print(f"  建议优先测试的模块:")
            for module in sorted(result['missing_modules'])[:5]:
                print(f"    - {module}")

if __name__ == "__main__":
    main()

