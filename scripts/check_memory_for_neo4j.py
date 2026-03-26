"""
检查服务器内存使用情况，评估是否可以部署Neo4j
"""
import subprocess
import json
import sys
from typing import Dict, List, Tuple

def get_system_memory() -> Dict[str, float]:
    """获取系统内存信息"""
    try:
        # Linux系统
        result = subprocess.run(
            ["free", "-m"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            mem_line = lines[1].split()
            total = float(mem_line[1])
            used = float(mem_line[2])
            free = float(mem_line[3])
            available = float(mem_line[6]) if len(mem_line) > 6 else free
            
            return {
                "total_gb": total / 1024,
                "used_gb": used / 1024,
                "free_gb": free / 1024,
                "available_gb": available / 1024,
                "usage_percent": (used / total) * 100
            }
    except FileNotFoundError:
        # Windows系统
        try:
            result = subprocess.run(
                ["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory", "/format:list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                total = 0
                free = 0
                for line in lines:
                    if 'TotalVisibleMemorySize=' in line:
                        total = float(line.split('=')[1]) / (1024 * 1024)  # KB to GB
                    if 'FreePhysicalMemory=' in line:
                        free = float(line.split('=')[1]) / (1024 * 1024)  # KB to GB
                
                used = total - free
                return {
                    "total_gb": total,
                    "used_gb": used,
                    "free_gb": free,
                    "available_gb": free,
                    "usage_percent": (used / total) * 100 if total > 0 else 0
                }
        except:
            pass
    
    return None

def get_docker_memory_usage() -> List[Dict[str, any]]:
    """获取Docker容器内存使用情况"""
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.MemUsage}}|{{.MemPerc}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        name = parts[0]
                        mem_usage = parts[1]  # e.g., "512MiB / 2GiB"
                        mem_perc = parts[2].replace('%', '')
                        
                        # 解析内存使用量
                        try:
                            mem_parts = mem_usage.split('/')
                            used_str = mem_parts[0].strip()
                            total_str = mem_parts[1].strip() if len(mem_parts) > 1 else "0"
                            
                            # 转换为MB
                            used_mb = parse_memory_size(used_str)
                            total_mb = parse_memory_size(total_str)
                            
                            containers.append({
                                "name": name,
                                "used_mb": used_mb,
                                "total_mb": total_mb,
                                "percent": float(mem_perc) if mem_perc else 0
                            })
                        except:
                            containers.append({
                                "name": name,
                                "used_mb": 0,
                                "total_mb": 0,
                                "percent": 0
                            })
            return containers
    except:
        pass
    return []

def parse_memory_size(size_str: str) -> float:
    """解析内存大小字符串，返回MB"""
    size_str = size_str.strip().upper()
    if 'GIB' in size_str or 'GB' in size_str:
        value = float(size_str.replace('GIB', '').replace('GB', '').strip())
        return value * 1024
    elif 'MIB' in size_str or 'MB' in size_str:
        value = float(size_str.replace('MIB', '').replace('MB', '').strip())
        return value
    elif 'KIB' in size_str or 'KB' in size_str:
        value = float(size_str.replace('KIB', '').replace('KB', '').strip())
        return value / 1024
    else:
        try:
            return float(size_str) / (1024 * 1024)  # 假设是字节
        except:
            return 0

def estimate_neo4j_memory(data_size_gb: float = 1.0) -> Dict[str, float]:
    """估算Neo4j内存需求"""
    # Neo4j内存配置建议
    # 最小配置（开发/测试）
    min_heap = 1.0  # GB
    min_pagecache = 0.5  # GB
    min_total = min_heap + min_pagecache + 0.5  # 额外0.5GB系统开销
    
    # 推荐配置（生产）
    # 根据数据量计算
    # heap: 建议为数据量的1-2倍，最小2GB，最大不超过系统内存的50%
    recommended_heap = max(2.0, min(data_size_gb * 1.5, 8.0))
    
    # pagecache: 建议为数据量的1-1.5倍，用于缓存图数据
    recommended_pagecache = max(1.0, min(data_size_gb * 1.2, 16.0))
    
    # 系统预留
    system_reserve = 2.0  # GB
    
    recommended_total = recommended_heap + recommended_pagecache + system_reserve
    
    return {
        "min_heap_gb": min_heap,
        "min_pagecache_gb": min_pagecache,
        "min_total_gb": min_total,
        "recommended_heap_gb": recommended_heap,
        "recommended_pagecache_gb": recommended_pagecache,
        "recommended_total_gb": recommended_total,
        "system_reserve_gb": system_reserve
    }

def analyze_memory_for_neo4j(system_mem: Dict, docker_containers: List[Dict], neo4j_config: Dict) -> Dict:
    """分析内存是否足够部署Neo4j"""
    total_mem_gb = system_mem["total_gb"]
    available_mem_gb = system_mem["available_gb"]
    used_mem_gb = system_mem["used_gb"]
    
    # 计算Docker容器总内存使用
    docker_total_mb = sum(c["used_mb"] for c in docker_containers)
    docker_total_gb = docker_total_mb / 1024
    
    # 计算可用于Neo4j的内存
    # 假设系统需要保留2GB
    system_reserve = 2.0
    available_for_neo4j = available_mem_gb - system_reserve
    
    # 评估最小配置
    min_neo4j = neo4j_config["min_total_gb"]
    can_deploy_min = available_for_neo4j >= min_neo4j
    
    # 评估推荐配置
    recommended_neo4j = neo4j_config["recommended_total_gb"]
    can_deploy_recommended = available_for_neo4j >= recommended_neo4j
    
    # 计算部署后的内存使用率
    if can_deploy_min:
        after_deploy_used = used_mem_gb + min_neo4j
        after_deploy_percent = (after_deploy_used / total_mem_gb) * 100
    else:
        after_deploy_used = used_mem_gb
        after_deploy_percent = system_mem["usage_percent"]
    
    return {
        "total_memory_gb": total_mem_gb,
        "used_memory_gb": used_mem_gb,
        "available_memory_gb": available_mem_gb,
        "docker_containers_memory_gb": docker_total_gb,
        "system_reserve_gb": system_reserve,
        "available_for_neo4j_gb": available_for_neo4j,
        "neo4j_min_required_gb": min_neo4j,
        "neo4j_recommended_gb": recommended_neo4j,
        "can_deploy_min": can_deploy_min,
        "can_deploy_recommended": can_deploy_recommended,
        "current_usage_percent": system_mem["usage_percent"],
        "after_deploy_usage_percent": after_deploy_percent,
        "recommendation": get_recommendation(total_mem_gb, available_for_neo4j, min_neo4j, recommended_neo4j)
    }

def get_recommendation(total_gb: float, available_gb: float, min_gb: float, recommended_gb: float) -> str:
    """生成部署建议"""
    if available_gb >= recommended_gb:
        return "✅ 可以部署Neo4j（推荐配置）"
    elif available_gb >= min_gb:
        return "⚠️ 可以部署Neo4j（最小配置），但建议优化其他服务的内存使用"
    elif total_gb >= 16:
        return "❌ 当前可用内存不足，建议：1) 优化现有服务内存使用 2) 增加服务器内存 3) 使用最小配置但性能可能受限"
    else:
        return "❌ 服务器内存不足16GB，建议升级到至少32GB内存"

def print_report(system_mem: Dict, docker_containers: List[Dict], neo4j_config: Dict, analysis: Dict):
    """打印分析报告"""
    print("=" * 80)
    print("Neo4j部署内存分析报告")
    print("=" * 80)
    print()
    
    # 系统内存信息
    print("📊 系统内存信息:")
    print(f"  总内存: {system_mem['total_gb']:.2f} GB")
    print(f"  已使用: {system_mem['used_gb']:.2f} GB ({system_mem['usage_percent']:.1f}%)")
    print(f"  可用内存: {system_mem['available_gb']:.2f} GB")
    print()
    
    # Docker容器内存使用
    if docker_containers:
        print("🐳 Docker容器内存使用 (Top 10):")
        sorted_containers = sorted(docker_containers, key=lambda x: x["used_mb"], reverse=True)
        total_docker_mb = sum(c["used_mb"] for c in docker_containers)
        print(f"  容器总数: {len(docker_containers)}")
        print(f"  容器总内存使用: {total_docker_mb / 1024:.2f} GB")
        print()
        print("  占用内存最多的容器:")
        for i, container in enumerate(sorted_containers[:10], 1):
            print(f"    {i}. {container['name']:40s} {container['used_mb']:8.1f} MB ({container['percent']:.1f}%)")
        print()
    
    # Neo4j内存需求
    print("📦 Neo4j内存需求:")
    print(f"  最小配置:")
    print(f"    - Heap: {neo4j_config['min_heap_gb']:.1f} GB")
    print(f"    - PageCache: {neo4j_config['min_pagecache_gb']:.1f} GB")
    print(f"    - 总计: {neo4j_config['min_total_gb']:.1f} GB")
    print()
    print(f"  推荐配置:")
    print(f"    - Heap: {neo4j_config['recommended_heap_gb']:.1f} GB")
    print(f"    - PageCache: {neo4j_config['recommended_pagecache_gb']:.1f} GB")
    print(f"    - 系统预留: {neo4j_config['system_reserve_gb']:.1f} GB")
    print(f"    - 总计: {neo4j_config['recommended_total_gb']:.1f} GB")
    print()
    
    # 分析结果
    print("🔍 部署可行性分析:")
    print(f"  可用于Neo4j的内存: {analysis['available_for_neo4j_gb']:.2f} GB")
    print(f"  Neo4j最小需求: {analysis['neo4j_min_required_gb']:.1f} GB")
    print(f"  Neo4j推荐配置: {analysis['neo4j_recommended_gb']:.1f} GB")
    print()
    print(f"  最小配置: {'✅ 可以部署' if analysis['can_deploy_min'] else '❌ 内存不足'}")
    print(f"  推荐配置: {'✅ 可以部署' if analysis['can_deploy_recommended'] else '❌ 内存不足'}")
    print()
    
    # 部署后内存使用
    if analysis['can_deploy_min']:
        print(f"  部署后内存使用率: {analysis['after_deploy_usage_percent']:.1f}%")
        if analysis['after_deploy_usage_percent'] > 85:
            print("  ⚠️  警告: 部署后内存使用率较高，建议监控")
    print()
    
    # 建议
    print("💡 建议:")
    print(f"  {analysis['recommendation']}")
    print()
    
    # 优化建议
    if not analysis['can_deploy_recommended']:
        print("🔧 优化建议:")
        if docker_containers:
            print("  1. 优化Docker容器内存使用:")
            sorted_containers = sorted(docker_containers, key=lambda x: x["used_mb"], reverse=True)
            for container in sorted_containers[:5]:
                print(f"     - {container['name']}: {container['used_mb']:.1f} MB")
        print("  2. 考虑使用Neo4j最小配置（性能可能受限）")
        print("  3. 如果数据量较小，可以降低PageCache大小")
        print("  4. 考虑将部分服务迁移到其他服务器")
        print()
    
    print("=" * 80)

def main():
    """主函数"""
    print("正在检查系统内存使用情况...")
    print()
    
    # 获取系统内存
    system_mem = get_system_memory()
    if not system_mem:
        print("❌ 无法获取系统内存信息")
        sys.exit(1)
    
    # 获取Docker容器内存使用
    docker_containers = get_docker_memory_usage()
    
    # 估算Neo4j内存需求（假设初始数据量1GB）
    neo4j_config = estimate_neo4j_memory(data_size_gb=1.0)
    
    # 分析
    analysis = analyze_memory_for_neo4j(system_mem, docker_containers, neo4j_config)
    
    # 打印报告
    print_report(system_mem, docker_containers, neo4j_config, analysis)
    
    # 返回退出码
    if analysis['can_deploy_min']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()



