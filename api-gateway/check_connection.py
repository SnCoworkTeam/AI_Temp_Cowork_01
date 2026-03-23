#!/usr/bin/env python3
"""
API Gateway 连接诊断脚本
检查 API Gateway 是否能正确连接到后端服务
"""
import sys
import urllib.request
import urllib.error
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from api_gateway.src.config import settings
except ImportError:
    # 如果无法导入，使用默认配置
    class Settings:
        LOCAL_DEV = False
        USE_LOCALHOST = False
        REGISTRY_SERVICE_URL = "http://registry-service:8000"
        HOST = "0.0.0.0"
        PORT = 8080
    
    settings = Settings()


def check_service(service_name: str, url: str, timeout: float = 5.0):
    """检查服务是否可访问"""
    try:
        req = urllib.request.Request(f"{url}/health")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                print(f"✅ {service_name} ({url}) - 正常")
                return True
            else:
                print(f"⚠️  {service_name} ({url}) - 返回状态码: {response.status}")
                return False
    except urllib.error.URLError as e:
        if "Connection refused" in str(e) or "Name or service not known" in str(e):
            print(f"❌ {service_name} ({url}) - 连接失败（服务可能未运行）")
        else:
            print(f"❌ {service_name} ({url}) - 错误: {e}")
        return False
    except Exception as e:
        print(f"❌ {service_name} ({url}) - 错误: {e}")
        return False


def check_registry_service():
    """检查 Registry Service"""
    registry_url = settings.REGISTRY_SERVICE_URL
    print(f"\n📋 检查 Registry Service: {registry_url}")
    return check_service("Registry Service", registry_url)


def check_auth_service():
    """检查 Auth Service"""
    use_localhost = settings.LOCAL_DEV or settings.USE_LOCALHOST
    
    if use_localhost:
        auth_url = "http://localhost:8003"
        mode = "本地模式 (localhost)"
    else:
        auth_url = "http://auth-service:8003"
        mode = "Docker 模式 (服务名)"
    
    print(f"\n🔐 检查 Auth Service ({mode}): {auth_url}")
    return check_service("Auth Service", auth_url)


def check_api_gateway():
    """检查 API Gateway 本身"""
    gateway_url = f"http://localhost:{settings.PORT}"
    print(f"\n🌐 检查 API Gateway: {gateway_url}")
    return check_service("API Gateway", gateway_url)


def test_proxy_route():
    """测试 API Gateway 代理路由"""
    gateway_url = f"http://localhost:{settings.PORT}"
    test_url = f"{gateway_url}/api/auth/health"
    
    print(f"\n🔗 测试 API Gateway 代理路由: {test_url}")
    try:
        req = urllib.request.Request(test_url)
        with urllib.request.urlopen(req, timeout=10.0) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')[:100]
                print(f"✅ 代理路由正常 - 状态码: {response.status}")
                print(f"   响应: {content}")
                return True
            else:
                content = response.read().decode('utf-8')[:200]
                print(f"⚠️  代理路由返回状态码: {response.status}")
                print(f"   响应: {content}")
                return False
    except Exception as e:
        print(f"❌ 代理路由测试失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("API Gateway 连接诊断")
    print("=" * 60)
    
    print(f"\n📝 当前配置:")
    print(f"   LOCAL_DEV: {settings.LOCAL_DEV}")
    print(f"   USE_LOCALHOST: {settings.USE_LOCALHOST}")
    print(f"   REGISTRY_SERVICE_URL: {settings.REGISTRY_SERVICE_URL}")
    print(f"   HOST: {settings.HOST}")
    print(f"   PORT: {settings.PORT}")
    
    # 检查各个服务
    results = []
    results.append(check_api_gateway())
    results.append(check_registry_service())
    results.append(check_auth_service())
    
    # 测试代理路由
    if all(results):
        results.append(test_proxy_route())
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断结果")
    print("=" * 60)
    
    if all(results):
        print("✅ 所有检查通过！API Gateway 连接正常。")
        return 0
    else:
        print("❌ 发现问题，请检查以下内容：")
        print("\n1. 确保所有服务正在运行：")
        print("   - API Gateway: http://localhost:8080")
        print("   - Auth Service: http://localhost:8003")
        print("   - Registry Service: http://localhost:8000")
        print("\n2. 如果是本地开发环境，在 .env 文件中设置：")
        print("   LOCAL_DEV=true")
        print("\n3. 检查服务日志以获取更多信息")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

