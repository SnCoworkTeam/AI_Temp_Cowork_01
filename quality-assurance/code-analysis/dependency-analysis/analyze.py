#!/usr/bin/env python3
"""
依赖分析
分析项目依赖关系、版本冲突和安全漏洞
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 项目根目录
project_root = Path(__file__).parent.parent.parent.parent
output_dir = project_root / "quality-assurance" / "reports" / "dependency-analysis"
output_dir.mkdir(parents=True, exist_ok=True)


def find_requirements_files(project_path: Path) -> List[Path]:
    """查找所有requirements文件"""
    requirements_files = []
    
    # 查找根目录的requirements.txt
    root_requirements = project_path / "requirements.txt"
    if root_requirements.exists():
        requirements_files.append(root_requirements)
    
    # 查找所有子目录的requirements.txt
    for req_file in project_path.rglob("requirements.txt"):
        if req_file != root_requirements:
            requirements_files.append(req_file)
    
    return requirements_files


def analyze_dependencies(requirements_file: Path) -> Dict[str, Any]:
    """分析单个requirements文件的依赖"""
    print(f"分析依赖: {requirements_file}")
    
    dependencies = {
        "file": str(requirements_file.relative_to(project_root)),
        "packages": [],
        "issues": []
    }
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 解析依赖行
            # 格式: package==version 或 package>=version
            if '==' in line:
                parts = line.split('==')
                package = parts[0].strip()
                version = parts[1].strip() if len(parts) > 1 else None
            elif '>=' in line:
                parts = line.split('>=')
                package = parts[0].strip()
                version = parts[1].strip() if len(parts) > 1 else None
            else:
                package = line
                version = None
            
            dependencies["packages"].append({
                "name": package,
                "version": version,
                "spec": line
            })
    
    except Exception as e:
        dependencies["issues"].append(f"读取文件错误: {e}")
    
    return dependencies


def check_security_vulnerabilities() -> Dict[str, Any]:
    """检查安全漏洞（使用safety）"""
    print("检查安全漏洞...")
    
    results = {
        "tool": "safety",
        "timestamp": datetime.now().isoformat(),
        "vulnerabilities": []
    }
    
    try:
        # 运行safety check
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
                    if "vulnerability" in line.lower() or "CVE" in line:
                        results["vulnerabilities"].append({"message": line})
        
        results["summary"] = {
            "total_vulnerabilities": len(results["vulnerabilities"])
        }
        
    except FileNotFoundError:
        print("  ⚠️  Safety未安装")
        results["error"] = "Safety not installed"
    
    return results


def check_version_conflicts() -> Dict[str, Any]:
    """检查版本冲突"""
    print("检查版本冲突...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "conflicts": []
    }
    
    # 查找所有requirements文件
    requirements_files = find_requirements_files(project_root)
    
    # 收集所有包及其版本要求
    package_versions = {}
    
    for req_file in requirements_files:
        deps = analyze_dependencies(req_file)
        for pkg in deps["packages"]:
            pkg_name = pkg["name"]
            if pkg_name not in package_versions:
                package_versions[pkg_name] = []
            package_versions[pkg_name].append({
                "file": deps["file"],
                "version": pkg["version"],
                "spec": pkg["spec"]
            })
    
    # 检查冲突
    for pkg_name, versions in package_versions.items():
        if len(versions) > 1:
            # 检查是否有不同的版本要求
            unique_versions = set(v["version"] for v in versions if v["version"])
            if len(unique_versions) > 1:
                results["conflicts"].append({
                    "package": pkg_name,
                    "requirements": versions
                })
    
    results["summary"] = {
        "total_packages": len(package_versions),
        "conflicts_count": len(results["conflicts"])
    }
    
    return results


def generate_report(all_results: Dict[str, Any]) -> None:
    """生成依赖分析报告"""
    report_file = output_dir / f"dependency-analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "analysis": all_results
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存: {report_file}")
    
    # 打印摘要
    print("\n=== 依赖分析摘要 ===")
    
    if "vulnerabilities" in all_results:
        vuln_count = all_results["vulnerabilities"].get("summary", {}).get("total_vulnerabilities", 0)
        print(f"安全漏洞: {vuln_count}")
    
    if "conflicts" in all_results:
        conflict_count = all_results["conflicts"].get("summary", {}).get("conflicts_count", 0)
        print(f"版本冲突: {conflict_count}")


def main():
    """主函数"""
    print("开始依赖分析...")
    
    results = {}
    
    # 分析依赖
    requirements_files = find_requirements_files(project_root)
    results["dependencies"] = [analyze_dependencies(f) for f in requirements_files]
    
    # 检查安全漏洞
    results["vulnerabilities"] = check_security_vulnerabilities()
    
    # 检查版本冲突
    results["conflicts"] = check_version_conflicts()
    
    # 生成报告
    generate_report(results)
    
    # 检查是否有问题
    vuln_count = results["vulnerabilities"].get("summary", {}).get("total_vulnerabilities", 0)
    conflict_count = results["conflicts"].get("summary", {}).get("conflicts_count", 0)
    
    if vuln_count > 0 or conflict_count > 0:
        print(f"\n⚠️  发现 {vuln_count} 个安全漏洞和 {conflict_count} 个版本冲突")
        sys.exit(1)
    else:
        print("\n✅ 依赖分析完成，未发现问题")
        sys.exit(0)


if __name__ == "__main__":
    main()









