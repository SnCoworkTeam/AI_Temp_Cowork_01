"""
检查环境变量，查找可能导致Docker API调用的配置
"""
import os
import sys

def check_environment():
    """检查环境变量"""
    print("=" * 80)
    print("检查环境变量配置")
    print("=" * 80)
    
    # 检查HTTP代理相关环境变量
    proxy_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'
    ]
    
    print("\n1. HTTP代理环境变量:")
    print("-" * 80)
    found_proxy = False
    for var in proxy_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var} = {value}")
            found_proxy = True
            # 检查是否包含docker相关的内容
            if 'docker' in value.lower():
                print(f"    ⚠️  警告: 此代理配置包含'docker'，可能触发Docker API调用！")
    
    if not found_proxy:
        print("  ✅ 未设置HTTP代理环境变量")
    
    # 检查Docker相关环境变量
    docker_vars = [
        'DOCKER_HOST', 'DOCKER_API_VERSION', 'DOCKER_TLS_VERIFY',
        'DOCKER_CERT_PATH', 'COMPOSE_PROJECT_NAME'
    ]
    
    print("\n2. Docker相关环境变量:")
    print("-" * 80)
    found_docker = False
    for var in docker_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var} = {value}")
            found_docker = True
    
    if not found_docker:
        print("  ✅ 未设置Docker相关环境变量")
    
    # 检查Python路径
    print("\n3. Python路径:")
    print("-" * 80)
    print(f"  sys.executable = {sys.executable}")
    print(f"  sys.path[0] = {sys.path[0] if sys.path else 'N/A'}")
    
    # 检查httpx相关配置
    print("\n4. 建议:")
    print("-" * 80)
    print("  如果发现HTTP代理配置指向Docker，请:")
    print("  1. 临时取消代理: unset HTTP_PROXY HTTPS_PROXY")
    print("  2. 或在代码中明确禁用代理: proxies={}")
    print("  3. 确保httpx客户端配置正确")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_environment()


