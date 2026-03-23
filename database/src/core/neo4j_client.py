"""
Neo4j图数据库客户端
提供Neo4j连接管理和基本操作
"""
import logging
from typing import Optional, Dict, Any, List
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Neo4jSettings(BaseSettings):
    """Neo4j配置"""
    
    NEO4J_URI: str = "bolt://localhost:7687"  # 本地使用localhost，Docker容器内使用neo4j
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_password"
    NEO4J_DATABASE: str = "neo4j"
    
    # 连接池配置
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = 50
    NEO4J_CONNECTION_ACQUISITION_TIMEOUT: int = 60
    NEO4J_CONNECTION_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


_settings = None


def get_neo4j_settings() -> Neo4jSettings:
    """获取Neo4j配置（单例）"""
    global _settings
    if _settings is None:
        _settings = Neo4jSettings()
    return _settings


class Neo4jClient:
    """Neo4j客户端"""
    
    def __init__(self, settings: Optional[Neo4jSettings] = None):
        """
        初始化Neo4j客户端
        
        Args:
            settings: Neo4j配置，如果为None则使用默认配置
        """
        self.settings = settings or get_neo4j_settings()
        self.driver: Optional[AsyncDriver] = None
    
    async def connect(self) -> bool:
        """
        连接到Neo4j数据库
        
        Returns:
            是否连接成功
        """
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD),
                max_connection_pool_size=self.settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
                connection_acquisition_timeout=self.settings.NEO4J_CONNECTION_ACQUISITION_TIMEOUT,
                connection_timeout=self.settings.NEO4J_CONNECTION_TIMEOUT
            )
            
            # 测试连接
            async with self.driver.session(database=self.settings.NEO4J_DATABASE) as session:
                result = await session.run("RETURN 1 AS test")
                await result.single()
            
            logger.info(f"Successfully connected to Neo4j at {self.settings.NEO4J_URI}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}", exc_info=True)
            return False
    
    async def disconnect(self):
        """断开Neo4j连接"""
        if self.driver:
            await self.driver.close()
            self.driver = None
            logger.info("Disconnected from Neo4j")
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        执行Cypher查询
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            database: 数据库名称，如果为None则使用默认数据库
        
        Returns:
            查询结果列表
        """
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        
        database = database or self.settings.NEO4J_DATABASE
        parameters = parameters or {}
        
        async with self.driver.session(database=database) as session:
            result = await session.run(query, parameters)
            records = await result.data()
            return records
    
    async def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        执行写操作（在事务中）
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            database: 数据库名称
        
        Returns:
            操作结果
        """
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        
        database = database or self.settings.NEO4J_DATABASE
        parameters = parameters or {}
        
        async with self.driver.session(database=database) as session:
            result = await session.run(query, parameters)
            records = await result.data()
            # Neo4j异步会话会自动提交，不需要手动commit
            return records
    
    async def create_node(
        self,
        labels: List[str],
        properties: Dict[str, Any],
        database: Optional[str] = None
    ) -> str:
        """
        创建节点
        
        Args:
            labels: 节点标签列表
            properties: 节点属性
            database: 数据库名称
        
        Returns:
            节点ID（内部ID）
        """
        labels_str = ":".join(labels) if labels else ""
        props_str = ", ".join([f"n.{k} = ${k}" for k in properties.keys()])
        
        query = f"""
        CREATE (n{":" + labels_str if labels_str else ""})
        SET {props_str}
        RETURN id(n) AS node_id
        """
        
        result = await self.execute_write(query, properties, database)
        if result:
            return str(result[0]["node_id"])
        raise RuntimeError("Failed to create node")
    
    async def update_node(
        self,
        node_id: str,
        labels: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> str:
        """
        更新节点
        
        Args:
            node_id: 节点ID（内部ID）
            labels: 节点标签列表（可选）
            properties: 节点属性
            database: 数据库名称
        
        Returns:
            节点ID
        """
        if not properties:
            return node_id
        
        labels_str = ""
        if labels:
            labels_str = ":".join(labels)
        
        props_str = ", ".join([f"n.{k} = ${k}" for k in properties.keys()])
        
        query = f"""
        MATCH (n)
        WHERE id(n) = $node_id
        {f'SET n:{labels_str}' if labels_str else ''}
        SET {props_str}
        RETURN id(n) AS node_id
        """
        
        params = {
            "node_id": int(node_id),
            **properties
        }
        
        result = await self.execute_write(query, params, database)
        if result:
            return str(result[0]["node_id"])
        raise RuntimeError("Failed to update node")
    
    async def find_node_by_uuid(
        self,
        uuid: str,
        labels: Optional[List[str]] = None,
        database: Optional[str] = None
    ) -> Optional[str]:
        """
        根据UUID查找节点
        
        Args:
            uuid: 实体UUID
            labels: 节点标签列表（可选）
            database: 数据库名称
        
        Returns:
            节点ID（内部ID），如果不存在则返回None
        """
        labels_str = ""
        if labels:
            labels_str = ":".join(labels)
        
        query = f"""
        MATCH (n{":" + labels_str if labels_str else ""})
        WHERE n.uuid = $uuid
        RETURN id(n) AS node_id
        LIMIT 1
        """
        
        result = await self.execute_query(query, {"uuid": uuid}, database)
        if result:
            return str(result[0]["node_id"])
        return None
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> str:
        """
        创建关系（如果不存在）
        
        Args:
            source_id: 源节点ID（内部ID）
            target_id: 目标节点ID（内部ID）
            rel_type: 关系类型
            properties: 关系属性
            database: 数据库名称
        
        Returns:
            关系ID
        """
        props_str = ""
        if properties:
            props_str = ", ".join([f"r.{k} = ${k}" for k in properties.keys()])
            props_str = f"SET {props_str}"
        
        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $source_id AND id(b) = $target_id
        MERGE (a)-[r:{rel_type}]->(b)
        {props_str}
        RETURN id(r) AS rel_id
        """
        
        params = {
            "source_id": int(source_id),
            "target_id": int(target_id),
            **(properties or {})
        }
        
        result = await self.execute_write(query, params, database)
        if result:
            return str(result[0]["rel_id"])
        raise RuntimeError("Failed to create relationship")
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            result = await self.execute_query("RETURN 1 AS test")
            return len(result) > 0
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()


# 全局客户端实例
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """获取Neo4j客户端（单例）"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client

