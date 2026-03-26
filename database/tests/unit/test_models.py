"""
数据模型测试
"""
import pytest
import uuid
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.base import Base, TimestampMixin
from database.src.models.user_models import User, Role, Permission, UserStatus
from database.src.models.knowledge_models import Document, DocumentChunk, DocumentType, DocumentStatus
from database.src.models.workflow_models import WorkflowDefinition, WorkflowExecution, WorkflowNode
from database.src.models.mcp_models import MCPTool, MCPToolExecution


@pytest.mark.unit
class TestBaseModel:
    """基础模型测试"""
    
    def test_timestamp_mixin(self, db_session):
        """测试时间戳混入"""
        # 创建一个简单的测试模型
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.ext.declarative import declarative_base
        
        TestBase = declarative_base()
        
        class TestModel(TestBase, TimestampMixin):
            __tablename__ = "test_model"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        TestBase.metadata.create_all(db_session.bind)
        
        test_obj = TestModel(name="test")
        db_session.add(test_obj)
        db_session.commit()
        
        assert test_obj.created_at is not None
        assert test_obj.updated_at is not None
    
    def test_base_model_to_dict(self, db_session):
        """测试BaseModel的to_dict方法"""
        user = User(
            username="dict_test",
            email="dict@example.com",
            password_hash="hashed"
        )
        db_session.add(user)
        db_session.commit()
        
        # 测试to_dict
        user_dict = user.to_dict()
        assert isinstance(user_dict, dict)
        assert user_dict["username"] == "dict_test"
        assert user_dict["email"] == "dict@example.com"
        assert "id" in user_dict
        assert "created_at" in user_dict
        assert "updated_at" in user_dict
    
    def test_base_model_update_from_dict(self, db_session):
        """测试BaseModel的update_from_dict方法"""
        user = User(
            username="update_dict_test",
            email="updatedict@example.com",
            password_hash="hashed"
        )
        db_session.add(user)
        db_session.commit()
        
        # 测试update_from_dict
        user.update_from_dict({
            "full_name": "Updated Name",
            "avatar_url": "http://example.com/avatar.jpg"
        })
        db_session.commit()
        
        assert user.full_name == "Updated Name"
        assert user.avatar_url == "http://example.com/avatar.jpg"


@pytest.mark.unit
class TestUserModel:
    """用户模型测试"""
    
    def test_user_creation(self, db_session):
        """测试创建用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.status == UserStatus.ACTIVE  # 默认状态
        assert user.created_at is not None
    
    def test_user_status_enum(self):
        """测试用户状态枚举"""
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.INACTIVE == "inactive"
        assert UserStatus.SUSPENDED == "suspended"
        assert UserStatus.DELETED == "deleted"
    
    def test_user_with_roles(self, db_session):
        """测试用户与角色的关联"""
        # 创建角色
        role = Role(
            code="admin",
            name="Administrator",
            description="Admin role"
        )
        db_session.add(role)
        db_session.flush()
        
        # 创建用户
        user = User(
            username="admin_user",
            email="admin@example.com",
            password_hash="hashed"
        )
        user.roles.append(role)
        db_session.add(user)
        db_session.commit()
        
        assert len(user.roles) == 1
        assert user.roles[0].code == "admin"
    
    def test_role_with_permissions(self, db_session):
        """测试角色与权限的关联"""
        # 创建权限
        permission = Permission(
            code="read:users",
            name="Read Users",
            resource="users",
            action="read"
        )
        db_session.add(permission)
        db_session.flush()
        
        # 创建角色
        role = Role(
            code="viewer",
            name="Viewer",
            description="Viewer role"
        )
        role.permissions.append(permission)
        db_session.add(role)
        db_session.commit()
        
        assert len(role.permissions) == 1
        assert role.permissions[0].code == "read:users"


@pytest.mark.unit
class TestKnowledgeModels:
    """知识库模型测试"""
    
    def test_document_creation(self, db_session):
        """测试创建文档"""
        doc = Document(
            filename="test_document.txt",
            file_type=DocumentType.TEXT,
            file_size=100,
            file_path="/path/to/test_document.txt",
            status=DocumentStatus.PROCESSED
        )
        db_session.add(doc)
        db_session.commit()
        
        assert doc.id is not None
        assert doc.filename == "test_document.txt"
        assert doc.file_type == DocumentType.TEXT
        assert doc.created_at is not None
    
    def test_document_with_chunks(self, db_session):
        """测试文档与块的关联"""
        # 创建文档
        doc = Document(
            filename="test_document.txt",
            file_type=DocumentType.TEXT,
            file_size=100,
            file_path="/path/to/test_document.txt",
            status=DocumentStatus.PROCESSED
        )
        db_session.add(doc)
        db_session.flush()
        
        # 创建多个块
        for i in range(3):
            chunk = DocumentChunk(
                document_id=doc.id,
                content=f"Chunk {i}",
                chunk_index=i
            )
            db_session.add(chunk)
        
        db_session.commit()
        
        assert len(doc.chunks) == 3
        assert doc.chunks[0].chunk_index == 0
    
    def test_chunk_creation(self, db_session):
        """测试创建文档块"""
        # 先创建文档
        doc = Document(
            filename="test_document.txt",
            file_type=DocumentType.TEXT,
            file_size=100,
            file_path="/path/to/test_document.txt",
            status=DocumentStatus.PROCESSED
        )
        db_session.add(doc)
        db_session.flush()
        
        chunk = DocumentChunk(
            document_id=doc.id,
            content="Test chunk",
            chunk_index=0
        )
        db_session.add(chunk)
        db_session.commit()
        
        assert chunk.id is not None
        assert chunk.document_id == doc.id
        assert chunk.chunk_index == 0


@pytest.mark.unit
class TestWorkflowModels:
    """工作流模型测试"""
    
    def test_workflow_creation(self, db_session):
        """测试创建工作流"""
        from database.src.models.workflow_models import WorkflowStatus
        workflow = WorkflowDefinition(
            name="test_workflow",
            description="Test workflow description",
            status=WorkflowStatus.DRAFT
        )
        db_session.add(workflow)
        db_session.commit()
        
        assert workflow.id is not None
        assert workflow.name == "test_workflow"
        assert workflow.status == WorkflowStatus.DRAFT
    
    def test_workflow_execution(self, db_session):
        """测试工作流执行"""
        from database.src.models.workflow_models import WorkflowStatus, ExecutionStatus
        # 先创建工作流
        workflow = WorkflowDefinition(
            name="exec_workflow",
            status=WorkflowStatus.ACTIVE
        )
        db_session.add(workflow)
        db_session.flush()
        
        # 创建执行记录
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            start_time=datetime.now()
        )
        db_session.add(execution)
        db_session.commit()
        
        assert execution.id is not None
        assert execution.workflow_id == workflow.id
        assert execution.status == ExecutionStatus.RUNNING


@pytest.mark.unit
class TestMCPModels:
    """MCP模型测试"""
    
    def test_mcp_tool_creation(self, db_session):
        """测试创建MCP工具"""
        from database.src.models.mcp_models import ToolType, ToolStatus
        tool = MCPTool(
            name="Test Tool",
            description="Test tool description",
            tool_type=ToolType.CUSTOM,
            status=ToolStatus.ACTIVE
        )
        db_session.add(tool)
        db_session.commit()
        
        assert tool.id is not None
        assert tool.name == "Test Tool"

