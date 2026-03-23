#!/usr/bin/env python3
"""
检查服务间依赖冲突
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent.parent

# 收集所有Python服务的依赖
services_deps = {}
services = ["mcp-gateway", "workflow-engine", "auth-service", "knowledge-base", "shared-libs"]

for service in services:
    req_file = project_root / service / "requirements.txt"
    if req_file.exists():
        deps = {}
        with open(req_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 解析依赖（简化版）
                    if '==' in line:
                        parts = line.split('==')
                        if len(parts) == 2:
                            deps[parts[0].strip()] = parts[1].strip()
        services_deps[service] = deps

# 检查版本冲突
conflicts = []
package_versions = defaultdict(dict)

for service, deps in services_deps.items():
    for package, version in deps.items():
        package_versions[package][service] = version

# 找出冲突
for package, versions in package_versions.items():
    unique_versions = set(versions.values())
    if len(unique_versions) > 1:
        conflicts.append({
            "package": package,
            "versions": dict(versions),
            "services": list(versions.keys())
        })

# 输出结果
if conflicts:
    print("\n发现依赖版本冲突:")
    for conflict in conflicts:
        print(f"\n包: {conflict['package']}")
        for service, version in conflict['versions'].items():
            print(f"  {service}: {version}")
else:
    print("\n✅ 未发现依赖版本冲突")

sys.exit(0 if not conflicts else 1)









