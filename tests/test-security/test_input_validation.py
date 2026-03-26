"""
输入验证安全测试
测试SQL注入、XSS等安全漏洞
"""
import pytest
import httpx
from typing import List


@pytest.mark.security
class TestInputValidation:
    """输入验证测试"""
    
    @pytest.fixture
    def security_test_cases(self):
        """安全测试用例"""
        return {
            "sql_injection": [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "admin'--",
                "' UNION SELECT * FROM users --"
            ],
            "xss": [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>"
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32",
                "/etc/passwd",
                "C:\\Windows\\System32"
            ],
            "command_injection": [
                "; rm -rf /",
                "| cat /etc/passwd",
                "&& ls -la",
                "`whoami`"
            ]
        }
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, security_test_cases):
        """测试SQL注入防护"""
        async with httpx.AsyncClient() as client:
            for payload in security_test_cases["sql_injection"]:
                # 测试各种可能注入SQL的端点
                response = await client.get(
                    f"http://localhost:8000/api/tools?search={payload}"
                )
                
                # 不应该返回500错误（表示SQL执行）
                # 应该正确处理或返回400
                assert response.status_code != 500, \
                    f"SQL注入漏洞: {payload}"
    
    @pytest.mark.asyncio
    async def test_xss_protection(self, security_test_cases):
        """测试XSS防护"""
        async with httpx.AsyncClient() as client:
            for payload in security_test_cases["xss"]:
                # 测试可能返回用户输入的端点
                response = await client.post(
                    "http://localhost:8000/api/tools/test_tool/execute",
                    json={"parameters": {"input": payload}}
                )
                
                # 响应中不应该包含原始脚本
                if response.status_code == 200:
                    response_text = response.text
                    # 检查是否转义了危险字符
                    assert "<script>" not in response_text or \
                           "&lt;script&gt;" in response_text, \
                           f"XSS漏洞: {payload}"
    
    @pytest.mark.asyncio
    async def test_path_traversal_protection(self, security_test_cases):
        """测试路径遍历防护"""
        async with httpx.AsyncClient() as client:
            for payload in security_test_cases["path_traversal"]:
                # 测试文件相关的端点
                response = await client.get(
                    f"http://localhost:8004/api/documents/{payload}"
                )
                
                # 不应该返回敏感文件内容
                # 应该返回404或400
                assert response.status_code in [400, 404, 403], \
                    f"路径遍历漏洞: {payload}"
                
                # 响应中不应该包含系统文件内容
                if response.status_code == 200:
                    response_text = response.text.lower()
                    assert "root:" not in response_text, \
                        f"路径遍历漏洞: 返回了系统文件内容"
    
    @pytest.mark.asyncio
    async def test_command_injection_protection(self, security_test_cases):
        """测试命令注入防护"""
        async with httpx.AsyncClient() as client:
            for payload in security_test_cases["command_injection"]:
                # 测试可能执行命令的端点
                response = await client.post(
                    "http://localhost:8000/api/tools/execute",
                    json={"command": payload}
                )
                
                # 不应该执行命令
                # 应该返回400或拒绝执行
                assert response.status_code in [400, 403], \
                    f"命令注入漏洞: {payload}"


@pytest.mark.security
class TestDataSecurity:
    """数据安全测试"""
    
    @pytest.mark.asyncio
    async def test_sensitive_data_exposure(self):
        """测试敏感数据泄露"""
        async with httpx.AsyncClient() as client:
            # 测试用户信息端点不应该返回密码
            response = await client.get("http://localhost:8002/api/users/test-user-id")
            
            if response.status_code == 200:
                data = response.json()
                # 不应该包含密码字段
                assert "password" not in data, "密码字段泄露"
                assert "hashed_password" not in data, "哈希密码泄露"
                assert "secret" not in str(data).lower(), "敏感信息泄露"
    
    @pytest.mark.asyncio
    async def test_encryption(self):
        """测试数据加密"""
        # 测试敏感数据是否加密存储
        # 这里需要访问数据库或日志来验证
        # 简化版本，实际应该检查数据库中的加密数据
        pass
    
    @pytest.mark.asyncio
    async def test_https_enforcement(self):
        """测试HTTPS强制"""
        # 在生产环境中，应该强制使用HTTPS
        # 这里可以检查HTTP到HTTPS的重定向
        pass









