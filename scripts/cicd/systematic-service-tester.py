#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统性服务测试器 - 逐个服务进行测试
支持分层测试策略，自动化测试闭环
"""

import os
import re
import json
import subprocess
import sys
import time
import shutil
import platform
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class ServiceTester:
    """系统性服务测试器"""

    # 服务分层定义
    SERVICE_LAYERS = {
        "layer1_infrastructure": {
            "name": "基础设施服务",
            "services": ["postgres", "redis", "registry-service", "config-center"],
            "priority": 1,
            "description": "数据库、缓存、服务注册、配置中心"
        },
        "layer2_gateway": {
            "name": "认证与网关服务",
            "services": ["auth-service", "api-gateway"],
            "priority": 2,
            "description": "认证服务和API网关"
        },
        "layer3_core_business": {
            "name": "核心业务服务",
            "services": [
                "metadata-service", "knowledge-base", "workflow-engine",
                "chat-service", "mcp-gateway", "sap-mcp-server"
            ],
            "priority": 3,
            "description": "元数据、知识库、工作流、聊天、MCP"
        },
        "layer4_ai_orchestration": {
            "name": "智能编排服务",
            "services": [
                "agent-service", "agent-orchestrator", "agent-registry",
                "dag-orchestrator", "memory-service"
            ],
            "priority": 4,
            "description": "Agent服务、编排器、DAG、内存管理"
        },
        "layer5_adapters": {
            "name": "扩展与适配服务",
            "services": [
                "joyagent-adapter", "sap-metadata-agent",
                "vector-coordinator-service"
            ],
            "priority": 5,
            "description": "适配器和扩展服务"
        },
        "layer6_frontend": {
            "name": "前端服务",
            "services": ["web-ui"],
            "priority": 6,
            "description": "Web用户界面"
        }
    }

    def __init__(self, mode: str = "layer"):
        """
        初始化测试器

        Args:
            mode: 测试模式
                - "layer": 按层测试（默认）
                - "service": 逐个服务测试
                - "all": 全部服务一起测试
        """
        self.project_dir = Path(__file__).parent.parent.parent
        self.repo = "PMLiuyubin/enterprise-ai-platform"
        self.workflow = "deploy.yml"
        self.log_dir = Path(os.getenv("TEMP", "/tmp")) / "service-test-logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.mode = mode
        self.is_windows = platform.system() == "Windows"
        self.max_iterations_per_service = 3
        self.max_fix_attempts = 5

        # 查找gh命令
        self.gh_cmd = self._find_gh_command()
        if not self.gh_cmd:
            print("❌ 未找到GitHub CLI (gh)，请确保已安装")
            print("   安装方法: winget install --id GitHub.cli")
            sys.exit(1)

        # 测试进度跟踪
        self.progress_file = self.log_dir / "test_progress.json"
        self.progress = self._load_progress()

        print(f"✅ 系统性服务测试器初始化完成")
        print(f"   模式: {mode}")
        print(f"   GitHub CLI: {self.gh_cmd}")
        print(f"   日志目录: {self.log_dir}")

    def _find_gh_command(self) -> Optional[str]:
        """查找gh命令路径"""
        gh_path = shutil.which("gh")
        if gh_path:
            return gh_path

        if self.is_windows:
            common_paths = [
                r"C:\Program Files\GitHub CLI\gh.exe",
                r"C:\Program Files (x86)\GitHub CLI\gh.exe",
                os.path.expanduser(r"~\AppData\Local\Programs\GitHub CLI\gh.exe"),
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path

        return None

    def _load_progress(self) -> Dict:
        """加载测试进度"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass

        return {
            "current_layer": "layer1_infrastructure",
            "current_service": None,
            "completed_services": [],
            "failed_services": [],
            "test_results": {},
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }

    def _save_progress(self):
        """保存测试进度"""
        self.progress["last_update"] = datetime.now().isoformat()
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)

    def _run_gh_command(self, args: List[str], retries: int = 3) -> Optional[subprocess.CompletedProcess]:
        """运行gh命令"""
        for attempt in range(retries):
            try:
                if self.is_windows:
                    cmd = " ".join([f'"{self.gh_cmd}"'] + [f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in args])
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True,
                        text=True, check=True, timeout=300
                    )
                else:
                    result = subprocess.run(
                        [self.gh_cmd] + args,
                        capture_output=True, text=True,
                        check=True, timeout=300
                    )
                return result
            except subprocess.TimeoutExpired:
                if attempt < retries - 1:
                    print(f"⚠️ 命令超时，重试 ({attempt + 1}/{retries})")
                    time.sleep(5)
            except subprocess.CalledProcessError as e:
                if attempt < retries - 1:
                    print(f"⚠️ 命令失败，重试 ({attempt + 1}/{retries})")
                    time.sleep(5)
                else:
                    print(f"❌ 命令执行失败: {e.stderr if e.stderr else str(e)}")
        return None

    def start_workflow(self) -> bool:
        """启动工作流"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 启动测试工作流...")
        result = self._run_gh_command([
            "workflow", "run", self.workflow,
            "--field", "environment=staging",
            "--repo", self.repo
        ])

        if result:
            print("✅ 工作流已启动")
            time.sleep(5)
            return True
        return False

    def get_latest_run_id(self) -> Tuple[Optional[str], Optional[str]]:
        """获取最新运行ID"""
        result = self._run_gh_command([
            "run", "list", "--workflow", self.workflow,
            "--repo", self.repo, "--limit", "1",
            "--json", "databaseId,status,conclusion"
        ])

        if result and result.stdout:
            runs = json.loads(result.stdout)
            if runs:
                run = runs[0]
                return str(run["databaseId"]), run["status"]
        return None, None

    def wait_for_completion(self, run_id: str, max_wait: int = 3600) -> str:
        """等待运行完成"""
        print(f"等待运行完成 (运行ID: {run_id})...")

        elapsed = 0
        last_status = None

        while elapsed < max_wait:
            result = self._run_gh_command([
                "run", "view", run_id, "--repo", self.repo,
                "--json", "status,conclusion"
            ])

            if result and result.stdout:
                run_info = json.loads(result.stdout)
                status = run_info["status"]

                if status != last_status:
                    print(f"  状态: {status} (已等待 {elapsed}s)")
                    last_status = status

                if status == "completed":
                    conclusion = run_info["conclusion"]
                    color = "✅" if conclusion == "success" else "❌"
                    print(f"{color} 运行完成，结果: {conclusion}")
                    return conclusion

            time.sleep(10)
            elapsed += 10

        print("⚠️ 等待超时")
        return "timeout"

    def download_logs(self, run_id: str) -> Path:
        """下载日志"""
        print("下载测试日志...")

        log_dir = self.log_dir / f"run-{run_id}"
        log_dir.mkdir(parents=True, exist_ok=True)

        # 获取所有作业
        result = self._run_gh_command([
            "run", "view", run_id, "--repo", self.repo,
            "--json", "jobs", "--jq", ".jobs[] | .name"
        ])

        if not result or not result.stdout:
            return log_dir

        jobs = [j for j in result.stdout.strip().split('\n') if j]

        for job in jobs:
            safe_name = re.sub(r'[<>:"/\\|?*$]', '_', job)
            log_file = log_dir / f"{safe_name}.log"

            try:
                log_result = self._run_gh_command([
                    "run", "view", run_id, "--repo", self.repo,
                    "--log", "--job", job
                ])

                if log_result and log_result.stdout:
                    with open(log_file, "w", encoding="utf-8") as f:
                        f.write(log_result.stdout)
            except Exception as e:
                print(f"⚠️ 下载日志失败 {job}: {e}")

        print(f"✅ 日志已保存: {log_dir}")
        return log_dir

    def analyze_service_errors(self, log_dir: Path, service: str) -> List[Dict]:
        """分析特定服务的错误"""
        print(f"分析服务 {service} 的错误...")

        errors = []

        # 查找相关日志
        service_logs = list(log_dir.glob(f"*{service}*.log"))
        service_logs += list(log_dir.glob("*Build*.log"))
        service_logs += list(log_dir.glob("*frontend*.log"))

        for log_file in service_logs:
            try:
                content = log_file.read_text(encoding="utf-8", errors="ignore")

                # TypeScript 错误
                ts_patterns = [
                    r'\./(src/[^:]+):(\d+):(\d+)\s+Type error:\s*(.+)',
                    r'##\[error\](src/[^:]+)\((\d+),(\d+)\):\s+error TS\d+:\s*(.+)',
                ]

                for pattern in ts_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        errors.append({
                            "type": "typescript",
                            "service": service,
                            "file": match.group(1),
                            "line": int(match.group(2)),
                            "message": match.group(4).strip()
                        })

                # Docker 构建错误
                if "ERROR" in content or "Failed" in content:
                    docker_pattern = r'ERROR \[.*?\] (.+)'
                    matches = re.finditer(docker_pattern, content)
                    for match in matches:
                        errors.append({
                            "type": "docker",
                            "service": service,
                            "message": match.group(1).strip()
                        })

                # Python 错误
                py_pattern = r'([\w/]+\.py):(\d+): (.+)'
                matches = re.finditer(py_pattern, content)
                for match in matches:
                    errors.append({
                        "type": "python",
                        "service": service,
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "message": match.group(3).strip()
                    })

            except Exception as e:
                print(f"⚠️ 分析日志失败 {log_file}: {e}")

        if errors:
            print(f"❌ 发现 {len(errors)} 个错误")
            for error in errors[:5]:  # 只显示前5个
                print(f"   - {error.get('file', 'unknown')}: {error['message'][:80]}")
        else:
            print("✅ 未发现错误")

        return errors

    def auto_fix_errors(self, errors: List[Dict]) -> bool:
        """自动修复错误"""
        if not errors:
            return False

        print(f"尝试自动修复 {len(errors)} 个错误...")

        fixed_count = 0

        for error in errors:
            if error["type"] == "typescript":
                if self._fix_typescript_error(error):
                    fixed_count += 1
            elif error["type"] == "python":
                if self._fix_python_error(error):
                    fixed_count += 1

        if fixed_count > 0:
            print(f"✅ 成功修复 {fixed_count} 个错误")
            return True

        print("⚠️ 未能自动修复错误")
        return False

    def _fix_typescript_error(self, error: Dict) -> bool:
        """修复 TypeScript 错误"""
        file_path = self.project_dir / "web-ui" / error["file"]
        if not file_path.exists():
            return False

        try:
            content = file_path.read_text(encoding="utf-8")
            original = content
            message = error["message"]

            # 修复缺失属性
            if "does not exist" in message:
                prop_match = re.search(r"Property '(\w+)'", message)
                if prop_match:
                    prop_name = prop_match.group(1)
                    if prop_name not in content:
                        content = re.sub(
                            r'(session_id\?: string)',
                            f'\\1\n  {prop_name}?: any',
                            content
                        )

            # 修复缺失导入
            elif "Cannot find name" in message:
                name_match = re.search(r"Cannot find name '(\w+)'", message)
                if name_match:
                    import_name = name_match.group(1)
                    if "lucide-react" in content and import_name not in content:
                        pattern = r"(import\s*\{[^}]+)\}\s*from\s*['\"]lucide-react['\"]"
                        content = re.sub(
                            pattern,
                            f"\\1, {import_name}}} from 'lucide-react'",
                            content
                        )

            if content != original:
                file_path.write_text(content, encoding="utf-8")
                print(f"  ✅ 已修复: {error['file']}")
                return True

        except Exception as e:
            print(f"  ❌ 修复失败: {e}")

        return False

    def _fix_python_error(self, error: Dict) -> bool:
        """修复 Python 错误"""
        # 简单的 Python 错误修复（可扩展）
        return False

    def verify_fixes(self) -> bool:
        """验证修复"""
        print("验证修复...")

        web_ui_dir = self.project_dir / "web-ui"
        if not web_ui_dir.exists():
            return True

        original_dir = os.getcwd()

        try:
            os.chdir(web_ui_dir)
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print("✅ TypeScript 检查通过")
                return True
            else:
                print("❌ TypeScript 检查失败")
                return False
        except Exception as e:
            print(f"⚠️ 验证失败: {e}")
            return False
        finally:
            os.chdir(original_dir)

    def commit_and_push(self, service: str) -> bool:
        """提交并推送"""
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if not result.stdout.strip():
                return False

            subprocess.run(["git", "add", "-A"], check=True, timeout=60)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"fix: Auto-fix {service} CI/CD errors - {timestamp}"

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True,
                timeout=60
            )

            subprocess.run(
                ["git", "push", "origin", "main"],
                check=True,
                timeout=120
            )

            print(f"✅ 已提交并推送修复: {service}")
            return True
        except Exception as e:
            print(f"⚠️ 提交失败: {e}")
            return False

    def test_service(self, service: str) -> Dict:
        """测试单个服务"""
        print("\n" + "=" * 70)
        print(f"测试服务: {service}")
        print("=" * 70)

        result = {
            "service": service,
            "status": "pending",
            "iterations": 0,
            "errors": [],
            "fixed": False,
            "start_time": datetime.now().isoformat()
        }

        for iteration in range(1, self.max_iterations_per_service + 1):
            print(f"\n--- 迭代 {iteration}/{self.max_iterations_per_service} ---")
            result["iterations"] = iteration

            # 启动工作流
            if not self.start_workflow():
                continue

            # 获取运行ID
            run_id, status = self.get_latest_run_id()
            if not run_id:
                continue

            # 等待完成
            conclusion = self.wait_for_completion(run_id)

            # 下载日志
            log_dir = self.download_logs(run_id)

            # 分析错误
            errors = self.analyze_service_errors(log_dir, service)
            result["errors"] = errors

            if conclusion == "success" and not errors:
                result["status"] = "passed"
                result["end_time"] = datetime.now().isoformat()
                print(f"✅ {service} 测试通过！")
                return result

            # 尝试修复
            if errors and iteration < self.max_iterations_per_service:
                if self.auto_fix_errors(errors):
                    result["fixed"] = True

                    if self.verify_fixes():
                        if self.commit_and_push(service):
                            print("等待新工作流启动...")
                            time.sleep(15)
                            continue

                print("⚠️ 无法自动修复，需要人工介入")
                break

        result["status"] = "failed"
        result["end_time"] = datetime.now().isoformat()
        return result

    def test_layer(self, layer_key: str) -> Dict:
        """测试一个服务层"""
        layer = self.SERVICE_LAYERS[layer_key]

        print("\n" + "=" * 70)
        print(f"测试层级: {layer['name']}")
        print(f"服务列表: {', '.join(layer['services'])}")
        print(f"描述: {layer['description']}")
        print("=" * 70)

        results = {
            "layer": layer_key,
            "name": layer["name"],
            "services": layer["services"],
            "test_results": [],
            "passed": 0,
            "failed": 0,
            "start_time": datetime.now().isoformat()
        }

        for service in layer["services"]:
            # 跳过已完成的服务
            if service in self.progress["completed_services"]:
                print(f"⏭️  跳过已完成的服务: {service}")
                continue

            self.progress["current_service"] = service
            self._save_progress()

            # 测试服务
            service_result = self.test_service(service)
            results["test_results"].append(service_result)

            if service_result["status"] == "passed":
                results["passed"] += 1
                self.progress["completed_services"].append(service)
            else:
                results["failed"] += 1
                self.progress["failed_services"].append(service)

            self.progress["test_results"][service] = service_result
            self._save_progress()

        results["end_time"] = datetime.now().isoformat()
        return results

    def run(self):
        """运行系统性测试"""
        print("=" * 70)
        print("系统性服务测试器")
        print("=" * 70)
        print(f"测试模式: {self.mode}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        if self.mode == "layer":
            # 按层测试
            for layer_key in sorted(self.SERVICE_LAYERS.keys()):
                layer_result = self.test_layer(layer_key)

                print("\n" + "=" * 70)
                print(f"层级 {layer_result['name']} 测试完成")
                print(f"通过: {layer_result['passed']}/{len(layer_result['services'])}")
                print(f"失败: {layer_result['failed']}/{len(layer_result['services'])}")
                print("=" * 70)

                # 如果有失败，询问是否继续
                if layer_result['failed'] > 0:
                    response = input("\n有服务测试失败，是否继续下一层？(y/n): ")
                    if response.lower() != 'y':
                        break

        elif self.mode == "all":
            # 全部服务一起测试
            all_services = []
            for layer in self.SERVICE_LAYERS.values():
                all_services.extend(layer["services"])

            for service in all_services:
                if service in self.progress["completed_services"]:
                    continue

                self.test_service(service)

        # 最终报告
        self._print_final_report()

    def _print_final_report(self):
        """打印最终报告"""
        print("\n" + "=" * 70)
        print("测试报告")
        print("=" * 70)

        total_services = len(self.progress["completed_services"]) + len(self.progress["failed_services"])

        print(f"总服务数: {total_services}")
        print(f"通过: {len(self.progress['completed_services'])}")
        print(f"失败: {len(self.progress['failed_services'])}")

        if self.progress["completed_services"]:
            print("\n✅ 通过的服务:")
            for service in self.progress["completed_services"]:
                print(f"   - {service}")

        if self.progress["failed_services"]:
            print("\n❌ 失败的服务:")
            for service in self.progress["failed_services"]:
                print(f"   - {service}")

        print(f"\n进度文件: {self.progress_file}")
        print(f"日志目录: {self.log_dir}")
        print("=" * 70)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="系统性服务测试器")
    parser.add_argument(
        "--mode",
        choices=["layer", "service", "all"],
        default="layer",
        help="测试模式: layer(按层), service(逐个), all(全部)"
    )

    args = parser.parse_args()

    tester = ServiceTester(mode=args.mode)

    try:
        tester.run()
    except KeyboardInterrupt:
        print("\n\n用户中断，停止测试")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n系统异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
