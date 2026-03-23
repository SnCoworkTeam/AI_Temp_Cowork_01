#!/usr/bin/env python3
"""
本地测试报告监控脚本
定时从服务器拉取测试报告并分析，可在虚拟环境中运行
"""

import os
import sys
import time
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import json

# 配置
SERVER_IP = "43.143.139.197"
SERVER_USER = "ubuntu"
KEY_PATH = "enterprise_ai_platform.pem"
REMOTE_PATH = "/opt/enterprise-ai-platform"
LOCAL_REPORT_DIR = Path("test-reports-local")
INTERVAL_MINUTES = 30  # 默认30分钟检查一次


class Colors:
    """终端颜色"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'


def print_color(message: str, color: str = Colors.RESET):
    """打印带颜色的消息"""
    print(f"{color}{message}{Colors.RESET}")


def run_command(cmd: List[str], check: bool = False) -> Tuple[int, str, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


def get_test_reports() -> bool:
    """从服务器拉取测试报告"""
    print_color("\n=== 从服务器拉取测试报告 ===", Colors.CYAN)
    
    # 创建本地目录
    LOCAL_REPORT_DIR.mkdir(exist_ok=True)
    (LOCAL_REPORT_DIR / "test-results").mkdir(exist_ok=True)
    (LOCAL_REPORT_DIR / "coverage-report").mkdir(exist_ok=True)
    
    try:
        # 拉取测试结果
        print_color("拉取测试结果...", Colors.YELLOW)
        cmd = [
            "scp", "-i", KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            "-r",
            f"{SERVER_USER}@{SERVER_IP}:{REMOTE_PATH}/test-results",
            str(LOCAL_REPORT_DIR / "test-results")
        ]
        returncode, stdout, stderr = run_command(cmd)
        if returncode != 0:
            print_color(f"⚠️  拉取测试结果时出现警告: {stderr}", Colors.YELLOW)
        
        # 拉取覆盖率报告
        print_color("拉取覆盖率报告...", Colors.YELLOW)
        cmd = [
            "scp", "-i", KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            "-r",
            f"{SERVER_USER}@{SERVER_IP}:{REMOTE_PATH}/coverage-report",
            str(LOCAL_REPORT_DIR / "coverage-report")
        ]
        returncode, stdout, stderr = run_command(cmd)
        if returncode != 0:
            print_color(f"⚠️  拉取覆盖率报告时出现警告: {stderr}", Colors.YELLOW)
        
        # 拉取测试报告Markdown
        print_color("拉取测试报告...", Colors.YELLOW)
        cmd = [
            "scp", "-i", KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            f"{SERVER_USER}@{SERVER_IP}:{REMOTE_PATH}/test-results/test-report.md",
            str(LOCAL_REPORT_DIR / "test-report.md")
        ]
        returncode, stdout, stderr = run_command(cmd)
        if returncode != 0:
            print_color(f"⚠️  拉取测试报告时出现警告: {stderr}", Colors.YELLOW)
        
        print_color(f"✅ 测试报告已拉取到本地: {LOCAL_REPORT_DIR}", Colors.GREEN)
        return True
    except Exception as e:
        print_color(f"❌ 拉取测试报告失败: {e}", Colors.RED)
        return False


def analyze_test_results() -> Tuple[Dict, bool]:
    """分析测试结果"""
    print_color("\n=== 分析测试结果 ===", Colors.CYAN)
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0
    }
    
    failed_tests = []
    
    # 分析JUnit XML报告
    xml_dir = LOCAL_REPORT_DIR / "test-results"
    if xml_dir.exists():
        for xml_file in xml_dir.glob("*-results.xml"):
            print_color(f"分析: {xml_file.name}", Colors.YELLOW)
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # 处理testsuite元素
                for testsuite in root.findall(".//testsuite"):
                    tests = int(testsuite.get("tests", 0))
                    failures = int(testsuite.get("failures", 0))
                    errors = int(testsuite.get("errors", 0))
                    skipped = int(testsuite.get("skipped", 0))
                    
                    results["total"] += tests
                    results["failed"] += failures
                    results["errors"] += errors
                    results["skipped"] += skipped
                    results["passed"] += tests - failures - errors - skipped
                    
                    # 收集失败的测试
                    for testcase in testsuite.findall(".//testcase"):
                        failure = testcase.find("failure")
                        error = testcase.find("error")
                        if failure is not None or error is not None:
                            failed_tests.append({
                                "file": xml_file.name,
                                "name": testcase.get("name", ""),
                                "classname": testcase.get("classname", ""),
                                "message": (failure or error).get("message", "")[:100] if (failure or error) is not None else ""
                            })
            except Exception as e:
                print_color(f"⚠️  解析 {xml_file.name} 失败: {e}", Colors.YELLOW)
    
    # 显示统计
    print_color("\n📊 测试统计:", Colors.BLUE)
    print_color(f"  总计: {results['total']}", Colors.RESET)
    print_color(f"  通过: {results['passed']}", Colors.GREEN)
    print_color(f"  失败: {results['failed']}", Colors.RED)
    print_color(f"  错误: {results['errors']}", Colors.RED)
    print_color(f"  跳过: {results['skipped']}", Colors.YELLOW)
    
    # 计算通过率
    if results["total"] > 0:
        pass_rate = round((results["passed"] / results["total"]) * 100, 2)
        print_color(f"  通过率: {pass_rate}%", Colors.BLUE)
        
        if pass_rate < 80:
            print_color("  ⚠️  通过率低于80%，需要关注！", Colors.YELLOW)
    
    # 显示失败的测试
    if failed_tests:
        print_color("\n❌ 失败的测试:", Colors.RED)
        for test in failed_tests[:10]:  # 只显示前10个
            print_color(f"  - {test['name']} ({test['file']})", Colors.RED)
            if test['message']:
                print_color(f"    错误: {test['message']}", Colors.RED)
        if len(failed_tests) > 10:
            print_color(f"  ... 还有 {len(failed_tests) - 10} 个失败的测试", Colors.YELLOW)
    
    all_passed = results["failed"] == 0 and results["errors"] == 0
    if all_passed:
        print_color("\n✅ 所有测试通过！", Colors.GREEN)
    else:
        print_color(f"\n❌ 发现 {results['failed'] + results['errors']} 个失败的测试！", Colors.RED)
    
    return results, all_passed


def generate_local_report(results: Dict) -> Path:
    """生成本地报告"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = LOCAL_REPORT_DIR / f"test-report-{timestamp}.md"
    
    report = f"""# 测试报告监控结果

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
服务器: {SERVER_IP}

## 测试统计

- **总计**: {results['total']}
- **通过**: {results['passed']}
- **失败**: {results['failed']}
- **错误**: {results['errors']}
- **跳过**: {results['skipped']}
- **通过率**: {round((results['passed'] / results['total'] * 100), 2) if results['total'] > 0 else 0}%

## 详细报告

查看详细报告请访问: {LOCAL_REPORT_DIR / 'test-results'}
查看覆盖率报告请访问: {LOCAL_REPORT_DIR / 'coverage-report'}

"""
    
    # 读取服务器上的测试报告
    server_report = LOCAL_REPORT_DIR / "test-report.md"
    if server_report.exists():
        report += f"\n## 服务器测试报告\n\n"
        report += server_report.read_text(encoding='utf-8')
    
    report_file.write_text(report, encoding='utf-8')
    print_color(f"\n📄 报告已生成: {report_file}", Colors.GREEN)
    
    return report_file


def run_tests_on_server() -> bool:
    """在服务器上运行测试"""
    print_color("\n=== 在服务器上运行测试 ===", Colors.CYAN)
    
    try:
        cmd = [
            "ssh", "-i", KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            f"{SERVER_USER}@{SERVER_IP}",
            f"cd {REMOTE_PATH} && bash scripts/test/run-tests-simple.sh > /tmp/test-run.log 2>&1 &"
        ]
        returncode, stdout, stderr = run_command(cmd)
        
        if returncode == 0:
            print_color("✅ 测试已在服务器后台启动", Colors.GREEN)
            print_color("等待测试完成（60秒）...", Colors.YELLOW)
            time.sleep(60)
            return True
        else:
            print_color(f"❌ 启动测试失败: {stderr}", Colors.RED)
            return False
    except Exception as e:
        print_color(f"❌ 启动测试失败: {e}", Colors.RED)
        return False


def main_loop(run_once: bool = False, run_tests: bool = False):
    """主循环"""
    print_color("=" * 50, Colors.CYAN)
    print_color("🧪 测试报告监控器", Colors.CYAN)
    print_color("=" * 50, Colors.CYAN)
    print_color(f"服务器: {SERVER_IP}", Colors.RESET)
    print_color(f"检查间隔: {INTERVAL_MINUTES} 分钟", Colors.RESET)
    print_color(f"本地报告目录: {LOCAL_REPORT_DIR}", Colors.RESET)
    print_color("=" * 50, Colors.CYAN)
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print_color(f"\n[{timestamp}] 开始检查...", Colors.CYAN)
        
        # 如果需要，先运行测试
        if run_tests:
            run_tests_on_server()
        
        # 拉取报告
        if get_test_reports():
            # 分析结果
            results, all_passed = analyze_test_results()
            
            # 生成本地报告
            generate_local_report(results)
            
            # 如果有失败，返回非零退出码
            if not all_passed:
                print_color("\n⚠️  检测到测试失败，请及时修复！", Colors.YELLOW)
        
        # 如果只运行一次，退出
        if run_once:
            break
        
        # 等待下次检查
        print_color(f"\n⏰ 等待 {INTERVAL_MINUTES} 分钟后再次检查...", Colors.YELLOW)
        time.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试报告监控器")
    parser.add_argument("--once", action="store_true", help="只运行一次，不循环")
    parser.add_argument("--run-tests", action="store_true", help="在检查前先运行测试")
    parser.add_argument("--interval", type=int, default=30, help="检查间隔（分钟）")
    
    args = parser.parse_args()
    
    INTERVAL_MINUTES = args.interval
    
    try:
        main_loop(run_once=args.once, run_tests=args.run_tests)
    except KeyboardInterrupt:
        print_color("\n\n👋 监控已停止", Colors.YELLOW)
        sys.exit(0)

