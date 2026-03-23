"""
数据库模块测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestDatabase:
    """数据库模块测试"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """模拟数据库管理器"""
        db_manager = MagicMock()
        db_manager.create_engine = MagicMock(return_value=MagicMock())
        db_manager.test_connection = MagicMock(return_value=True)
        db_manager.dispose = MagicMock()
        return db_manager
    
    @pytest.fixture
    def mock_get_database_manager(self):
        """模拟获取数据库管理器"""
        return MagicMock()
    
    def test_init_database_success(self, mock_db_manager):
        """测试初始化数据库成功"""
        with patch('src.core.database.get_database_manager', return_value=mock_db_manager), \
             patch('src.core.database.init_session_factory'):
            from src.core.database import init_database
            
            result = init_database()
            
            assert result is True
            mock_db_manager.create_engine.assert_called_once()
            mock_db_manager.test_connection.assert_called_once()
    
    def test_init_database_connection_failure(self, mock_db_manager):
        """测试初始化数据库（连接失败）"""
        mock_db_manager.test_connection.return_value = False
        
        with patch('src.core.database.get_database_manager', return_value=mock_db_manager), \
             patch('src.core.database.init_session_factory'):
            from src.core.database import init_database
            
            result = init_database()
            
            assert result is False
    
    def test_init_database_exception(self, mock_db_manager):
        """测试初始化数据库（异常）"""
        mock_db_manager.create_engine.side_effect = Exception("Database error")
        
        with patch('src.core.database.get_database_manager', return_value=mock_db_manager), \
             patch('src.core.database.init_session_factory'):
            from src.core.database import init_database
            
            result = init_database()
            
            assert result is False
    
    def test_close_database_with_manager(self):
        """测试关闭数据库（有管理器）"""
        mock_db_manager = MagicMock()
        mock_db_manager.dispose = MagicMock()
        
        with patch('src.core.database._db_manager', mock_db_manager):
            from src.core.database import close_database
            
            close_database()
            
            mock_db_manager.dispose.assert_called_once()
    
    def test_close_database_without_manager(self):
        """测试关闭数据库（无管理器）"""
        with patch('src.core.database._db_manager', None):
            from src.core.database import close_database
            
            # 应该不会抛出异常
            close_database()
    
    def test_get_database_engine(self):
        """测试获取数据库引擎"""
        mock_engine = MagicMock()
        
        with patch('src.core.database.get_engine', return_value=mock_engine):
            from src.core.database import get_database_engine
            
            result = get_database_engine()
            
            assert result == mock_engine
    
    def test_get_redis(self):
        """测试获取Redis客户端"""
        mock_redis = MagicMock()
        
        with patch('src.core.database.get_redis_client', return_value=mock_redis):
            from src.core.database import get_redis
            
            result = get_redis()
            
            assert result == mock_redis
    
    def test_get_async_redis(self):
        """测试获取异步Redis客户端"""
        mock_async_redis = MagicMock()
        
        with patch('src.core.database.get_async_redis_client', return_value=mock_async_redis):
            from src.core.database import get_async_redis
            
            result = get_async_redis()
            
            assert result == mock_async_redis


@pytest.mark.unit
class TestDatabaseDependencies:
    """数据库依赖注入测试"""
    
    @pytest.fixture
    def mock_session_local(self):
        """模拟SessionLocal"""
        session = MagicMock()
        session.close = MagicMock()
        return session
    
    def test_get_db_success(self, mock_session_local):
        """测试获取数据库会话成功"""
        with patch('src.dependencies.database.SessionLocal', return_value=mock_session_local):
            from src.dependencies.database import get_db
            
            # get_db是一个生成器，需要迭代
            db_gen = get_db()
            session = next(db_gen)
            
            assert session == mock_session_local
            
            # 测试finally块中的close
            try:
                next(db_gen)
            except StopIteration:
                pass
            
            mock_session_local.close.assert_called_once()
    
    def test_get_db_exception_handling(self, mock_session_local):
        """测试获取数据库会话（异常处理）"""
        mock_session_local.close = MagicMock()
        
        with patch('src.dependencies.database.SessionLocal', return_value=mock_session_local):
            from src.dependencies.database import get_db
            
            db_gen = get_db()
            session = next(db_gen)
            
            # 模拟异常
            try:
                raise Exception("Test error")
            except Exception:
                # 确保finally块会执行
                try:
                    next(db_gen)
                except StopIteration:
                    pass
            
            # close应该被调用
            mock_session_local.close.assert_called_once()
