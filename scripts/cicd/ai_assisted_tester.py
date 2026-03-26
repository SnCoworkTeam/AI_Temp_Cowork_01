#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI辅助的CI/CD自动化测试器
支持Claude Code协作的测试闭环
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

class AIAssistedTester:
    """AI辅助的测试器 - 支持Claude Code协作"""

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

    def __init__(self, mode: str = "layer", enable_ai_assist: bool = True):
        """
        初始化测试器

        Args:
            mode: 测试模式 (layer/service/all)
            enable_ai_assist: 是否启用AI辅助(Claude Code协作)
        """
        self.project_dir = Path(__file__).parent.parent.parent
        self.repo = "PMLiuyubin/enterprise-ai-platform"
        self.workflow = "deploy.yml"
        self.log_dir = Path(os.getenv("TEMP", "/tmp")) / "ai-assisted-test-logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.mode = mode
        self.enable_ai_assist = enable_ai_assist
        self.is_windows = platform.system() == "Windows"
        self.max_iterations_per_service = 5
        self.max_fix_attempts = 3

        # 查找gh命令
        self.gh_cmd = self._find_gh_command()
        if not self.gh_cmd:
            print("❌ 未找到GitHub CLI (gh)，请确保已安装")
            print("   安装方法: winget install --id GitHub.cli")
            sys.exit(1)

        # 测试进度跟踪
        self.progress_file = self.log_dir / "test_progress.json"
        self.progress = self._load_progress()

        print(f"✅ AI辅助测试器初始化完成")
        print(f"   模式: {mode}")
        print(f"   AI辅助: {'启用' if enable_ai_assist else '禁用'}")
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
            "ai_fix_stats": {
                "total_fixes": 0,
                "successful_fixes": 0,
                "failed_fixes": 0
            },
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

    def analyze_errors(self, log_dir: Path, service: Optional[str] = None) -> List[Dict]:
        """分析错误 - 增强版本"""
        print(f"分析错误{f' (服务: {service})' if service else ''}...")

        errors = []

        # 查找相关日志
        if service:
            log_files = list(log_dir.glob(f"*{service}*.log"))
            log_files += list(log_dir.glob("*Build*.log"))
            log_files += list(log_dir.glob("*frontend*.log"))
        else:
            log_files = list(log_dir.glob("*.log"))

        for log_file in log_files:
            try:
                content = log_file.read_text(encoding="utf-8", errors="ignore")

                # TypeScript 错误
                ts_patterns = [
                    r'(src/[^:]+):(\d+):(\d+)\s+-\s+error\s+TS(\d+):\s*(.+)',
                    r'##\[error\](src/[^:]+)\((\d+),(\d+)\):\s+error TS(\d+):\s*(.+)',
                ]

                for pattern in ts_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        error_info = {
                            "type": "typescript",
                            "service": service or "unknown",
                            "file": match.group(1),
                            "line": int(match.group(2)),
                            "column": int(match.group(3)),
                            "ts_code": match.group(4),
                            "message": match.group(5).strip(),
                            "log_file": str(log_file),
                            "fixable": self._is_fixable_typescript_error(match.group(5))
                        }

                        # 提取代码上下文
                        error_info['context'] = self._extract_code_context(
                            self.project_dir / "web-ui" / error_info['file'],
                            error_info['line']
                        )

                        errors.append(error_info)

                # Docker 构建错误
                if "ERROR" in content or "Failed" in content:
                    docker_pattern = r'ERROR \[.*?\] (.+)'
                    matches = re.finditer(docker_pattern, content)
                    for match in matches:
                        errors.append({
                            "type": "docker",
                            "service": service or "unknown",
                            "message": match.group(1).strip(),
                            "log_file": str(log_file),
                            "fixable": False
                        })

                # Python 错误
                py_pattern = r'([\w/]+\.py):(\d+): (.+)'
                matches = re.finditer(py_pattern, content)
                for match in matches:
                    errors.append({
                        "type": "python",
                        "service": service or "unknown",
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "message": match.group(3).strip(),
                        "log_file": str(log_file),
                        "fixable": False
                    })

            except Exception as e:
                print(f"⚠️ 分析日志失败 {log_file}: {e}")

        # 去重
        unique_errors = []
        seen = set()
        for error in errors:
            key = (error.get('file', ''), error.get('line', 0), error['message'])
            if key not in seen:
                seen.add(key)
                unique_errors.append(error)

        if unique_errors:
            print(f"❌ 发现 {len(unique_errors)} 个错误")
            for i, error in enumerate(unique_errors[:5], 1):
                fixable_tag = "🔧" if error.get('fixable') else ""
                print(f"   {i}. {fixable_tag} [{error['type']}] {error.get('file', 'unknown')}: {error['message'][:80]}")
            if len(unique_errors) > 5:
                print(f"   ... 还有 {len(unique_errors) - 5} 个错误")
        else:
            print("✅ 未发现错误")

        return unique_errors

    def _is_fixable_typescript_error(self, message: str) -> bool:
        """判断TypeScript错误是否可自动修复"""
        fixable_patterns = [
            "Cannot find name",
            "Property .* does not exist",
            "Type .* is not assignable to type",
            "Module .* has no exported member",
            "Expected",
        ]
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in fixable_patterns)

    def _extract_code_context(self, file_path: Path, line: int, context_lines: int = 3) -> str:
        """提取代码上下文"""
        if not file_path.exists():
            return ""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start = max(0, line - context_lines - 1)
            end = min(len(lines), line + context_lines)

            context = []
            for i in range(start, end):
                prefix = "→" if i == line - 1 else " "
                context.append(f"{prefix} {i+1:4d} | {lines[i].rstrip()}")

            return "\n".join(context)
        except:
            return ""

    def generate_claude_report(self, errors: List[Dict], log_dir: Path, iteration: int, service: Optional[str] = None) -> Path:
        """生成Claude Code错误报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        service_tag = f"_{service}" if service else ""
        report_file = self.log_dir / f"claude_report_iter_{iteration}{service_tag}_{timestamp}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Claude Code错误修复报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**迭代次数**: {iteration}\n")
            if service:
                f.write(f"**目标服务**: {service}\n")
            f.write(f"**错误总数**: {len(errors)}\n")
            f.write(f"**日志目录**: {log_dir}\n")

            # 错误统计
            error_types = {}
            fixable_count = 0
            for error in errors:
                error_type = error['type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
                if error.get('fixable'):
                    fixable_count += 1

            f.write(f"\n## 📊 错误统计\n\n")
            for error_type, count in error_types.items():
                f.write(f"- **{error_type}**: {count} 个\n")
            f.write(f"- **可自动修复**: {fixable_count} 个\n")
            f.write(f"- **需要仔细分析**: {len(errors) - fixable_count} 个\n")

            f.write(f"\n## 🔍 错误详情\n\n")

            # 按优先级排序: 可修复的在前
            sorted_errors = sorted(errors, key=lambda e: (not e.get('fixable', False), e['type']))

            for i, error in enumerate(sorted_errors, 1):
                fixable_tag = "🔧 可修复" if error.get('fixable') else "⚠️ 需要分析"
                f.write(f"### 错误 {i}: {fixable_tag} [{error['type']}]\n\n")

                if error.get('file'):
                    # 相对路径
                    rel_path = error['file']
                    if error['type'] == 'typescript':
                        full_path = f"web-ui/{rel_path}"
                    else:
                        full_path = rel_path

                    f.write(f"- **文件**: [{full_path}](../{full_path})\n")
                    if error.get('line'):
                        f.write(f"- **位置**: 行 {error['line']}")
                        if error.get('column'):
                            f.write(f", 列 {error['column']}")
                        f.write(f"\n")

                f.write(f"- **错误消息**:\n")
                f.write(f"  ```\n")
                f.write(f"  {error['message']}\n")
                f.write(f"  ```\n\n")

                if error.get('context'):
                    f.write(f"- **代码上下文**:\n")
                    f.write(f"  ```typescript\n")
                    f.write(f"  {error['context']}\n")
                    f.write(f"  ```\n\n")

                # 修复建议
                if error['type'] == 'typescript':
                    f.write(f"- **修复建议**:\n")
                    message = error['message']

                    if "Cannot find name" in message:
                        name_match = re.search(r"Cannot find name '(\w+)'", message)
                        if name_match:
                            name = name_match.group(1)
                            f.write(f"  1. 检查是否需要导入 `{name}`\n")
                            f.write(f"  2. 如果是React组件,添加导入: `import {{ {name} }} from 'lucide-react'`\n")
                            f.write(f"  3. 如果是类型,添加类型导入\n")

                    elif "does not exist" in message:
                        prop_match = re.search(r"Property '(\w+)'", message)
                        if prop_match:
                            prop = prop_match.group(1)
                            f.write(f"  1. 在接口中添加属性定义: `{prop}?: any`\n")
                            f.write(f"  2. 或检查属性名是否拼写正确\n")

                    elif "not assignable" in message:
                        f.write(f"  1. 检查类型定义是否匹配\n")
                        f.write(f"  2. 考虑使用类型断言或类型保护\n")
                        f.write(f"  3. 更新接口定义以匹配实际类型\n")

                f.write(f"\n---\n\n")

            f.write(f"\n## 🎯 修复步骤\n\n")
            f.write(f"### 方式一: 使用Claude Code (推荐)\n\n")
            f.write(f"1. **在Claude Code中运行以下提示词**:\n\n")
            f.write(f"```\n")
            f.write(f"请帮我修复这个错误报告中的所有错误。\n\n")
            f.write(f"错误报告文件: {report_file}\n\n")
            f.write(f"请按以下步骤操作:\n")
            f.write(f"1. 阅读上面的错误报告,理解所有错误\n")
            f.write(f"2. 优先处理标记为'可修复'的错误\n")
            f.write(f"3. 对每个错误:\n")
            f.write(f"   - 使用Read工具读取相关文件\n")
            f.write(f"   - 分析错误的根本原因\n")
            f.write(f"   - 使用Edit工具进行修复\n")
            f.write(f"   - 确保修复不引入新问题\n")
            f.write(f"4. 修复完成后,运行验证命令\n")
            f.write(f"5. 如果验证通过,提交代码\n")
            f.write(f"```\n\n")

            f.write(f"2. **等待Claude Code完成修复**\n\n")
            f.write(f"3. **验证修复结果**\n\n")

            f.write(f"### 方式二: 手动修复\n\n")
            f.write(f"如果某些错误无法自动修复,可以手动修复:\n\n")
            f.write(f"1. 根据上面的错误详情和修复建议\n")
            f.write(f"2. 在IDE中打开相关文件\n")
            f.write(f"3. 根据错误消息进行修复\n")
            f.write(f"4. 运行验证命令\n\n")

            f.write(f"\n## ✅ 验证命令\n\n")
            f.write(f"修复完成后,运行以下命令验证:\n\n")
            f.write(f"```bash\n")
            f.write(f"# TypeScript类型检查\n")
            f.write(f"cd web-ui\n")
            f.write(f"npx tsc --noEmit\n\n")
            f.write(f"# ESLint检查\n")
            f.write(f"npm run lint\n\n")
            f.write(f"# 构建测试\n")
            f.write(f"npm run build\n\n")
            f.write(f"# Python测试 (如果有Python错误)\n")
            f.write(f"cd ..\n")
            f.write(f"pytest tests/ -v --maxfail=5\n")
            f.write(f"```\n\n")

            f.write(f"\n## 📝 提交代码\n\n")
            f.write(f"验证通过后,提交代码:\n\n")
            f.write(f"```bash\n")
            f.write(f"git add -A\n")
            f.write(f"git commit -m \"fix: AI-assisted fixes for iteration {iteration}\"\n")
            f.write(f"git push origin main\n")
            f.write(f"```\n\n")

            f.write(f"\n## 🔄 继续测试\n\n")
            f.write(f"代码提交后,返回Python脚本终端,按Enter继续下一轮测试。\n")

        print(f"✅ Claude Code报告已生成: {report_file}")
        return report_file

    def wait_for_user_fix(self, report_file: Path) -> bool:
        """等待用户使用Claude Code修复"""
        print(f"\n{'='*70}")
        print(f"🤖 需要Claude Code协助修复")
        print(f"{'='*70}")
        print(f"错误报告: {report_file}")
        print(f"\n请在Claude Code中:")
        print(f"1. 打开错误报告文件")
        print(f"2. 将报告内容提供给Claude Code")
        print(f"3. 让Claude Code分析并修复错误")
        print(f"4. 修复完成后,按Enter继续...")
        print(f"{'='*70}\n")

        try:
            input("按Enter继续,或Ctrl+C中断...")
            return True
        except KeyboardInterrupt:
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

            # 1. 启动工作流
            if not self.start_workflow():
                continue

            # 2. 获取运行ID
            run_id, status = self.get_latest_run_id()
            if not run_id:
                continue

            # 3. 等待完成
            conclusion = self.wait_for_completion(run_id)

            # 4. 下载日志
            log_dir = self.download_logs(run_id)

            # 5. 分析错误
            errors = self.analyze_errors(log_dir, service)
            result["errors"] = errors

            if conclusion == "success" and not errors:
                result["status"] = "passed"
                result["end_time"] = datetime.now().isoformat()
                print(f"✅ {service} 测试通过！")
                return result

            # 6. 生成Claude Code报告
            if errors and iteration < self.max_iterations_per_service:
                report_file = self.generate_claude_report(errors, log_dir, iteration, service)

                if self.enable_ai_assist:
                    # 等待用户使用Claude Code修复
                    if not self.wait_for_user_fix(report_file):
                        print("⚠️ 用户中断,停止测试")
                        break

                    # 更新AI修复统计
                    self.progress["ai_fix_stats"]["total_fixes"] += 1
                    self._save_progress()

                    print("等待新工作流启动...")
                    time.sleep(15)
                    continue
                else:
                    print(f"⚠️ AI辅助已禁用,请手动修复错误后重新运行")
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
                self.progress["ai_fix_stats"]["successful_fixes"] += 1
            else:
                results["failed"] += 1
                self.progress["failed_services"].append(service)
                self.progress["ai_fix_stats"]["failed_fixes"] += 1

            self.progress["test_results"][service] = service_result
            self._save_progress()

        results["end_time"] = datetime.now().isoformat()
        return results

    def run(self):
        """运行系统性测试"""
        print("=" * 70)
        print("AI辅助的CI/CD自动化测试器")
        print("=" * 70)
        print(f"测试模式: {self.mode}")
        print(f"AI辅助: {'启用' if self.enable_ai_assist else '禁用'}")
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

                # 如果有失败,询问是否继续
                if layer_result['failed'] > 0:
                    try:
                        response = input("\n有服务测试失败,是否继续下一层？(y/n): ")
                        if response.lower() != 'y':
                            break
                    except KeyboardInterrupt:
                        break

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

        # AI修复统计
        ai_stats = self.progress["ai_fix_stats"]
        if ai_stats["total_fixes"] > 0:
            success_rate = (ai_stats["successful_fixes"] / ai_stats["total_fixes"]) * 100
            print(f"\nAI辅助修复统计:")
            print(f"  总修复次数: {ai_stats['total_fixes']}")
            print(f"  成功: {ai_stats['successful_fixes']}")
            print(f"  失败: {ai_stats['failed_fixes']}")
            print(f"  成功率: {success_rate:.1f}%")

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

    parser = argparse.ArgumentParser(description="AI辅助的CI/CD自动化测试器")
    parser.add_argument(
        "--mode",
        choices=["layer", "service", "all"],
        default="layer",
        help="测试模式: layer(按层), service(逐个), all(全部)"
    )
    parser.add_argument(
        "--no-ai-assist",
        action="store_true",
        help="禁用AI辅助(Claude Code协作)"
    )

    args = parser.parse_args()

    tester = AIAssistedTester(
        mode=args.mode,
        enable_ai_assist=not args.no_ai_assist
    )

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
