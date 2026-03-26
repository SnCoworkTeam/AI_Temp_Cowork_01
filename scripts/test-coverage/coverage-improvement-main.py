#!/usr/bin/env python3
"""
测试覆盖率提升主程序
按照计划逐个处理服务，提升测试覆盖率达到80%
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 导入其他模块
_script_path = Path(__file__).resolve()
sys.path.insert(0, str(_script_path.parent))

# 使用importlib动态导入
import importlib.util

def import_module_from_file(module_name, file_path):
    """从文件路径动态导入模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

parse_ssh_config = import_module_from_file("parse_ssh_config", _script_path.parent / "parse-ssh-config.py")
run_command_with_timeout = import_module_from_file("run_command_with_timeout", _script_path.parent / "run-command-with-timeout.py")
check_coverage = import_module_from_file("check_coverage", _script_path.parent / "check-coverage.py")
upload_files_module = import_module_from_file("upload_files", _script_path.parent / "upload-files.py")
improve_coverage = import_module_from_file("improve_coverage", _script_path.parent / "improve-coverage.py")

get_ssh_config = parse_ssh_config.get_ssh_config
run_command_safe = run_command_with_timeout.run_command_safe
check_service_coverage = check_coverage.check_service_coverage
upload_files = upload_files_module.upload_files
upload_service_files = upload_files_module.upload_service_files
improve_service_coverage = improve_coverage.improve_service_coverage
analyze_test_errors = improve_coverage.analyze_test_errors
fix_test_errors = improve_coverage.fix_test_errors
CommandResult = run_command_with_timeout.CommandResult

# 项目根目录
PROJECT_ROOT = _script_path.parent.parent.parent.resolve()

# 服务列表（按依赖顺序）
SERVICES = [
    "database",
    "shared_libs",
    "auth-service",
    "mcp-gateway",
    "workflow-engine",
    "knowledge-base",
    "metadata-service"
]

# 目标覆盖率
TARGET_COVERAGE = 80.0

# 最大循环次数（防止无限循环）
MAX_ITERATIONS = 10


def find_test_files(service_name: str) -> List[Path]:
    """查找服务的测试文件"""
    service_path = PROJECT_ROOT / service_name
    test_files = []
    
    if not service_path.exists():
        return test_files
    
    # 查找所有测试文件
    for test_dir in ["tests", "tests/unit", "tests/integration"]:
        test_path = service_path / test_dir
        if test_path.exists():
            test_files.extend(test_path.rglob("test_*.py"))
    
    return test_files


def find_source_files(service_name: str) -> List[Path]:
    """查找服务的源代码文件"""
    service_path = PROJECT_ROOT / service_name
    source_files = []
    
    if not service_path.exists():
        return source_files
    
    # 查找所有源代码文件
    for src_dir in ["src"]:
        src_path = service_path / src_dir
        if src_path.exists():
            source_files.extend(src_path.rglob("*.py"))
    
    return source_files


def upload_service_test_files(service_name: str, ssh_config: Dict) -> bool:
    """上传服务的测试文件到服务器"""
    test_files = find_test_files(service_name)
    
    if not test_files:
        print(f"  警告: {service_name} 没有找到测试文件")
        return True
    
    file_mappings = []
    for test_file in test_files:
        rel_path = test_file.relative_to(PROJECT_ROOT)
        file_mappings.append({
            "local": str(rel_path),
            "remote": f"/opt/enterprise-ai-platform/{rel_path}".replace("\\", "/")
        })
    
    print(f"  上传 {len(file_mappings)} 个测试文件...")
    results = upload_files(file_mappings, ssh_config, timeout=10)
    
    success_count = sum(1 for r in results.values() if r.success)
    if success_count == len(results):
        print(f"  ✓ 所有测试文件上传成功")
        return True
    else:
        print(f"  ✗ {len(results) - success_count} 个文件上传失败")
        return False


def upload_service_source_files(service_name: str, ssh_config: Dict) -> bool:
    """上传服务的源代码文件到服务器（如果修改了）"""
    source_files = find_source_files(service_name)
    
    if not source_files:
        return True
    
    file_mappings = []
    for src_file in source_files:
        rel_path = src_file.relative_to(PROJECT_ROOT)
        file_mappings.append({
            "local": str(rel_path),
            "remote": f"/opt/enterprise-ai-platform/{rel_path}".replace("\\", "/")
        })
    
    print(f"  上传 {len(file_mappings)} 个源代码文件...")
    results = upload_files.upload_files(file_mappings, ssh_config, timeout=10)
    
    success_count = sum(1 for r in results.values() if r.success)
    return success_count == len(results)


def analyze_missing_coverage(coverage_data: Dict) -> List[str]:
    """分析缺失的覆盖率，返回需要添加测试的文件列表"""
    missing_files = []
    
    files_coverage = coverage_data.get("files", {})
    for file_path, file_data in files_coverage.items():
        file_coverage = file_data.get("coverage", 0.0)
        if file_coverage < TARGET_COVERAGE:
            missing_files.append(file_path)
    
    return missing_files


def process_service(
    service_name: str,
    ssh_config: Dict,
    iteration: int = 0
) -> Dict:
    """
    处理单个服务，提升测试覆盖率
    
    Args:
        service_name: 服务名称
        ssh_config: SSH配置
        iteration: 当前迭代次数
        
    Returns:
        处理结果字典
    """
    print(f"\n{'='*60}")
    print(f"处理服务: {service_name} (迭代 {iteration + 1})")
    print(f"{'='*60}")
    
    # 步骤1: 检查当前覆盖率
    print(f"\n[步骤1] 检查当前覆盖率...")
    coverage_result = check_service_coverage(
        service_name,
        TARGET_COVERAGE,
        ssh_config,
        timeout=120
    )
    
    current_coverage = coverage_result.get("coverage", 0.0)
    meets_target = coverage_result.get("meets_target", False)
    
    print(f"  当前覆盖率: {current_coverage:.2f}%")
    print(f"  目标覆盖率: {TARGET_COVERAGE}%")
    print(f"  是否达标: {'是' if meets_target else '否'}")
    
    if meets_target:
        print(f"\n✓ {service_name} 已达到目标覆盖率！")
        return {
            "service": service_name,
            "status": "SUCCESS",
            "coverage": current_coverage,
            "target": TARGET_COVERAGE,
            "iterations": iteration + 1
        }
    
    # 步骤2: 如果测试失败，先修复测试
    if coverage_result.get("status") == "TEST_FAILED":
        print(f"\n[步骤2] 测试失败，需要修复...")
        test_output = coverage_result.get("test_output", "")
        test_error = coverage_result.get("test_error", "")
        
        print(f"  测试输出: {test_output[:500]}...")
        print(f"  测试错误: {test_error[:500]}...")
        
        # 分析错误
        error_analysis = analyze_test_errors(test_output, test_error)
        print(f"  错误类型: {error_analysis.get('error_types', [])}")
        print(f"  建议: {error_analysis.get('suggestions', [])}")
        
        # 尝试自动修复
        test_files = find_test_files(service_name)
        fixed = False
        for test_file in test_files:
            if fix_test_errors(test_file, error_analysis):
                print(f"  ✓ 已修复: {test_file.name}")
                fixed = True
        
        if fixed:
            # 上传修复后的文件
            print(f"\n[步骤3] 上传修复后的测试文件...")
            upload_service_test_files(service_name, ssh_config)
            
            # 重新运行测试
            return process_service(service_name, ssh_config, iteration + 1)
        else:
            print(f"  ✗ 无法自动修复，需要手动修复")
            return {
                "service": service_name,
                "status": "NEEDS_MANUAL_FIX",
                "coverage": current_coverage,
                "target": TARGET_COVERAGE,
                "error": "测试失败且无法自动修复",
                "iterations": iteration + 1
            }
    
    # 步骤3: 分析缺失的测试
    print(f"\n[步骤3] 分析缺失的测试...")
    coverage_data = coverage_result.get("coverage_data", {})
    missing_files = analyze_missing_coverage(coverage_data)
    
    if missing_files:
        print(f"  发现 {len(missing_files)} 个文件覆盖率不足:")
        for file_path in missing_files[:5]:  # 只显示前5个
            file_data = coverage_data.get("files", {}).get(file_path, {})
            file_cov = file_data.get("coverage", 0.0)
            print(f"    - {file_path}: {file_cov:.2f}%")
        if len(missing_files) > 5:
            print(f"    ... 还有 {len(missing_files) - 5} 个文件")
    
    # 步骤4: 生成测试文件
    print(f"\n[步骤4] 生成测试文件...")
    improve_result = improve_service_coverage(service_name, TARGET_COVERAGE)
    
    if improve_result.get("status") == "SUCCESS":
        created_count = improve_result.get("created_tests", 0)
        if created_count > 0:
            print(f"  ✓ 创建了 {created_count} 个测试文件")
        else:
            print(f"  - 没有需要创建的测试文件")
    else:
        print(f"  ✗ 生成测试文件失败: {improve_result.get('message', '')}")
    
    # 步骤5: 上传文件
    print(f"\n[步骤5] 上传文件到服务器...")
    test_upload_ok = upload_service_test_files(service_name, ssh_config)
    source_upload_ok = upload_service_source_files(service_name, ssh_config)
    
    if not test_upload_ok:
        print(f"  ✗ 测试文件上传失败")
        return {
            "service": service_name,
            "status": "UPLOAD_FAILED",
            "coverage": current_coverage,
            "target": TARGET_COVERAGE,
            "iterations": iteration + 1
        }
    
    # 步骤6: 重新运行测试并检查覆盖率
    if iteration < MAX_ITERATIONS - 1:
        return process_service(service_name, ssh_config, iteration + 1)
    else:
        print(f"\n✗ 达到最大迭代次数 ({MAX_ITERATIONS})，停止处理")
        return {
            "service": service_name,
            "status": "MAX_ITERATIONS",
            "coverage": current_coverage,
            "target": TARGET_COVERAGE,
            "iterations": iteration + 1
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="提升所有服务的测试覆盖率达到80%")
    parser.add_argument("--service", help="只处理指定服务")
    parser.add_argument("--skip", nargs="+", help="跳过的服务列表")
    parser.add_argument("--target", type=float, default=80.0, help="目标覆盖率（默认80%）")
    
    args = parser.parse_args()
    
    global TARGET_COVERAGE
    TARGET_COVERAGE = args.target
    
    # 读取SSH配置
    print("读取SSH配置...")
    try:
        ssh_config = get_ssh_config()
        print(f"✓ SSH配置已加载: {ssh_config.get('hostname')}")
    except Exception as e:
        print(f"✗ 读取SSH配置失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 确定要处理的服务列表
    services_to_process = []
    if args.service:
        services_to_process = [args.service]
    else:
        skip_list = args.skip or []
        services_to_process = [s for s in SERVICES if s not in skip_list]
    
    print(f"\n将处理以下服务: {', '.join(services_to_process)}")
    print(f"目标覆盖率: {TARGET_COVERAGE}%")
    
    # 处理每个服务
    results = {}
    for service_name in services_to_process:
        try:
            result = process_service(service_name, ssh_config)
            results[service_name] = result
        except KeyboardInterrupt:
            print(f"\n\n用户中断")
            break
        except Exception as e:
            print(f"\n✗ 处理 {service_name} 时出错: {e}", file=sys.stderr)
            results[service_name] = {
                "service": service_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    # 生成汇总报告
    print(f"\n{'='*60}")
    print("处理结果汇总")
    print(f"{'='*60}")
    
    success_count = 0
    for service_name, result in results.items():
        status = result.get("status", "UNKNOWN")
        coverage = result.get("coverage", 0.0)
        meets_target = coverage >= TARGET_COVERAGE
        
        status_icon = "✓" if meets_target else "✗"
        print(f"{status_icon} {service_name:20s} | 覆盖率: {coverage:6.2f}% | 状态: {status}")
        
        if meets_target:
            success_count += 1
    
    print(f"\n完成: {success_count}/{len(results)} 个服务达到目标覆盖率")
    
    # 保存结果到文件
    results_file = PROJECT_ROOT / ".coverage-improvement-results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存到: {results_file}")
    
    # 如果所有服务都达标，返回0，否则返回1
    sys.exit(0 if success_count == len(results) else 1)


if __name__ == "__main__":
    main()
