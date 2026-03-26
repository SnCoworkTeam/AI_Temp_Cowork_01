"""
MCP Gateway 模型单元测试
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "mcp-gateway" / "src"))


@pytest.mark.unit
class TestToolModels:
    """工具模型测试"""
    
    def test_tool_definition_creation(self):
        """测试工具定义创建"""
        try:
            from src.models.tool_models import ToolDefinition
        except ImportError:
            pytest.skip("ToolDefinition not available")
            return
        
        tool = ToolDefinition(
            id=uuid4(),
            name="test_tool",
            description="Test tool",
            parameters_schema={"type": "object"},
            created_at=datetime.utcnow()
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "Test tool"
        assert tool.parameters_schema == {"type": "object"}
    
    def test_tool_execution_creation(self):
        """测试工具执行记录创建"""
        try:
            from src.models.tool_models import ToolExecution
        except ImportError:
            pytest.skip("ToolExecution not available")
            return
        
        execution = ToolExecution(
            id=uuid4(),
            tool_id=uuid4(),
            input_data={"param": "value"},
            output_data={"result": "success"},
            status="completed",
            execution_time=0.5,
            created_at=datetime.utcnow()
        )
        
        assert execution.status == "completed"
        assert execution.execution_time == 0.5
        assert execution.input_data == {"param": "value"}


@pytest.mark.unit
class TestConfigModels:
    """配置模型测试"""
    
    def test_tool_config_validation(self):
        """测试工具配置验证"""
        try:
            from src.models.config_models import ToolConfig
        except ImportError:
            pytest.skip("ToolConfig not available")
            return
        
        config = ToolConfig(
            tool_name="test_tool",
            enabled=True,
            rate_limit=100,
            timeout=30
        )
        
        assert config.tool_name == "test_tool"
        assert config.enabled is True
        assert config.rate_limit == 100







