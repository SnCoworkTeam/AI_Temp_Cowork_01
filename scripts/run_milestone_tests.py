"""
运行里程碑1-4的集成测试
"""
import sys
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def check_docker_services():
    """检查Docker服务是否运行"""
    print("=" * 60)
    print("检查Docker服务状态")
    print("=" * 60)
    
    services = ["postgres", "redis", "qdrant", "neo4j"]
    running_services = []
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        for line in result.stdout.strip().split('\n'):
            if line:
                import json
                try:
                    service_info = json.loads(line)
                    service_name = service_info.get("Service", "")
                    state = service_info.get("State", "")
                    if state == "running":
                        running_services.append(service_name)
                except:
                    pass
    except Exception as e:
        print(f"检查Docker服务失败: {e}")
        return False
    
    print(f"\n运行中的服务: {', '.join(running_services) if running_services else '无'}")
    
    # 检查必需的服务
    required_services = ["postgres"]
    missing_services = [s for s in required_services if s not in running_services]
    
    if missing_services:
        print(f"\n⚠️  缺少必需服务: {', '.join(missing_services)}")
        print("正在启动服务...")
        return start_services()
    
    return True

def start_services():
    """启动Docker服务"""
    print("\n" + "=" * 60)
    print("启动Docker服务")
    print("=" * 60)
    
    try:
        # 启动服务
        subprocess.run(
            ["docker-compose", "up", "-d", "postgres", "redis", "qdrant", "neo4j"],
            cwd=PROJECT_ROOT,
            check=True
        )
        
        print("\n等待服务启动...")
        time.sleep(15)
        
        # 再次检查
        result = subprocess.run(
            ["docker-compose", "ps"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        print(result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动服务失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")
        return False

def run_tests():
    """运行测试"""
    print("\n" + "=" * 60)
    print("运行里程碑集成测试")
    print("=" * 60)
    
    test_file = PROJECT_ROOT / "tests" / "milestone_integration_test.py"
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    try:
        # 运行pytest
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                str(test_file),
                "-v",
                "--tb=short",
                "-x"  # 遇到第一个失败就停止
            ],
            cwd=PROJECT_ROOT
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("LuminaOS演进蓝图 - 里程碑1-4测试验证")
    print("=" * 60)
    print()
    
    # 1. 检查Docker服务
    if not check_docker_services():
        print("\n❌ Docker服务检查失败，请手动启动服务")
        print("   运行: docker-compose up -d postgres redis qdrant neo4j")
        return 1
    
    # 2. 运行测试
    print("\n" + "=" * 60)
    print("开始运行测试")
    print("=" * 60)
    
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成")
    else:
        print("❌ 测试失败")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

