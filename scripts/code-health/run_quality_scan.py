#!/usr/bin/env python3
"""
代码质量扫描工具
运行 pylint、mypy、flake8 等工具对所有Python服务进行质量扫描
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
SERVICES = [
    "auth-service",
    "metadata-service",
    "mcp-gateway",
    "workflow-engine",
    "knowledge-base",
    "shared_libs",
    "database"
]

class QualityScanner:
    def __init__(self):
        self.results = {
            "scan_date": datetime.now().isoformat(),
            "services": {}
        }

    def check_tool_installed(self, tool: str) -> bool:
        """检查工具是否安装"""
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def install_tools(self):
        """安装必要的质量检查工具"""
        tools = ["pylint", "mypy", "flake8", "bandit"]

        print("检查并安装质量检查工具...")
        for tool in tools:
            if not self.check_tool_installed(tool):
                print(f"安装 {tool}...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", tool],
                                 check=True, capture_output=True)
                    print(f"✅ {tool} 安装成功")
                except subprocess.CalledProcessError as e:
                    print(f"❌ {tool} 安装失败: {e}")
            else:
                print(f"✅ {tool} 已安装")

    def run_pylint(self, service_path: Path) -> Dict[str, Any]:
        """运行 pylint 检查"""
        print(f"  运行 pylint...")

        # pylint 配置
        pylint_rc = PROJECT_ROOT / ".pylintrc"
        if not pylint_rc.exists():
            # 创建基本配置
            pylint_rc.write_text("""[MASTER]
max-line-length=120
disable=C0111,R0903,W0212,C0103,R0913,R0914,R0915,W0703
""")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pylint",
                 "--output-format=json",
                 "--rcfile", str(pylint_rc),
                 str(service_path / "src")],
                capture_output=True,
                text=True,
                timeout=300
            )

            # pylint 返回码: 0=无问题, 1-31=有问题但不是错误
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    return {
                        "status": "completed",
                        "issues_count": len(issues),
                        "issues": issues[:50],  # 只保存前50个问题
                        "score": self._parse_pylint_score(result.stderr)
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error": "无法解析 pylint 输出"
                    }
            else:
                return {
                    "status": "completed",
                    "issues_count": 0,
                    "score": 10.0
                }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "pylint 执行超时"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _parse_pylint_score(self, stderr: str) -> float:
        """从 pylint stderr 中解析分数"""
        for line in stderr.split('\n'):
            if 'Your code has been rated at' in line:
                try:
                    score = float(line.split()[6].split('/')[0])
                    return score
                except (IndexError, ValueError):
                    pass
        return 0.0

    def run_mypy(self, service_path: Path) -> Dict[str, Any]:
        """运行 mypy 类型检查"""
        print(f"  运行 mypy...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "mypy",
                 str(service_path / "src"),
                 "--ignore-missing-imports",
                 "--no-strict-optional"],
                capture_output=True,
                text=True,
                timeout=300
            )

            errors = [line for line in result.stdout.split('\n') if line.strip()]

            return {
                "status": "completed",
                "errors_count": len([e for e in errors if ": error:" in e]),
                "warnings_count": len([e for e in errors if ": warning:" in e]),
                "errors": errors[:50]
            }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "mypy 执行超时"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_flake8(self, service_path: Path) -> Dict[str, Any]:
        """运行 flake8 代码风格检查"""
        print(f"  运行 flake8...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8",
                 str(service_path / "src"),
                 "--max-line-length=120",
                 "--extend-ignore=E203,W503"],
                capture_output=True,
                text=True,
                timeout=300
            )

            issues = [line for line in result.stdout.split('\n') if line.strip()]

            return {
                "status": "completed",
                "issues_count": len(issues),
                "issues": issues[:100]
            }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "flake8 执行超时"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_bandit(self, service_path: Path) -> Dict[str, Any]:
        """运行 bandit 安全检查"""
        print(f"  运行 bandit...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "bandit",
                 "-r", str(service_path / "src"),
                 "-f", "json",
                 "-ll"],  # 只报告中高风险
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    return {
                        "status": "completed",
                        "high_severity": len([r for r in data.get("results", [])
                                            if r.get("issue_severity") == "HIGH"]),
                        "medium_severity": len([r for r in data.get("results", [])
                                              if r.get("issue_severity") == "MEDIUM"]),
                        "issues": data.get("results", [])[:20]
                    }
                except json.JSONDecodeError:
                    return {"status": "error", "error": "无法解析 bandit 输出"}
            else:
                return {
                    "status": "completed",
                    "high_severity": 0,
                    "medium_severity": 0
                }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "bandit 执行超时"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def scan_service(self, service_name: str) -> Dict[str, Any]:
        """扫描单个服务"""
        service_path = PROJECT_ROOT / service_name

        if not service_path.exists():
            return {"status": "not_found", "error": f"服务路径不存在: {service_path}"}

        print(f"\n扫描 {service_name}...")

        results = {
            "path": str(service_path),
            "pylint": self.run_pylint(service_path),
            "mypy": self.run_mypy(service_path),
            "flake8": self.run_flake8(service_path),
            "bandit": self.run_bandit(service_path)
        }

        return results

    def scan_all_services(self):
        """扫描所有服务"""
        print("=" * 60)
        print("开始代码质量扫描")
        print("=" * 60)

        self.install_tools()

        for service in SERVICES:
            self.results["services"][service] = self.scan_service(service)

        # 保存结果
        output_file = PROJECT_ROOT / "quality_scan_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n扫描完成！结果已保存到: {output_file}")

        # 生成摘要
        self.generate_summary()

    def generate_summary(self):
        """生成扫描摘要"""
        print("\n" + "=" * 60)
        print("扫描摘要")
        print("=" * 60)

        for service, results in self.results["services"].items():
            print(f"\n{service}:")

            if results.get("status") == "not_found":
                print("  ❌ 未找到")
                continue

            # Pylint
            pylint = results.get("pylint", {})
            if pylint.get("status") == "completed":
                print(f"  Pylint: {pylint.get('score', 0):.1f}/10, "
                      f"{pylint.get('issues_count', 0)} 问题")

            # Mypy
            mypy = results.get("mypy", {})
            if mypy.get("status") == "completed":
                print(f"  Mypy: {mypy.get('errors_count', 0)} 错误, "
                      f"{mypy.get('warnings_count', 0)} 警告")

            # Flake8
            flake8 = results.get("flake8", {})
            if flake8.get("status") == "completed":
                print(f"  Flake8: {flake8.get('issues_count', 0)} 问题")

            # Bandit
            bandit = results.get("bandit", {})
            if bandit.get("status") == "completed":
                print(f"  Bandit: {bandit.get('high_severity', 0)} 高风险, "
                      f"{bandit.get('medium_severity', 0)} 中风险")


def main():
    scanner = QualityScanner()
    scanner.scan_all_services()


if __name__ == "__main__":
    main()
