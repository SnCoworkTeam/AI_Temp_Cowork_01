#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优先测试核心服务，然后按顺序一个服务一个服务的测试

功能：
- 启动CI/CD工作流
- 等待测试完成
- 下载错误日志
- 分析错误（仅显示，不自动修复）
- 提交代码修改（如果有）

注意：此脚本不进行自动修复，修复工作需手动完成
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

class CoreServiceTester:
    def __init__(self):
        self.project_dir = Path(__file__).parent.parent.parent
        self.repo = "PMLiuyubin/enterprise-ai-platform"
        self.workflow = "deploy.yml"
        self.log_dir = Path(os.getenv("TEMP", "/tmp")) / "github-errors"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.is_windows = platform.system() == "Windows"
        
        # 核心服务（优先测试）
        self.core_services = [
            "web-ui",           # 前端 - 最重要
            "api-gateway",      # API网关
            "auth-service",     # 认证服务
            "workflow-engine",  # 工作流引擎
        ]
        
        # 其他服务（按顺序测试）
        self.other_services = [
            "knowledge-base",
            "metadata-service",
            "registry-service",
            "config-center",
            "mcp-gateway",
            "chat-service",
            "dag-orchestrator",
            "agent-service",
            "agent-orchestrator",
            "agent-registry",
            "memory-service",
            "sap-metadata-agent",
            "vector-coordinator-service",
            "sap-mcp-server",
            "joyagent-adapter",
        ]
        
        self.current_service_index = 0
        self.test_phase = "core"  # core 或 other
        
        # 查找gh命令
        self.gh_cmd = self._find_gh_command()
        if not self.gh_cmd:
            print("❌ 未找到GitHub CLI (gh)")
            sys.exit(1)
        
        print(f"✅ 使用GitHub CLI: {self.gh_cmd}")
        print(f"📋 核心服务: {', '.join(self.core_services)}")
        print(f"📋 其他服务: {len(self.other_services)} 个")
        
    def _find_gh_command(self):
        """查找gh命令路径"""
        gh_path = shutil.which("gh")
        if gh_path:
            return gh_path
        
        if self.is_windows:
            common_paths = [
                r"C:\Program Files\GitHub CLI\gh.exe",
                r"C:\Program Files (x86)\GitHub CLI\gh.exe",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path
            
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
        for attempt in range(retries):
            try:
                if self.is_windows:
                    cmd_str = " ".join([f'"{self.gh_cmd}"'] + [f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in args])
                    result = subprocess.run(
                        cmd_str,
                        shell=True,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',  # 处理编码错误
                        check=True,
                        timeout=300
                    )
                else:
                    result = subprocess.run(
                        [self.gh_cmd] + args,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        check=True,
                        timeout=300
                    )
                return result
            except subprocess.TimeoutExpired:
                if attempt < retries - 1:
                    time.sleep(delay)
            except subprocess.CalledProcessError as e:
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    # 不抛出异常，返回None让调用者处理
                    return None
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    # 不抛出异常，返回None让调用者处理
                    return None
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
        """等待运行完成"""
        print(f"等待运行完成... (最多{max_wait}秒)")
        
        elapsed = 0
        while elapsed < max_wait:
            try:
                result = self._run_gh_command([
                    "run", "view", run_id, "--repo", self.repo,
                    "--json", "status,conclusion"
                ])
                
                if result and result.stdout:
                    run_info = json.loads(result.stdout)
                    status = run_info["status"]
                    
                    if status == "completed":
                        conclusion = run_info["conclusion"]
                        return conclusion
                
                time.sleep(10)
                elapsed += 10
            except Exception as e:
                print(f"⚠️ 检查状态失败: {e}")
                time.sleep(10)
                elapsed += 10
        
        return "timeout"
    
    def get_jobs_with_ids(self, run_id):
        """获取所有作业及其ID"""
        try:
            result = self._run_gh_command([
                "run", "view", run_id, "--repo", self.repo,
                "--json", "jobs"
            ])
            
            if not result or not result.stdout:
                return []
            
            run_info = json.loads(result.stdout)
            jobs = run_info.get("jobs", [])
            
            return [
                {
                    "id": str(job.get("databaseId", "")),
                    "name": job.get("name", "Unknown"),
                    "status": job.get("status", "unknown"),
                    "conclusion": job.get("conclusion", "none")
                }
                for job in jobs
            ]
        except Exception as e:
            print(f"❌ 获取作业列表失败: {e}")
            return []
    
    def download_job_log(self, run_id, job_id, job_name):
        """使用job ID下载日志 - 修复编码问题"""
        print(f"📥 下载日志: job_id={job_id}, job_name={job_name}")
        
        # 方法1: 使用job ID（数字ID）
        if job_id and job_id.isdigit():
            try:
                # 直接使用subprocess，确保编码正确
                if self.is_windows:
                    cmd = f'"{self.gh_cmd}" run view {run_id} --repo {self.repo} --log --job {job_id}'
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=60
                    )
                else:
                    result = subprocess.run(
                        [self.gh_cmd, "run", "view", run_id, "--repo", self.repo,
                         "--log", "--job", job_id],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=60
                    )
                
                if result.returncode == 0 and result.stdout:
                    print(f"✅ 使用job ID下载成功 ({len(result.stdout)} 字符)")
                    return result.stdout
                else:
                    print(f"⚠️ job ID下载失败: {result.stderr[:200] if result.stderr else '无错误信息'}")
            except Exception as e:
                print(f"⚠️ job ID下载异常: {e}")
        
        # 方法2: 使用job name
        try:
            if self.is_windows:
                cmd = f'"{self.gh_cmd}" run view {run_id} --repo {self.repo} --log --job "{job_name}"'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=60
                )
            else:
                result = subprocess.run(
                    [self.gh_cmd, "run", "view", run_id, "--repo", self.repo,
                     "--log", "--job", job_name],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=60
                )
            
            if result.returncode == 0 and result.stdout:
                print(f"✅ 使用job name下载成功 ({len(result.stdout)} 字符)")
                return result.stdout
        except Exception as e:
            print(f"⚠️ job name下载异常: {e}")
        
        # 方法3: 获取所有日志然后提取
        try:
            if self.is_windows:
                cmd = f'"{self.gh_cmd}" run view {run_id} --repo {self.repo} --log'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=120
                )
            else:
                result = subprocess.run(
                    [self.gh_cmd, "run", "view", run_id, "--repo", self.repo, "--log"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=120
                )
            
            if result.returncode == 0 and result.stdout:
                # 提取特定job的日志
                lines = result.stdout.split('\n')
                job_lines = []
                in_job = False
                for line in lines:
                    if f"##[{job_name}]" in line or f"##[{job_name} " in line:
                        in_job = True
                    if in_job:
                        job_lines.append(line)
                    if in_job and line.startswith("##[") and job_name not in line and "Frontend" not in line:
                        break
                
                if job_lines:
                    log_content = '\n'.join(job_lines)
                    print(f"✅ 从全部日志中提取成功 ({len(log_content)} 字符)")
                    return log_content
        except Exception as e:
            print(f"⚠️ 获取全部日志异常: {e}")
        
        print(f"❌ 所有方法都失败，无法下载日志")
        return None
    
    def check_jobs_status(self, run_id):
        """检查作业状态，重点关注Frontend Tests"""
        jobs = self.get_jobs_with_ids(run_id)
        
        if not jobs:
            return False, 0, 0, None
        
        print(f"\n{'='*60}")
        print(f"作业状态检查 (共 {len(jobs)} 个作业)")
        print(f"{'='*60}")
        
        success_count = 0
        failure_count = 0
        skipped_count = 0
        frontend_job = None
        
        for job in jobs:
            name = job["name"]
            status = job["status"]
            conclusion = job["conclusion"]
            
            if "Frontend" in name or "frontend" in name.lower():
                frontend_job = job
            
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
            else:
                print(f"⏳ {name} ({status})")
        
        print(f"{'='*60}")
        print(f"成功: {success_count} | 失败: {failure_count} | 跳过: {skipped_count}")
        print(f"{'='*60}\n")
        
        all_passed = failure_count == 0 and success_count > 0
        return all_passed, success_count, failure_count, frontend_job
    
    def analyze_frontend_errors(self, log_content):
        """分析前端错误"""
        errors = []
        
        # TypeScript错误 - 多种格式
        patterns = [
            # 格式: ##[error]src/app/admin/settings/page.tsx(198,24): error TS2339: Property 'last_login_at' does not exist
            r'##\[error\](src/[^:]+)\((\d+),(\d+)\):\s+error TS\d+:\s*(.+)',
            # 格式: ./src/app/admin/settings/page.tsx:198:24 Type error: Property 'last_login_at' does not exist
            r'\./(src/[^:]+):(\d+):(\d+)\s+Type error:\s*(.+)',
            # 格式: error TS2339: Property 'last_login_at' does not exist
            r'error TS\d+:\s*(.+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, log_content, re.MULTILINE)
            for match in matches:
                if len(match.groups()) >= 4:
                    errors.append({
                        "type": "typescript",
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "column": int(match.group(3)),
                        "message": match.group(4).strip()
                    })
                elif len(match.groups()) >= 1:
                    errors.append({
                        "type": "typescript",
                        "message": match.group(1).strip()
                    })
        
        # 去重（基于文件+行号）
        seen = set()
        unique_errors = []
        for error in errors:
            key = (error.get("file"), error.get("line"), error.get("message", ""))
            if key not in seen:
                seen.add(key)
                unique_errors.append(error)
        
        # 构建错误
        if "Failed to compile" in log_content:
            unique_errors.append({
                "type": "build",
                "message": "前端构建失败"
            })
        
        return unique_errors
    
    
    def commit_and_push(self):
        """提交并推送 - 确保每次修复都提交"""
        try:
            # 切换到项目目录
            original_dir = os.getcwd()
            os.chdir(self.project_dir)
            
            try:
                # 检查是否有更改
                result = subprocess.run(
                    ["git", "status", "--short"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=30
                )
                
                if not result.stdout.strip():
                    print("  ℹ️ 没有更改需要提交")
                    return False
                
                print(f"  📝 发现更改，准备提交...")
                print(f"  更改文件:")
                for line in result.stdout.strip().split('\n')[:10]:  # 只显示前10个
                    print(f"    {line}")
                
                # 添加所有更改
                subprocess.run(
                    ["git", "add", "-A"],
                    check=True,
                    timeout=60,
                    capture_output=True
                )
                
                # 生成提交信息
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"fix: Manual fixes for CI/CD tests - {timestamp}"
                
                # 提交
                commit_result = subprocess.run(
                    ["git", "commit", "-m", commit_message],
                    check=True,
                    timeout=60,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                print(f"  ✅ 代码已提交: {commit_result.stdout.strip()[:100]}")
                
                # 推送
                print(f"  📤 推送到GitHub...")
                push_result = subprocess.run(
                    ["git", "push", "origin", "main"],
                    check=True,
                    timeout=120,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                print(f"  ✅ 代码已推送到GitHub")
                return True
                
            finally:
                os.chdir(original_dir)
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Git操作失败: {e}")
            if e.stderr:
                print(f"  错误: {e.stderr[:200]}")
            return False
        except Exception as e:
            print(f"  ❌ 提交异常: {e}")
            return False
    
    def run(self):
        """运行测试"""
        print("=" * 60)
        print("核心服务优先测试系统")
        print("=" * 60)
        print(f"核心服务: {', '.join(self.core_services)}")
        print("=" * 60)
        print()
        
        iteration = 0
        consecutive_success = 0
        
        while iteration < 100:  # 限制迭代次数
            iteration += 1
            
            print()
            print("=" * 60)
            print(f"迭代 {iteration}")
            print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            print()
            
            try:
                # 启动工作流
                if not self.start_workflow():
                    print("等待30秒后重试...")
                    time.sleep(30)
                    continue
                
                # 获取运行ID
                run_id, status = self.get_latest_run_id()
                if not run_id:
                    print("等待30秒后重试...")
                    time.sleep(30)
                    continue
                
                print(f"运行ID: {run_id}")
                
                # 等待完成
                conclusion = self.wait_for_completion(run_id)
                print(f"运行结果: {conclusion}")
                
                # 检查作业状态
                all_passed, success_count, failure_count, frontend_job = self.check_jobs_status(run_id)
                
                if all_passed:
                    consecutive_success += 1
                    print(f"✅ 所有测试通过！ (连续成功: {consecutive_success})")
                    
                    if consecutive_success >= 2:
                        print()
                        print("=" * 60)
                        print("🎉 所有核心服务测试通过！")
                        print("=" * 60)
                        break
                else:
                    consecutive_success = 0
                    
                    # 优先处理Frontend Tests
                    if frontend_job and frontend_job["conclusion"] == "failure":
                        print("🔍 下载Frontend Tests错误日志...")
                        
                        try:
                            log_content = self.download_job_log(
                                run_id,
                                frontend_job["id"],
                                frontend_job["name"]
                            )
                            
                            if log_content:
                                print(f"✅ 日志下载成功 ({len(log_content)} 字符)")
                                
                                # 保存日志到文件
                                log_file = self.log_dir / f"run-{run_id}-frontend.log"
                                log_file.write_text(log_content, encoding='utf-8', errors='replace')
                                print(f"📁 日志已保存到: {log_file}")
                                
                                # 分析错误（仅用于显示，不自动修复）
                                errors = self.analyze_frontend_errors(log_content)
                                
                                if errors:
                                    print(f"\n发现 {len(errors)} 个错误:")
                                    for i, error in enumerate(errors[:10], 1):  # 显示前10个
                                        file_info = f"{error.get('file', '?')}:{error.get('line', '?')}" if error.get('file') else "?"
                                        print(f"  {i}. {file_info} - {error['message'][:100]}")
                                    
                                    if len(errors) > 10:
                                        print(f"  ... 还有 {len(errors) - 10} 个错误")
                                    
                                    print(f"\n⚠️ 请手动修复这些错误，然后脚本会自动提交代码")
                                else:
                                    print("⚠️ 未发现可识别的错误，请查看日志文件")
                                
                                # 检查是否有代码修改，如果有则提交
                                print("\n📝 检查是否有代码修改需要提交...")
                                if self.commit_and_push():
                                    print("✅ 代码已提交到Git，等待新工作流...")
                                    time.sleep(15)
                                else:
                                    print("ℹ️ 没有代码修改需要提交")
                            else:
                                print("⚠️ 无法下载日志，尝试从GitHub网页查看")
                                print(f"   运行链接: https://github.com/{self.repo}/actions/runs/{run_id}")
                        except Exception as e:
                            print(f"⚠️ 处理错误日志时出现异常: {e}")
                            import traceback
                            traceback.print_exc()
                            print("继续测试...")
                    
                    # 处理其他失败的作业
                    if failure_count > 0:
                        print(f"\n⚠️ 还有 {failure_count} 个作业失败，请查看GitHub Actions获取详细信息")
                        print(f"   运行链接: https://github.com/{self.repo}/actions/runs/{run_id}")
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n\n用户中断")
                break
            except Exception as e:
                print(f"⚠️ 迭代异常: {e}")
                import traceback
                traceback.print_exc()
                print("继续下一轮测试...")
                time.sleep(10)  # 短暂休息后继续
        
        print()
        print("=" * 60)
        print("测试结束")
        print("=" * 60)

if __name__ == "__main__":
    tester = CoreServiceTester()
    try:
        tester.run()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)

