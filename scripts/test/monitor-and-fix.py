#!/usr/bin/env python3
"""
测试监控和自动修复脚本
监控测试报告，发现bug后自动分析并提供修复建议
"""

import os
import sys
import time
import subprocess
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# 配置
SERVER_IP = "43.143.139.197"
SERVER_USER = "ubuntu"
KEY_PATH = "enterprise_ai_platform.pem"
REMOTE_PATH = "/opt/enterprise-ai-platform"
LOCAL_REPORT_DIR = Path("test-reports-local")
FIX_REPORT_DIR = Path("fix-reports")
INTERVAL_MINUTES = 30


class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class TestFailure:
    file: str
    test_name: str
    class_name: str
    message: str
    type: str
    stack_trace: str


@dataclass
class Issue:
    type: str
    severity: Severity
    failure: TestFailure
    fix: str
    auto_fixable: bool
    module: Optional[str] = None
    import_name: Optional[str] = None


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'


def print_color(message: str, color: str = Colors.RESET):
    print(f"{color}{message}{Colors.RESET}")


def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """运行命令"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_test_reports() -> bool:
    """从服务器拉取测试报告"""
    print_color("\n=== 从服务器拉取测试报告 ===", Colors.CYAN)
    
    LOCAL_REPORT_DIR.mkdir(exist_ok=True)
    (LOCAL_REPORT_DIR / "test-results").mkdir(exist_ok=True)
    
    try:
        # 拉取测试结果
        cmd = [
            "scp", "-i", KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            "-r",
            f"{SERVER_USER}@{SERVER_IP}:{REMOTE_PATH}/test-results",
            str(LOCAL_REPORT_DIR / "test-results")
        ]
        returncode, _, stderr = run_command(cmd)
        if returncode != 0:
            print_color(f"⚠️  拉取警告: {stderr}", Colors.YELLOW)
        
        print_color("✅ 测试报告已拉取", Colors.GREEN)
        return True
    except Exception as e:
        print_color(f"❌ 拉取失败: {e}", Colors.RED)
        return False


def analyze_failures() -> List[TestFailure]:
    """分析测试失败"""
    print_color("\n=== 分析测试失败 ===", Colors.CYAN)
    
    failures = []
    xml_dir = LOCAL_REPORT_DIR / "test-results"
    
    if not xml_dir.exists():
        return failures
    
    for xml_file in xml_dir.glob("*-results.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            for testcase in root.findall(".//testcase"):
                failure_elem = testcase.find("failure") or testcase.find("error")
                if failure_elem is not None:
                    failures.append(TestFailure(
                        file=xml_file.name,
                        test_name=testcase.get("name", ""),
                        class_name=testcase.get("classname", ""),
                        message=failure_elem.get("message", ""),
                        type=failure_elem.tag,
                        stack_trace=failure_elem.text or ""
                    ))
        except Exception as e:
            print_color(f"⚠️  解析 {xml_file.name} 失败: {e}", Colors.YELLOW)
    
    return failures


def identify_issues(failures: List[TestFailure]) -> List[Issue]:
    """识别常见问题模式"""
    issues = []
    
    for failure in failures:
        message = failure.message
        stack_trace = failure.stack_trace
        
        # 模式1: ModuleNotFoundError
        match = re.search(r"ModuleNotFoundError.*No module named ['\"](\w+)['\"]", message)
        if match:
            module = match.group(1)
            issues.append(Issue(
                type="MissingModule",
                severity=Severity.HIGH,
                failure=failure,
                fix=f"在requirements.txt中添加 {module}，或在服务器上安装: pip install {module}",
                auto_fixable=True,
                module=module
            ))
            continue
        
        # 模式2: ImportError
        match = re.search(r"ImportError.*cannot import name ['\"](\w+)['\"]", message)
        if match:
            import_name = match.group(1)
            issues.append(Issue(
                type="ImportError",
                severity=Severity.HIGH,
                failure=failure,
                fix=f"检查导入路径和模块结构，确保 {import_name} 正确导入",
                auto_fixable=False,
                import_name=import_name
            ))
            continue
        
        # 模式3: 数据库连接错误
        if re.search(r"connection.*refused|database.*not.*found|authentication.*failed", message, re.IGNORECASE):
            issues.append(Issue(
                type="DatabaseConnection",
                severity=Severity.CRITICAL,
                failure=failure,
                fix="检查数据库服务是否运行，检查连接配置",
                auto_fixable=False
            ))
            continue
        
        # 模式4: 文件不存在
        if re.search(r"No such file or directory|FileNotFoundError", message):
            issues.append(Issue(
                type="FileNotFound",
                severity=Severity.MEDIUM,
                failure=failure,
                fix="检查文件路径，确保文件已同步到服务器",
                auto_fixable=False
            ))
            continue
        
        # 模式5: 断言失败
        if re.search(r"AssertionError|assert.*failed", message):
            issues.append(Issue(
                type="AssertionFailure",
                severity=Severity.MEDIUM,
                failure=failure,
                fix="检查测试逻辑和业务逻辑，修复断言条件",
                auto_fixable=False
            ))
            continue
        
        # 模式6: 超时
        if re.search(r"timeout|timed.*out", message, re.IGNORECASE):
            issues.append(Issue(
                type="Timeout",
                severity=Severity.MEDIUM,
                failure=failure,
                fix="检查服务响应时间，可能需要优化性能或增加超时时间",
                auto_fixable=False
            ))
            continue
        
        # 默认：未知问题
        issues.append(Issue(
            type="Unknown",
            severity=Severity.LOW,
            failure=failure,
            fix="需要手动分析错误信息",
            auto_fixable=False
        ))
    
    return issues


def auto_fix(issues: List[Issue], auto_fix_enabled: bool) -> Tuple[bool, List[str]]:
    """自动修复（仅限安全的问题）"""
    if not auto_fix_enabled:
        print_color("\n⚠️  自动修复已禁用，使用 --auto-fix 参数启用", Colors.YELLOW)
        return False, []
    
    print_color("\n=== 尝试自动修复 ===", Colors.CYAN)
    
    fixed = 0
    fix_actions = []
    
    for issue in issues:
        if issue.auto_fixable and issue.type == "MissingModule" and issue.module:
            print_color(f"修复: 添加缺失模块 {issue.module}", Colors.YELLOW)
            
            # 检查requirements.txt
            req_files = ["requirements.txt", "tests/requirements.txt"]
            for req_file in req_files:
                req_path = Path(req_file)
                if req_path.exists():
                    content = req_path.read_text(encoding='utf-8')
                    if issue.module not in content:
                        req_path.write_text(
                            content + f"\n{issue.module}>=0.0.0  # 自动添加\n",
                            encoding='utf-8'
                        )
                        fix_actions.append(f"在 {req_file} 中添加了 {issue.module}")
                        fixed += 1
                    break
    
    if fixed > 0:
        print_color(f"✅ 已修复 {fixed} 个问题", Colors.GREEN)
        for action in fix_actions:
            print_color(f"  - {action}", Colors.CYAN)
        return True, fix_actions
    else:
        print_color("ℹ️  没有可自动修复的问题", Colors.YELLOW)
        return False, []


def generate_fix_report(failures: List[TestFailure], issues: List[Issue], 
                        fix_actions: List[str]) -> Path:
    """生成修复报告"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = FIX_REPORT_DIR / f"fix-report-{timestamp}.md"
    
    FIX_REPORT_DIR.mkdir(exist_ok=True)
    
    # 按严重程度分组
    critical = [i for i in issues if i.severity == Severity.CRITICAL]
    high = [i for i in issues if i.severity == Severity.HIGH]
    medium = [i for i in issues if i.severity == Severity.MEDIUM]
    low = [i for i in issues if i.severity == Severity.LOW]
    
    auto_fixable_count = sum(1 for i in issues if i.auto_fixable)
    
    report = f"""# Bug修复报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
服务器: {SERVER_IP}

## 📊 失败统计

- **总失败数**: {len(failures)}
- **可自动修复**: {auto_fixable_count}
- **需要手动修复**: {len(issues) - auto_fixable_count}

## 🐛 问题详情

"""
    
    if critical:
        report += "\n### 🔴 严重问题 (Critical)\n\n"
        for issue in critical:
            report += f"""#### {issue.failure.test_name}

- **类型**: {issue.type}
- **测试**: {issue.failure.class_name}::{issue.failure.test_name}
- **错误**: {issue.failure.message[:200]}
- **修复建议**: {issue.fix}
- **自动修复**: {issue.auto_fixable}

"""
    
    if high:
        report += "\n### 🟠 高优先级问题 (High)\n\n"
        for issue in high:
            report += f"""#### {issue.failure.test_name}

- **类型**: {issue.type}
- **修复建议**: {issue.fix}
- **自动修复**: {issue.auto_fixable}

"""
    
    if medium:
        report += "\n### 🟡 中优先级问题 (Medium)\n\n"
        for issue in medium:
            report += f"- **{issue.failure.test_name}**: {issue.fix}\n"
    
    report += "\n## 🔧 修复操作\n\n"
    
    if fix_actions:
        report += "已执行以下自动修复:\n\n"
        for action in fix_actions:
            report += f"- {action}\n"
    else:
        report += "未执行自动修复。请手动修复上述问题。\n"
    
    report += f"""

## 📋 下一步

1. 查看详细错误信息: `{LOCAL_REPORT_DIR}/test-results/`
2. 根据修复建议修复问题
3. 同步代码到服务器
4. 重新运行测试验证修复

---
报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    report_file.write_text(report, encoding='utf-8')
    print_color(f"\n📄 修复报告已生成: {report_file}", Colors.GREEN)
    
    return report_file


def send_notification(issues: List[Issue]):
    """发送通知"""
    if not issues:
        return
    
    critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL)
    high_count = sum(1 for i in issues if i.severity == Severity.HIGH)
    
    print_color(f"\n🔔 发现 {len(issues)} 个问题需要修复！", Colors.RED)
    if critical_count > 0:
        print_color(f"  🔴 严重问题: {critical_count}", Colors.RED)
    if high_count > 0:
        print_color(f"  🟠 高优先级: {high_count}", Colors.YELLOW)


def main_loop(run_once: bool = False, auto_fix: bool = False):
    """主循环"""
    print_color("=" * 50, Colors.CYAN)
    print_color("🐛 Bug监控和修复系统", Colors.CYAN)
    print_color("=" * 50, Colors.CYAN)
    print_color(f"服务器: {SERVER_IP}", Colors.RESET)
    print_color(f"检查间隔: {INTERVAL_MINUTES} 分钟", Colors.RESET)
    print_color(f"自动修复: {auto_fix}", Colors.RESET)
    print_color("=" * 50, Colors.CYAN)
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print_color(f"\n[{timestamp}] 开始检查...", Colors.CYAN)
        
        # 拉取报告
        if get_test_reports():
            # 分析失败
            failures = analyze_failures()
            
            if failures:
                print_color(f"\n❌ 发现 {len(failures)} 个失败的测试", Colors.RED)
                
                # 识别问题
                issues = identify_issues(failures)
                
                # 显示问题摘要
                print_color("\n=== 问题摘要 ===", Colors.CYAN)
                from collections import Counter
                type_counts = Counter(i.type for i in issues)
                for issue_type, count in type_counts.items():
                    print_color(f"  {issue_type}: {count} 个", Colors.YELLOW)
                
                # 尝试自动修复
                fixed, fix_actions = auto_fix(issues, auto_fix)
                
                # 生成修复报告
                report_file = generate_fix_report(failures, issues, fix_actions)
                
                # 发送通知
                send_notification(issues)
                
                print_color(f"\n📋 请查看修复报告: {report_file}", Colors.YELLOW)
            else:
                print_color("\n✅ 所有测试通过！", Colors.GREEN)
        
        if run_once:
            break
        
        print_color(f"\n⏰ 等待 {INTERVAL_MINUTES} 分钟后再次检查...", Colors.YELLOW)
        time.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bug监控和修复系统")
    parser.add_argument("--once", action="store_true", help="只运行一次")
    parser.add_argument("--auto-fix", action="store_true", help="启用自动修复（谨慎使用）")
    parser.add_argument("--interval", type=int, default=30, help="检查间隔（分钟）")
    
    args = parser.parse_args()
    
    INTERVAL_MINUTES = args.interval
    
    try:
        main_loop(run_once=args.once, auto_fix=args.auto_fix)
    except KeyboardInterrupt:
        print_color("\n\n👋 监控已停止", Colors.YELLOW)
        sys.exit(0)

