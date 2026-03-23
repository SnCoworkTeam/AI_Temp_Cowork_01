#!/usr/bin/env python3
"""
完整自动修复循环
1. 启动工作流
2. 获取运行ID
3. 等待完成
4. 下载日志
5. 分析错误
6. 修复bug
7. 验证修复
8. 提交推送
9. 循环
"""

import os
import re
import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

class AutoFixCycle:
    def __init__(self):
        self.project_dir = Path(__file__).parent.parent.parent
        self.repo = "PMLiuyubin/enterprise-ai-platform"
        self.workflow = "deploy.yml"
        self.log_dir = Path(os.getenv("TEMP", "/tmp")) / "github-errors"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_iterations = 5
        
    def start_workflow(self):
        """步骤1: 启动工作流"""
        print("[1/8] 启动工作流...")
        try:
            result = subprocess.run(
                ["gh", "workflow", "run", self.workflow,
                 "--field", "environment=staging", "--repo", self.repo],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ 工作流已启动")
            time.sleep(5)  # 等待工作流启动
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 启动失败: {e}")
            return False
    
    def get_latest_run_id(self):
        """步骤2: 获取最新运行ID"""
        print("[2/8] 获取最新运行ID...")
        try:
            result = subprocess.run(
                ["gh", "run", "list", "--workflow", self.workflow,
                 "--repo", self.repo, "--limit", "1",
                 "--json", "databaseId,status,conclusion"],
                capture_output=True,
                text=True,
                check=True
            )
            
            runs = json.loads(result.stdout)
            if runs:
                run = runs[0]
                run_id = str(run["databaseId"])
                status = run["status"]
                
                print(f"运行ID: {run_id}")
                print(f"状态: {status}")
                return run_id, status
            return None, None
        except Exception as e:
            print(f"❌ 获取运行ID失败: {e}")
            return None, None
    
    def wait_for_completion(self, run_id, max_wait=1800):
        """步骤3: 等待运行完成"""
        print(f"[3/8] 等待运行完成... (最多{max_wait}秒)")
        
        elapsed = 0
        while elapsed < max_wait:
            try:
                result = subprocess.run(
                    ["gh", "run", "view", run_id, "--repo", self.repo,
                     "--json", "status,conclusion"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                run_info = json.loads(result.stdout)
                status = run_info["status"]
                
                if status == "completed":
                    conclusion = run_info["conclusion"]
                    color = "✅" if conclusion == "success" else "❌"
                    print(f"{color} 运行完成，结果: {conclusion}")
                    return conclusion
                
                print(f"  状态: {status} (已等待 {elapsed}s)")
                time.sleep(10)
                elapsed += 10
            except Exception as e:
                print(f"⚠️ 检查状态失败: {e}")
                time.sleep(10)
                elapsed += 10
        
        print("⚠️ 超时")
        return "timeout"
    
    def download_logs(self, run_id):
        """步骤4: 下载日志"""
        print("[4/8] 下载日志...")
        
        log_dir = self.log_dir / f"run-{run_id}"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 获取所有作业
            result = subprocess.run(
                ["gh", "run", "view", run_id, "--repo", self.repo,
                 "--json", "jobs", "--jq", ".jobs[] | .name"],
                capture_output=True,
                text=True,
                check=True
            )
            
            jobs = [j for j in result.stdout.strip().split('\n') if j]
            
            for job in jobs:
                print(f"  下载: {job}")
                # 清理文件名
                safe_name = re.sub(r'[<>:"/\\|?*$]', '_', job)
                log_file = log_dir / f"{safe_name}.log"
                
                with open(log_file, "w", encoding="utf-8") as f:
                    subprocess.run(
                        ["gh", "run", "view", run_id, "--repo", self.repo,
                         "--log", "--job", job],
                        stdout=f,
                        stderr=subprocess.DEVNULL
                    )
            
            print(f"✅ 日志已保存到: {log_dir}")
            return log_dir
        except Exception as e:
            print(f"❌ 下载日志失败: {e}")
            return log_dir
    
    def analyze_errors(self, log_dir):
        """步骤5: 分析错误"""
        print("[5/8] 分析错误...")
        
        errors = []
        
        # 查找前端测试日志
        frontend_logs = list(log_dir.glob("*frontend*.log"))
        frontend_logs += list(log_dir.glob("*Frontend*.log"))
        
        for log_file in frontend_logs:
            print(f"分析: {log_file.name}")
            content = log_file.read_text(encoding="utf-8", errors="ignore")
            
            # 提取TypeScript错误 - 多种格式
            patterns = [
                r'\./(src/[^:]+):(\d+):(\d+)\s+Type error:\s*(.+)',
                r'##\[error\](src/[^:]+)\((\d+),(\d+)\):\s+error TS\d+:\s*(.+)',
                r'error TS\d+:\s*(.+)',
            ]
            
            matches = []
            for pattern in patterns:
                matches.extend(re.finditer(pattern, content))
            
            for match in matches:
                errors.append({
                    "type": "typescript",
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "message": match.group(4).strip()
                })
                print(f"  发现错误: {match.group(1)}:{match.group(2)} - {match.group(4).strip()}")
        
        if errors:
            print(f"❌ 发现 {len(errors)} 个错误")
        else:
            print("✅ 未发现错误")
        
        return errors
    
    def auto_fix(self, errors):
        """步骤6: 自动修复"""
        print("[6/8] 自动修复...")
        
        if not errors:
            print("✅ 无需修复")
            return False
        
        fixed = False
        
        for error in errors:
            file_path = self.project_dir / "web-ui" / error["file"]
            message = error["message"]
            
            if not file_path.exists():
                continue
            
            print(f"修复: {error['file']}:{error['line']}")
            print(f"  错误: {message}")
            
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            
            # 修复1: display_name, permissions, created_at等User接口字段
            if "does not exist" in message:
                if error["file"] == "src/lib/api/auth.ts":
                    # 提取缺失的属性名
                    prop_match = re.search(r"Property '(\w+)'", message)
                    if prop_match:
                        prop_name = prop_match.group(1)
                        if prop_name not in content:
                            # 在session_id后添加
                            content = re.sub(
                                r'(session_id\?: string)',
                                f'\\1\n  {prop_name}?: string' if prop_name in ['display_name', 'created_at', 'last_login_at'] else f'\\1\n  {prop_name}?: string[]' if prop_name == 'permissions' else f'\\1\n  {prop_name}?: any',
                                content
                            )
                            fixed = True
            
            # 修复2: 缺失导入
            match = re.search(r"Cannot find name '(\w+)'", message)
            if match:
                import_name = match.group(1)
                if f"from 'lucide-react'" in content or 'from "lucide-react"' in content:
                    if import_name not in content:
                        # 添加到导入
                        import_pattern = r"(import\s*\{[^}]+)\}\s*from\s*['\"]lucide-react['\"]"
                        if re.search(import_pattern, content):
                            content = re.sub(
                                import_pattern,
                                f"\\1,\n  {import_name}}} from 'lucide-react'",
                                content
                            )
                            fixed = True
            
            # 修复3: JSX语法错误 - 缺失闭合标签
            if "has no corresponding closing tag" in message or "Expected corresponding" in message:
                # 查找缺失的闭合标签
                tag_match = re.search(r"JSX element '(\w+)'", message)
                if tag_match:
                    tag_name = tag_match.group(1)
                    # 检查是否有对应的闭合标签
                    open_count = len(re.findall(f'<{tag_name}[^>]*>', content))
                    close_count = len(re.findall(f'</{tag_name}>', content))
                    if open_count > close_count:
                        # 在文件末尾或return语句前添加闭合标签
                        if "</div>" in content and f"</{tag_name}>" not in content:
                            # 在最后一个</div>后添加
                            content = content.rsplit("</div>", 1)[0] + f"</div>\n    </{tag_name}>" + content.rsplit("</div>", 1)[1]
                            fixed = True
            
            # 修复4: 类型不匹配
            if "is not assignable" in message:
                # 移除错误的else分支
                if "stat.icon" in content and "<span" in content:
                    lines = content.split('\n')
                    new_lines = []
                    skip = False
                    
                    for i, line in enumerate(lines):
                        if "IconComponent ?" in line:
                            new_lines.append(line.replace("?", "&&"))
                            skip = True
                        elif skip and "stat.icon" in line:
                            continue
                        elif skip and "</span>" in line:
                            skip = False
                            continue
                        else:
                            new_lines.append(line)
                            skip = False
                    
                    content = '\n'.join(new_lines)
                    fixed = True
            
            if content != original_content:
                file_path.write_text(content, encoding="utf-8")
                print(f"  ✅ 已修复")
        
        return fixed
    
    def verify_fixes(self):
        """步骤7: 验证修复"""
        print("[7/8] 验证修复...")
        
        web_ui_dir = self.project_dir / "web-ui"
        os.chdir(web_ui_dir)
        
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ 类型检查通过")
                return True
            else:
                print("❌ 类型检查仍有错误")
                errors = [line for line in result.stdout.split('\n') if 'error' in line.lower()]
                for error in errors[:5]:
                    print(f"  {error}")
                return False
        finally:
            os.chdir(self.project_dir)
    
    def commit_and_push(self):
        """步骤8: 提交并推送"""
        print("[8/8] 提交并推送...")
        
        # 检查是否有更改
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            print("⚠️ 没有更改需要提交")
            return False
        
        print("更改的文件:")
        for line in result.stdout.strip().split('\n'):
            print(f"  {line}")
        
        # 添加所有更改
        subprocess.run(["git", "add", "-A"], check=True)
        
        # 提交
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"fix: Auto-fix CI/CD errors - {timestamp}"
        
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=True
        )
        
        # 推送
        print("推送到远程...")
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print("✅ 已提交并推送")
        return True
    
    def run(self):
        """运行完整循环"""
        print("=" * 50)
        print("完整自动修复循环")
        print("=" * 50)
        print()
        
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            print()
            print("=" * 50)
            print(f"迭代 {iteration} / {self.max_iterations}")
            print("=" * 50)
            print()
            
            # 步骤1: 启动工作流
            if not self.start_workflow():
                print("跳过本次迭代")
                continue
            
            # 步骤2: 获取运行ID
            run_id, status = self.get_latest_run_id()
            if not run_id:
                print("跳过本次迭代")
                continue
            
            # 步骤3: 等待完成
            conclusion = self.wait_for_completion(run_id)
            
            # 步骤4: 下载日志
            log_dir = self.download_logs(run_id)
            
            # 步骤5: 分析错误
            errors = self.analyze_errors(log_dir)
            
            # 如果成功且无错误，退出
            if conclusion == "success" and not errors:
                print()
                print("=" * 50)
                print("✅ 所有测试通过！")
                print("=" * 50)
                break
            
            # 步骤6: 自动修复
            fixed = self.auto_fix(errors)
            
            if not fixed:
                print("⚠️ 无法自动修复，需要手动修复")
                print(f"日志目录: {log_dir}")
                break
            
            # 步骤7: 验证修复
            if not self.verify_fixes():
                print("❌ 修复验证失败")
                break
            
            # 步骤8: 提交并推送
            if self.commit_and_push():
                print("等待新工作流启动...")
                time.sleep(10)
            else:
                print("无需提交，继续下一轮")
        
        print()
        print("=" * 50)
        print("循环完成")
        print("=" * 50)
        print(f"总迭代次数: {iteration}")
        print(f"日志目录: {self.log_dir}")

if __name__ == "__main__":
    fixer = AutoFixCycle()
    fixer.run()

