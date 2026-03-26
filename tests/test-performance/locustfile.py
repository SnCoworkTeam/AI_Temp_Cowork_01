"""
Locust性能测试配置
用于负载测试和压力测试
"""
from locust import HttpUser, task, between
import json


class MCPGatewayUser(HttpUser):
    """MCP Gateway用户负载测试"""
    wait_time = between(1, 3)
    host = "http://localhost:8000"
    
    @task(3)
    def health_check(self):
        """健康检查"""
        self.client.get("/api/health")
    
    @task(2)
    def list_tools(self):
        """列出工具"""
        self.client.get("/api/tools")
    
    @task(1)
    def execute_tool(self):
        """执行工具"""
        # 先获取工具列表
        response = self.client.get("/api/tools")
        if response.status_code == 200:
            tools = response.json()
            if tools and len(tools) > 0:
                tool_name = tools[0].get("name")
                self.client.post(
                    f"/api/tools/{tool_name}/execute",
                    json={"parameters": {}}
                )


class WorkflowEngineUser(HttpUser):
    """Workflow Engine用户负载测试"""
    wait_time = between(2, 5)
    host = "http://localhost:8001"
    
    @task(3)
    def health_check(self):
        """健康检查"""
        self.client.get("/api/health")
    
    @task(2)
    def list_workflows(self):
        """列出工作流"""
        self.client.get("/api/workflows")
    
    @task(1)
    def get_workflow(self):
        """获取工作流详情"""
        # 假设有一个测试工作流ID
        self.client.get("/api/workflows/test-workflow-id")


class AuthServiceUser(HttpUser):
    """Auth Service用户负载测试"""
    wait_time = between(1, 2)
    host = "http://localhost:8002"
    
    @task(5)
    def health_check(self):
        """健康检查"""
        self.client.get("/api/health")
    
    @task(3)
    def login(self):
        """登录"""
        self.client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )
    
    @task(1)
    def get_current_user(self):
        """获取当前用户"""
        # 需要token，这里简化处理
        headers = {"Authorization": "Bearer mock-token"}
        self.client.get("/api/users/me", headers=headers)


class KnowledgeBaseUser(HttpUser):
    """Knowledge Base用户负载测试"""
    wait_time = between(2, 4)
    host = "http://localhost:8004"
    
    @task(3)
    def health_check(self):
        """健康检查"""
        self.client.get("/api/health")
    
    @task(2)
    def list_documents(self):
        """列出文档"""
        self.client.get("/api/documents")
    
    @task(1)
    def search_documents(self):
        """搜索文档"""
        self.client.post(
            "/api/search/semantic",
            json={"query": "test query", "limit": 10}
        )









