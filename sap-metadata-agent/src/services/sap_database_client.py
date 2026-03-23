"""
SAP数据库客户端
支持直接连接SAP数据库（HANA、SQL Server等）进行元数据查询
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class SAPDatabaseClient:
    """SAP数据库客户端"""
    
    def __init__(
        self,
        db_type: str,  # 'hdb' for HANA, 'mssql' for SQL Server
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        max_workers: int = 5
    ):
        """
        初始化SAP数据库客户端
        
        Args:
            db_type: 数据库类型 ('hdb' 或 'mssql')
            host: 数据库主机
            port: 数据库端口
            database: 数据库名
            user: 用户名
            password: 密码
            max_workers: 线程池最大工作线程数
        """
        self.db_type = db_type.lower()
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.max_workers = max_workers
        self.engine: Optional[Engine] = None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    def _build_connection_string(self) -> str:
        """构建数据库连接字符串"""
        if self.db_type == 'hdb':
            # SAP HANA连接字符串
            return f"hana://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == 'mssql':
            # SQL Server连接字符串
            return f"mssql+pyodbc://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def connect(self) -> bool:
        """
        连接到SAP数据库
        
        Returns:
            是否连接成功
        """
        try:
            connection_string = self._build_connection_string()
            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False
            )
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Successfully connected to SAP {self.db_type.upper()} database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SAP database: {e}", exc_info=True)
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
        if self.executor:
            self.executor.shutdown(wait=True)
    
    async def get_all_tables(self, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有表列表
        
        Args:
            schema: 模式名（可选）
            
        Returns:
            表信息列表
        """
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        def _get_tables():
            inspector = inspect(self.engine)
            if self.db_type == 'hdb':
                # HANA: 获取所有表
                if schema:
                    tables = inspector.get_table_names(schema=schema)
                else:
                    # 获取所有schema的表
                    schemas = inspector.get_schema_names()
                    all_tables = []
                    for sch in schemas:
                        if sch.upper() in ['SYS', 'SYSTEM']:  # 跳过系统schema
                            continue
                        try:
                            tables = inspector.get_table_names(schema=sch)
                            for table in tables:
                                all_tables.append({
                                    'table_name': table,
                                    'schema': sch,
                                    'full_name': f"{sch}.{table}"
                                })
                        except Exception as e:
                            logger.warning(f"Failed to get tables from schema {sch}: {e}")
                            continue
                    return all_tables
            else:  # mssql
                if schema:
                    tables = inspector.get_table_names(schema=schema)
                else:
                    tables = inspector.get_table_names()
                return [{'table_name': t, 'schema': schema or 'dbo', 'full_name': f"{schema or 'dbo'}.{t}"} for t in tables]
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _get_tables)
    
    async def get_table_structure(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            schema: 模式名（可选）
            
        Returns:
            表结构信息
        """
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        def _get_structure():
            inspector = inspect(self.engine)
            
            # 获取列信息
            columns = inspector.get_columns(table_name, schema=schema)
            
            # 获取主键
            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
            primary_key = pk_constraint.get('constrained_columns', []) if pk_constraint else []
            
            # 获取外键
            foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)
            
            # 获取索引
            indexes = inspector.get_indexes(table_name, schema=schema)
            
            return {
                'table_name': table_name,
                'schema': schema,
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col.get('nullable', True),
                        'default': col.get('default'),
                        'comment': col.get('comment')
                    }
                    for col in columns
                ],
                'primary_key': primary_key,
                'foreign_keys': [
                    {
                        'name': fk.get('name'),
                        'constrained_columns': fk.get('constrained_columns', []),
                        'referred_table': fk.get('referred_table'),
                        'referred_columns': fk.get('referred_columns', [])
                    }
                    for fk in foreign_keys
                ],
                'indexes': [
                    {
                        'name': idx.get('name'),
                        'columns': idx.get('column_names', []),
                        'unique': idx.get('unique', False)
                    }
                    for idx in indexes
                ]
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _get_structure)
    
    async def get_table_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        """
        获取表的行数
        
        Args:
            table_name: 表名
            schema: 模式名（可选）
            
        Returns:
            行数
        """
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        def _get_count():
            full_table_name = f"{schema}.{table_name}" if schema else table_name
            with self.engine.connect() as conn:
                if self.db_type == 'hdb':
                    result = conn.execute(text(f'SELECT COUNT(*) FROM "{full_table_name}"'))
                else:  # mssql
                    result = conn.execute(text(f'SELECT COUNT(*) FROM [{full_table_name}]'))
                return result.scalar()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _get_count)
    
    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            
        Returns:
            查询结果
        """
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        def _execute():
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _execute)
    
    async def get_sap_table_info(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        获取SAP表详细信息（包括SAP特定信息）
        
        Args:
            table_name: 表名
            schema: 模式名（可选）
            
        Returns:
            SAP表详细信息
        """
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        # 获取基础结构
        structure = await self.get_table_structure(table_name, schema)
        
        # 获取行数
        try:
            row_count = await self.get_table_row_count(table_name, schema)
        except Exception as e:
            logger.warning(f"Failed to get row count for {table_name}: {e}")
            row_count = None
        
        # 尝试获取SAP特定信息（表类型、描述等）
        sap_info = {}
        try:
            if self.db_type == 'hdb':
                # HANA: 查询系统表获取表类型和描述
                query = f"""
                SELECT TABLE_TYPE, COMMENTS 
                FROM SYS.TABLES 
                WHERE SCHEMA_NAME = '{schema or 'SAPR3'}' 
                AND TABLE_NAME = '{table_name}'
                """
                result = await self.execute_query(query)
                if result:
                    sap_info = {
                        'table_type': result[0].get('TABLE_TYPE'),
                        'description': result[0].get('COMMENTS')
                    }
        except Exception as e:
            logger.debug(f"Failed to get SAP-specific info for {table_name}: {e}")
        
        return {
            **structure,
            'row_count': row_count,
            'sap_info': sap_info
        }


