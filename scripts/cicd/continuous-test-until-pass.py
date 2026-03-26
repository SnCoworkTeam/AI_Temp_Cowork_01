#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续测试直到所有21个服务测试通过
不停止，直到所有测试通过
稳定版本 - 支持Windows
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

class ContinuousTester:
    def __init__(self):
        self.project_dir = Path(__file__).parent.parent.parent
        self.repo = "PMLiuyubin/enterprise-ai-platform"
        self.workflow = "deploy.yml"
        self.log_dir = Path(os.getenv("TEMP", "/tmp")) / "github-errors"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_iterations = 999  # 几乎无限制
        self.all_services = [
            "api-gateway", "auth-service", "knowledge-base", "metadata-service",
            "workflow-engine", "web-ui", "registry-service", "config-center",
            "sap-mcp-server", "mcp-gateway", "chat-service", "dag-orchestrator",
            "agent-service", "agent-orchestrator", "agent-registry", "joyagent-adapter",
            "memory-service", "sap-metadata-agent", "vector-coordinator-service"
        ]
        self.total_services = len(self.all_services)
        self.is_windows = platform.system() == "Windows"
        
        # 查找gh命令路径
        self.gh_cmd = self._find_gh_command()
        if not self.gh_cmd:
            print("❌ 未找到GitHub CLI (gh)，请确保已安装并添加到PATH")
            print("   安装方法: winget install --id GitHub.cli")
            sys.exit(1)
        
        print(f"✅ 使用GitHub CLI: {self.gh_cmd}")
        
    def _find_gh_command(self):
        """查找gh命令路径"""
        # 首先尝试which/where
        gh_path = shutil.which("gh")
        if gh_path:
            return gh_path
        
        # Windows上尝试常见路径
        if self.is_windows:
            common_paths = [
                r"C:\Program Files\GitHub CLI\gh.exe",
                r"C:\Program Files (x86)\GitHub CLI\gh.exe",
                os.path.expanduser(r"~\AppData\Local\Programs\GitHub CLI\gh.exe"),
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path
            
            # 尝试使用where命令
            try:
                result = subprocess.run(
                    ["where.exe", "gh"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split('\n')[0]
            except:
                pass
        
        return None
    
    def _run_gh_command(self, args, retries=3, delay=5):
        """运行gh命令，带重试机制"""
        cmd = [self.gh_cmd] + args
        
        for attempt in range(retries):
            try:
                if self.is_windows:
                    # Windows上使用shell=True确保能找到命令
                    result = subprocess.run(
                        " ".join([f'"{self.gh_cmd}"'] + [f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in args]),
                        shell=True,
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=300
                    )
                else:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=300
                    )
                return result
            except subprocess.TimeoutExpired:
                print(f"⚠️ 命令超时 (尝试 {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    time.sleep(delay)
            except subprocess.CalledProcessError as e:
                if attempt < retries - 1:
                    print(f"⚠️ 命令失败，重试中... (尝试 {attempt + 1}/{retries})")
                    if e.stderr:
                        print(f"   错误: {e.stderr[:200]}")
                    time.sleep(delay)
                else:
                    raise
            except Exception as e:
                if attempt < retries - 1:
                    print(f"⚠️ 异常，重试中... (尝试 {attempt + 1}/{retries}): {e}")
                    time.sleep(delay)
                else:
                    raise
        
        return None
        
    def start_workflow(self):
        """启动工作流"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 启动工作流...")
        try:
            result = self._run_gh_command([
                "workflow", "run", self.workflow,
                "--field", "environment=staging", "--repo", self.repo
            ])
            
            if result:
                print(f"✅ 工作流已启动")
                time.sleep(5)
                return True
            return False
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False
    
    def get_latest_run_id(self):
        """获取最新运行ID"""
        try:
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
        except Exception as e:
            print(f"❌ 获取运行ID失败: {e}")
            return None, None
    
    def wait_for_completion(self, run_id, max_wait=3600):
        """等待运行完成（最多1小时）"""
        print(f"等待运行完成... (最多{max_wait}秒)")
        
        elapsed = 0
        last_status = None
        
        while elapsed < max_wait:
            try:
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
            except Exception as e:
                print(f"⚠️ 检查状态失败: {e}")
                time.sleep(10)
                elapsed += 10
        
        print("⚠️ 超时")
        return "timeout"
    
    def check_all_jobs_status(self, run_id):
        """检查所有作业的状态"""
        try:
            result = self._run_gh_command([
                "run", "view", run_id, "--repo", self.repo,
                "--json", "jobs"
            ])
            
            if not result or not result.stdout:
                return False, 0, 0
            
            run_info = json.loads(result.stdout)
            jobs = run_info.get("jobs", [])
            
            print(f"\n{'='*60}")
            print(f"作业状态检查 (共 {len(jobs)} 个作业)")
            print(f"{'='*60}")
            
            success_count = 0
            failure_count = 0
            skipped_count = 0
            in_progress_count = 0
            
            for job in jobs:
                name = job.get("name", "Unknown")
                status = job.get("status", "unknown")
                conclusion = job.get("conclusion", "none")
                
                if status == "completed":
                    if conclusion == "success":
                        print(f"✅ {name}")
                        success_count += 1
                    elif conclusion == "failure":
                        print(f"❌ {name}")
                        failure_count += 1
                    elif conclusion == "skipped":
                        print(f"⏭️  {name} (跳过)")
                        skipped_count += 1
                elif status == "in_progress":
                    print(f"🔄 {name} (进行中)")
                    in_progress_count += 1
                else:
                    print(f"⏳ {name} ({status})")
            
            print(f"{'='*60}")
            print(f"成功: {success_count} | 失败: {failure_count} | 跳过: {skipped_count} | 进行中: {in_progress_count}")
            print(f"{'='*60}\n")
            
            # 如果所有作业都完成且没有失败，返回True
            if in_progress_count == 0 and failure_count == 0:
                return True, success_count, failure_count
            return False, success_count, failure_count
            
        except Exception as e:
            print(f"❌ 检查作业状态失败: {e}")
            return False, 0, 0
    
    def download_logs(self, run_id):
        """下载日志"""
        log_dir = self.log_dir / f"run-{run_id}"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        try:
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
            
            return log_dir
        except Exception as e:
            print(f"❌ 下载日志失败: {e}")
            return log_dir
    
    def analyze_errors(self, log_dir):
        """分析错误"""
        errors = []
        
        frontend_logs = list(log_dir.glob("*frontend*.log"))
        frontend_logs += list(log_dir.glob("*Frontend*.log"))
        
        for log_file in frontend_logs:
            try:
                content = log_file.read_text(encoding="utf-8", errors="ignore")
                
                patterns = [
                    r'\./(src/[^:]+):(\d+):(\d+)\s+Type error:\s*(.+)',
                    r'##\[error\](src/[^:]+)\((\d+),(\d+)\):\s+error TS\d+:\s*(.+)',
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        errors.append({
                            "type": "typescript",
                            "file": match.group(1),
                            "line": int(match.group(2)),
                            "message": match.group(4).strip()
                        })
            except Exception as e:
                print(f"⚠️ 分析日志失败 {log_file}: {e}")
        
        return errors
    
    def auto_fix(self, errors):
        """自动修复"""
        if not errors:
            return False
        
        fixed = False
        
        for error in errors:
            file_path = self.project_dir / "web-ui" / error["file"]
            message = error["message"]
            
            if not file_path.exists():
                continue
            
            print(f"修复: {error['file']}:{error['line']}")
            try:
                content = file_path.read_text(encoding="utf-8")
                original_content = content
                
                # 修复User接口字段
                if "does not exist" in message:
                    if error["file"] == "src/lib/api/auth.ts":
                        prop_match = re.search(r"Property '(\w+)'", message)
                        if prop_match:
                            prop_name = prop_match.group(1)
                            if prop_name not in content:
                                content = re.sub(
                                    r'(session_id\?: string)',
                                    f'\\1\n  {prop_name}?: string' if prop_name in ['display_name', 'created_at', 'last_login_at'] else f'\\1\n  {prop_name}?: string[]' if prop_name == 'permissions' else f'\\1\n  {prop_name}?: any',
                                    content
                                )
                                fixed = True
                
                # 修复缺失导入
                match = re.search(r"Cannot find name '(\w+)'", message)
                if match:
                    import_name = match.group(1)
                    if f"from 'lucide-react'" in content or 'from "lucide-react"' in content:
                        if import_name not in content:
                            import_pattern = r"(import\s*\{[^}]+)\}\s*from\s*['\"]lucide-react['\"]"
                            if re.search(import_pattern, content):
                                content = re.sub(
                                    import_pattern,
                                    f"\\1,\n  {import_name}}} from 'lucide-react'",
                                    content
                                )
                                fixed = True
                
                if content != original_content:
                    file_path.write_text(content, encoding="utf-8")
                    print(f"  ✅ 已修复")
            except Exception as e:
                print(f"  ❌ 修复失败: {e}")
        
        return fixed
    
    def verify_fixes(self):
        """验证修复"""
        web_ui_dir = self.project_dir / "web-ui"
        original_dir = os.getcwd()
        
        try:
            os.chdir(web_ui_dir)
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return result.returncode == 0
        except Exception as e:
            print(f"⚠️ 验证失败: {e}")
            return False
        finally:
            os.chdir(original_dir)
    
    def commit_and_push(self):
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
            commit_message = f"fix: Auto-fix CI/CD errors - {timestamp}"
            
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
            return True
        except Exception as e:
            print(f"⚠️ 提交失败: {e}")
            return False
    
    def run(self):
        """持续运行直到所有测试通过"""
        print("=" * 60)
        print("持续测试系统 - 直到所有21个服务测试通过")
        print("=" * 60)
        print(f"目标服务数: {self.total_services}")
        print(f"最大迭代次数: {self.max_iterations}")
        print(f"系统: {platform.system()}")
        print("=" * 60)
        print()
        
        iteration = 0
        consecutive_success = 0
        last_error_time = None
        
        while iteration < self.max_iterations:
            iteration += 1
            
            print()
            print("=" * 60)
            print(f"迭代 {iteration} / {self.max_iterations}")
            print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            print()
            
            try:
                # 启动工作流
                if not self.start_workflow():
                    print("跳过本次迭代，等待30秒后重试...")
                    time.sleep(30)
                    continue
                
                # 获取运行ID
                run_id, status = self.get_latest_run_id()
                if not run_id:
                    print("跳过本次迭代，等待30秒后重试...")
                    time.sleep(30)
                    continue
                
                print(f"运行ID: {run_id}")
                
                # 等待完成
                conclusion = self.wait_for_completion(run_id)
                
                # 检查所有作业状态
                all_passed, success_count, failure_count = self.check_all_jobs_status(run_id)
                
                if all_passed:
                    consecutive_success += 1
                    print(f"✅ 所有测试通过！ (连续成功: {consecutive_success})")
                    
                    if consecutive_success >= 2:  # 连续2次成功才真正停止
                        print()
                        print("=" * 60)
                        print("🎉 所有服务测试通过！系统停止。")
                        print("=" * 60)
                        print(f"总迭代次数: {iteration}")
                        print(f"成功作业数: {success_count}")
                        break
                else:
                    consecutive_success = 0
                    last_error_time = datetime.now()
                    
                    # 下载日志
                    log_dir = self.download_logs(run_id)
                    
                    # 分析错误
                    errors = self.analyze_errors(log_dir)
                    
                    if errors:
                        print(f"发现 {len(errors)} 个错误，尝试自动修复...")
                        
                        # 自动修复
                        fixed = self.auto_fix(errors)
                        
                        if fixed:
                            # 验证修复
                            if self.verify_fixes():
                                # 提交并推送
                                if self.commit_and_push():
                                    print("✅ 修复已提交，等待新工作流...")
                                    time.sleep(15)
                                else:
                                    print("⚠️ 无需提交")
                            else:
                                print("❌ 修复验证失败")
                        else:
                            print("⚠️ 无法自动修复，需要手动检查")
                            print(f"日志目录: {log_dir}")
                    else:
                        print("⚠️ 未发现可自动修复的错误")
                        print(f"日志目录: {log_dir}")
                
                # 短暂休息
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n\n用户中断，停止测试")
                break
            except Exception as e:
                print(f"❌ 迭代异常: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(30)  # 异常后等待更长时间
        
        print()
        print("=" * 60)
        print("循环结束")
        print("=" * 60)
        print(f"总迭代次数: {iteration}")
        print(f"日志目录: {self.log_dir}")

if __name__ == "__main__":
    tester = ContinuousTester()
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
