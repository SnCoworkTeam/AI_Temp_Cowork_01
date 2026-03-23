#!/usr/bin/env python3
"""
安全扫描
使用多种工具进行安全漏洞扫描
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 项目根目录
project_root = Path(__file__).parent.parent.parent.parent
output_dir = project_root / "quality-assurance" / "reports" / "security-scan"
output_dir.mkdir(parents=True, exist_ok=True)


def run_bandit_scan() -> Dict[str, Any]:
    """使用Bandit进行安全扫描"""
    print("运行 Bandit 安全扫描...")
    
    results = {
        "tool": "bandit",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }
    
    try:
        cmd = [
            sys.executable, "-m", "bandit",
            "-r", str(project_root),
            "-f", "json",
            "-ll",  # 低/低级别
            "-x", "venv,env,.venv,__pycache__,migrations",  # 排除目录
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            try:
                bandit_results = json.loads(result.stdout)
                results["issues"] = bandit_results.get("results", [])
                results["metrics"] = bandit_results.get("metrics", {})
                
                # 统计严重程度
                severity_counts = {
                    "HIGH": 0,
                    "MEDIUM": 0,
                    "LOW": 0
                }
                
                for issue in results["issues"]:
                    severity = issue.get("issue_severity", "LOW")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                results["severity_counts"] = severity_counts
                
            except json.JSONDecodeError:
                pass
        
    except FileNotFoundError:
        print("  ⚠️  Bandit未安装")
        results["error"] = "Bandit not installed"
    
    return results


def run_safety_check() -> Dict[str, Any]:
    """使用Safety检查依赖安全漏洞"""
    print("运行 Safety 依赖安全检查...")
    
    results = {
        "tool": "safety",
        "timestamp": datetime.now().isoformat(),
        "vulnerabilities": []
    }
    
    try:
        cmd = [sys.executable, "-m", "safety", "check", "--json"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            try:
                vulns = json.loads(result.stdout)
                results["vulnerabilities"] = vulns
            except json.JSONDecodeError:
                # 解析文本输出
                for line in result.stdout.split("\n"):
                    if line.strip() and ("vulnerability" in line.lower() or "CVE" in line):
                        results["vulnerabilities"].append({"message": line.strip()})
        
        results["summary"] = {
            "total_vulnerabilities": len(results["vulnerabilities"])
        }
        
    except FileNotFoundError:
        print("  ⚠️  Safety未安装")
        results["error"] = "Safety not installed"
    
    return results


def check_secrets() -> Dict[str, Any]:
    """检查硬编码的密钥和敏感信息"""
    print("检查硬编码密钥...")
    
    results = {
        "tool": "secrets_scanner",
        "timestamp": datetime.now().isoformat(),
        "secrets": []
    }
    
    # 敏感关键词模式
    sensitive_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码"),
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "硬编码API密钥"),
        (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', "硬编码密钥"),
        (r'access[_-]?token\s*=\s*["\'][^"\']+["\']', "硬编码访问令牌"),
        (r'aws[_-]?access[_-]?key[_-]?id\s*=\s*["\'][^"\']+["\']', "硬编码AWS密钥"),
    ]
    
    import re
    
    # 查找所有Python文件
    python_files = list(project_root.rglob("*.py"))
    python_files = [
        f for f in python_files
        if "venv" not in str(f)
        and "__pycache__" not in str(f)
        and ".git" not in str(f)
        and "migrations" not in str(f)
    ]
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description in sensitive_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # 排除注释和测试文件中的示例
                        if not line.strip().startswith('#') and 'test' not in str(py_file).lower():
                            results["secrets"].append({
                                "file": str(py_file.relative_to(project_root)),
                                "line": line_num,
                                "type": description,
                                "content": line.strip()[:50]  # 只显示前50字符
                            })
        except Exception as e:
            pass
    
    results["summary"] = {
        "total_secrets": len(results["secrets"])
    }
    
    return results


def generate_report(all_results: List[Dict[str, Any]]) -> None:
    """生成安全扫描报告"""
    report_file = output_dir / f"security-scan-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "scans": all_results
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存: {report_file}")
    
    # 打印摘要
    print("\n=== 安全扫描摘要 ===")
    for result in all_results:
        tool = result.get("tool", "unknown")
        print(f"\n{tool}:")
        
        if "severity_counts" in result:
            counts = result["severity_counts"]
            print(f"  高危: {counts.get('HIGH', 0)}")
            print(f"  中危: {counts.get('MEDIUM', 0)}")
            print(f"  低危: {counts.get('LOW', 0)}")
        
        if "summary" in result:
            vuln_count = result["summary"].get("total_vulnerabilities", 0)
            if vuln_count > 0:
                print(f"  漏洞数: {vuln_count}")
        
        if "secrets" in result:
            secret_count = result["summary"].get("total_secrets", 0)
            if secret_count > 0:
                print(f"  硬编码密钥: {secret_count}")


def main():
    """主函数"""
    print("开始安全扫描...")
    
    all_results = []
    
    # 运行各种安全扫描
    all_results.append(run_bandit_scan())
    all_results.append(run_safety_check())
    all_results.append(check_secrets())
    
    # 生成报告
    generate_report(all_results)
    
    # 检查是否有严重安全问题
    critical_issues = 0
    
    for result in all_results:
        # Bandit高危问题
        if "severity_counts" in result:
            critical_issues += result["severity_counts"].get("HIGH", 0)
        
        # Safety漏洞
        if "summary" in result:
            critical_issues += result["summary"].get("total_vulnerabilities", 0)
        
        # 硬编码密钥
        if "summary" in result and "secrets" in result:
            critical_issues += result["summary"].get("total_secrets", 0)
    
    if critical_issues > 0:
        print(f"\n❌ 发现 {critical_issues} 个严重安全问题")
        sys.exit(1)
    else:
        print("\n✅ 安全扫描完成，未发现严重问题")
        sys.exit(0)


if __name__ == "__main__":
    main()









