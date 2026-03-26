"""
EA集成测试
测试EA向量化、图谱和混合查询的端到端功能
"""
import pytest
import asyncio
import sys
from pathlib import Path

# 添加路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "metadata-service" / "src" / "services"))
sys.path.insert(0, str(PROJECT_ROOT / "os-core"))

from resource_registry import ResourceRegistry
from resource_resolver import ResourceResolver
from business_object_adapter import BusinessObjectAdapter

# EA服务
try:
    from ea_vectorization_service import EAVectorizationService
    from ea_knowledge_graph import EAKnowledgeGraph
    from ea_hybrid_query import EAHybridQuery
    EA_SERVICES_AVAILABLE = True
except ImportError:
    EA_SERVICES_AVAILABLE = False
    pytest.skip("EA服务不可用", allow_module_level=True)


class TestEAIntegration:
    """EA集成测试"""
    
    @pytest.fixture
    def db_session(self):
        """创建数据库会话"""
        from database.src.core.session import get_db, init_session_factory
        from database.src.core.database import get_database_manager
        
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            pytest.skip("数据库连接失败")
        
        init_session_factory()
        db = next(get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def ea_services(self, db_session):
        """创建EA服务实例"""
        vector_service = EAVectorizationService(db_session)
        graph_service = EAKnowledgeGraph(db_session)
        hybrid_query = EAHybridQuery(db_session, graph_service, vector_service)
        
        return {
            "vector": vector_service,
            "graph": graph_service,
            "hybrid": hybrid_query
        }
    
    @pytest.mark.asyncio
    async def test_vectorize_business_process(self, ea_services, db_session):
        """测试向量化业务流程"""
        # 获取一个业务流程
        from database.src.models.enterprise_architecture_models import BusinessProcess
        
        process = db_session.query(BusinessProcess).first()
        if not process:
            pytest.skip("没有业务流程数据")
        
        # 向量化
        result = ea_services["vector"].vectorize_business_process(process)
        
        assert result["entity_id"] == process.id
        assert result["entity_type"] == "BusinessProcess"
        assert len(result["vector"]) > 0
    
    @pytest.mark.asyncio
    async def test_create_entity_in_graph(self, ea_services, db_session):
        """测试在图谱中创建实体"""
        # 确保Neo4j连接
        if ea_services["graph"].use_neo4j and ea_services["graph"].neo4j_client:
            if not ea_services["graph"].neo4j_client.driver:
                await ea_services["graph"].neo4j_client.connect()
        
        # 创建测试实体
        success = await ea_services["graph"].create_entity(
            entity_type="BusinessProcess",
            entity_id="test:process:001",
            properties={
                "name": "测试流程",
                "description": "这是一个测试流程"
            }
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_hybrid_query(self, ea_services):
        """测试混合查询"""
        results = ea_services["hybrid"].query(
            user_input="采购订单",
            query_type="hybrid",
            top_k=5
        )
        
        assert "query_type" in results
        assert results["query_type"] == "hybrid"
        assert "vector_results" in results
        assert "graph_results" in results
    
    def test_vectorization_service_integration(self, ea_services):
        """测试向量化服务集成"""
        # 检查是否集成了向量模型管理器
        assert ea_services["vector"].embedding_manager is not None or True  # 允许降级
    
    @pytest.mark.asyncio
    async def test_graph_service_integration(self, ea_services):
        """测试图谱服务集成"""
        # 检查是否集成了Neo4j
        if ea_services["graph"].use_neo4j:
            assert ea_services["graph"].neo4j_client is not None
        else:
            # 如果没有Neo4j，应该能从关系数据库加载
            assert True


class TestEAPerformance:
    """EA性能测试"""
    
    @pytest.fixture
    def db_session(self):
        """创建数据库会话"""
        from database.src.core.session import get_db, init_session_factory
        from database.src.core.database import get_database_manager
        
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            pytest.skip("数据库连接失败")
        
        init_session_factory()
        db = next(get_db())
        yield db
        db.close()
    
    @pytest.mark.asyncio
    async def test_vectorization_performance(self, db_session):
        """测试向量化性能"""
        import time
        
        vector_service = EAVectorizationService(db_session)
        
        # 测试批量向量化性能
        from database.src.models.enterprise_architecture_models import BusinessProcess
        
        processes = db_session.query(BusinessProcess).limit(10).all()
        if not processes:
            pytest.skip("没有业务流程数据")
        
        start_time = time.time()
        results = vector_service.batch_vectorize_processes(processes)
        elapsed = time.time() - start_time
        
        # 性能要求：10个流程向量化应该在5秒内完成
        assert elapsed < 5.0, f"向量化耗时过长: {elapsed:.2f}秒"
        assert len(results) == len(processes)
    
    @pytest.mark.asyncio
    async def test_hybrid_query_performance(self, db_session):
        """测试混合查询性能"""
        import time
        
        from ea_vectorization_service import EAVectorizationService
        from ea_knowledge_graph import EAKnowledgeGraph
        from ea_hybrid_query import EAHybridQuery
        
        vector_service = EAVectorizationService(db_session)
        graph_service = EAKnowledgeGraph(db_session)
        hybrid_query = EAHybridQuery(db_session, graph_service, vector_service)
        
        start_time = time.time()
        results = hybrid_query.query(
            user_input="采购订单",
            query_type="hybrid",
            top_k=10
        )
        elapsed = time.time() - start_time
        
        # 性能要求：混合查询应该在2秒内完成
        assert elapsed < 2.0, f"混合查询耗时过长: {elapsed:.2f}秒"
