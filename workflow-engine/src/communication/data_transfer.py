"""
智能体数据传递机制实现
提供智能体之间的数据传递、格式转换、序列化和缓存功能
"""

import asyncio
import json
import pickle
import gzip
import base64
from typing import Dict, Any, Optional, Union, List, Type, TypeVar
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import logging
from abc import ABC, abstractmethod

from shared_libs.luminaos_common.schemas.agent_communication import (
    DataTransferMessage, AgentMessage, MessageHeader, MessageType,
    MessagePriority, MessageDeliveryMode
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DataFormat(str, Enum):
    """数据格式枚举"""
    JSON = "json"
    PICKLE = "pickle"
    XML = "xml"
    YAML = "yaml"
    CSV = "csv"
    BINARY = "binary"
    COMPRESSED = "compressed"
    ENCRYPTED = "encrypted"


class CompressionType(str, Enum):
    """压缩类型枚举"""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"
    BZIP2 = "bzip2"


class EncryptionType(str, Enum):
    """加密类型枚举"""
    NONE = "none"
    AES256 = "aes256"
    RSA = "rsa"
    HYBRID = "hybrid"


@dataclass
class DataTransferConfig:
    """数据传递配置"""
    max_size: int = 10 * 1024 * 1024  # 10MB
    enable_compression: bool = True
    compression_type: CompressionType = CompressionType.GZIP
    compression_threshold: int = 1024  # 1KB
    enable_encryption: bool = False
    encryption_type: EncryptionType = EncryptionType.NONE
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1小时
    retry_count: int = 3
    timeout: float = 30.0


@dataclass
class DataPacket:
    """数据包"""
    packet_id: str
    source_node: str
    target_node: str
    data_type: str
    content: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    format: DataFormat = DataFormat.JSON
    compression: CompressionType = CompressionType.NONE
    encryption: EncryptionType = EncryptionType.NONE
    checksum: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    size: int = 0


class DataSerializer(ABC):
    """数据序列化器接口"""

    @abstractmethod
    def serialize(self, data: Any) -> bytes:
        """序列化数据"""
        pass

    @abstractmethod
    def deserialize(self, data: bytes, target_type: Type[T] = None) -> T:
        """反序列化数据"""
        pass

    @abstractmethod
    def get_format(self) -> DataFormat:
        """获取数据格式"""
        pass


class JSONSerializer(DataSerializer):
    """JSON序列化器"""

    def serialize(self, data: Any) -> bytes:
        try:
            return json.dumps(data, default=self._json_serializer, ensure_ascii=False).encode('utf-8')
        except Exception as e:
            logger.error(f"JSON序列化失败: {e}")
            raise

    def deserialize(self, data: bytes, target_type: Type[T] = None) -> T:
        try:
            decoded = json.loads(data.decode('utf-8'))
            if target_type and hasattr(target_type, 'parse_obj'):
                # Pydantic模型
                return target_type.parse_obj(decoded)
            return decoded
        except Exception as e:
            logger.error(f"JSON反序列化失败: {e}")
            raise

    def get_format(self) -> DataFormat:
        return DataFormat.JSON

    def _json_serializer(self, obj):
        """JSON序列化辅助函数"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class PickleSerializer(DataSerializer):
    """Pickle序列化器"""

    def serialize(self, data: Any) -> bytes:
        try:
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Pickle序列化失败: {e}")
            raise

    def deserialize(self, data: bytes, target_type: Type[T] = None) -> T:
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Pickle反序列化失败: {e}")
            raise

    def get_format(self) -> DataFormat:
        return DataFormat.PICKLE


class DataCompressor:
    """数据压缩器"""

    @staticmethod
    def compress(data: bytes, compression_type: CompressionType) -> bytes:
        """压缩数据"""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            return gzip.compress(data)
        elif compression_type == CompressionType.ZLIB:
            import zlib
            return zlib.compress(data)
        elif compression_type == CompressionType.BZIP2:
            import bz2
            return bz2.compress(data)
        else:
            raise ValueError(f"不支持的压缩类型: {compression_type}")

    @staticmethod
    def decompress(data: bytes, compression_type: CompressionType) -> bytes:
        """解压数据"""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            return gzip.decompress(data)
        elif compression_type == CompressionType.ZLIB:
            import zlib
            return zlib.decompress(data)
        elif compression_type == CompressionType.BZIP2:
            import bz2
            return bz2.decompress(data)
        else:
            raise ValueError(f"不支持的压缩类型: {compression_type}")


class DataEncryptor:
    """数据加密器"""

    def __init__(self, encryption_key: Optional[bytes] = None):
        self.encryption_key = encryption_key or b"default_key_32bytes_long!!!!!"

    def encrypt(self, data: bytes, encryption_type: EncryptionType) -> bytes:
        """加密数据"""
        if encryption_type == EncryptionType.NONE:
            return data
        elif encryption_type == EncryptionType.AES256:
            return self._aes_encrypt(data)
        else:
            raise ValueError(f"不支持的加密类型: {encryption_type}")

    def decrypt(self, data: bytes, encryption_type: EncryptionType) -> bytes:
        """解密数据"""
        if encryption_type == EncryptionType.NONE:
            return data
        elif encryption_type == EncryptionType.AES256:
            return self._aes_decrypt(data)
        else:
            raise ValueError(f"不支持的加密类型: {encryption_type}")

    def _aes_encrypt(self, data: bytes) -> bytes:
        """AES加密（简化实现）"""
        # 实际项目中应该使用专业的加密库如cryptography
        from cryptography.fernet import Fernet
        f = Fernet(base64.urlsafe_b64encode(self.encryption_key))
        return f.encrypt(data)

    def _aes_decrypt(self, data: bytes) -> bytes:
        """AES解密（简化实现）"""
        from cryptography.fernet import Fernet
        f = Fernet(base64.urlsafe_b64encode(self.encryption_key))
        return f.decrypt(data)


class DataCache:
    """数据缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, datetime] = {}
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if key not in self.cache:
            return None

        # 检查TTL
        if self._is_expired(key):
            self._remove(key)
            return None

        self.access_times[key] = datetime.now()
        return self.cache[key]['data']

    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """设置缓存数据"""
        # 检查缓存大小
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        self.cache[key] = {
            'data': data,
            'created_at': datetime.now(),
            'ttl': ttl or self.ttl
        }
        self.access_times[key] = datetime.now()

    def _is_expired(self, key: str) -> bool:
        """检查是否过期"""
        if key not in self.cache:
            return True

        item = self.cache[key]
        age = (datetime.now() - item['created_at']).total_seconds()
        return age > item['ttl']

    def _remove(self, key: str):
        """移除缓存项"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]

    def _evict_lru(self):
        """驱逐最近最少使用的缓存项"""
        if not self.access_times:
            return

        lru_key = min(self.access_times, key=self.access_times.get)
        self._remove(lru_key)

    def clear_expired(self):
        """清理过期缓存"""
        expired_keys = [key for key in self.cache if self._is_expired(key)]
        for key in expired_keys:
            self._remove(key)


class DataTransferManager:
    """数据传递管理器"""

    def __init__(self, config: DataTransferConfig = None):
        self.config = config or DataTransferConfig()
        self.serializers: Dict[DataFormat, DataSerializer] = {
            DataFormat.JSON: JSONSerializer(),
            DataFormat.PICKLE: PickleSerializer()
        }
        self.compressor = DataCompressor()
        self.encryptor = DataEncryptor()
        self.cache = DataCache(ttl=self.config.cache_ttl)
        self.transfer_history: List[Dict[str, Any]] = []

    def register_serializer(self, format_type: DataFormat, serializer: DataSerializer):
        """注册序列化器"""
        self.serializers[format_type] = serializer
        logger.info(f"注册序列化器: {format_type}")

    async def prepare_data_packet(
        self,
        source_node: str,
        target_node: str,
        data: Any,
        data_type: str = "general",
        format_type: DataFormat = DataFormat.JSON,
        metadata: Dict[str, Any] = None
    ) -> DataPacket:
        """准备数据包"""

        packet_id = self._generate_packet_id(source_node, target_node, data)

        # 检查缓存
        if self.config.enable_caching:
            cached_packet = self.cache.get(packet_id)
            if cached_packet:
                logger.info(f"使用缓存数据包: {packet_id}")
                return cached_packet

        # 序列化数据
        serializer = self.serializers.get(format_type)
        if not serializer:
            raise ValueError(f"不支持的数据格式: {format_type}")

        serialized_data = serializer.serialize(data)

        # 压缩数据
        compression_type = CompressionType.NONE
        if (self.config.enable_compression and
            len(serialized_data) > self.config.compression_threshold):
            compression_type = self.config.compression_type
            serialized_data = self.compressor.compress(serialized_data, compression_type)

        # 加密数据
        encryption_type = EncryptionType.NONE
        if self.config.enable_encryption:
            encryption_type = self.config.encryption_type
            serialized_data = self.encryptor.encrypt(serialized_data, encryption_type)

        # 计算校验和
        checksum = self._calculate_checksum(serialized_data)

        # 创建数据包
        packet = DataPacket(
            packet_id=packet_id,
            source_node=source_node,
            target_node=target_node,
            data_type=data_type,
            content=base64.b64encode(serialized_data).decode('utf-8'),
            metadata=metadata or {},
            format=format_type,
            compression=compression_type,
            encryption=encryption_type,
            checksum=checksum,
            size=len(serialized_data)
        )

        # 缓存数据包
        if self.config.enable_caching:
            self.cache.set(packet_id, packet)

        return packet

    async def extract_data_packet(
        self,
        packet: DataPacket,
        target_type: Type[T] = None
    ) -> T:
        """解析数据包"""

        try:
            # 解码数据
            serialized_data = base64.b64decode(packet.content)

            # 验证校验和
            if packet.checksum:
                expected_checksum = self._calculate_checksum(serialized_data)
                if expected_checksum != packet.checksum:
                    raise ValueError(f"数据包校验失败: {packet.packet_id}")

            # 解密数据
            if packet.encryption != EncryptionType.NONE:
                serialized_data = self.encryptor.decrypt(serialized_data, packet.encryption)

            # 解压数据
            if packet.compression != CompressionType.NONE:
                serialized_data = self.compressor.decompress(serialized_data, packet.compression)

            # 反序列化数据
            serializer = self.serializers.get(packet.format)
            if not serializer:
                raise ValueError(f"不支持的数据格式: {packet.format}")

            data = serializer.deserialize(serialized_data, target_type)

            # 记录传输历史
            self._record_transfer_history(packet, success=True)

            return data

        except Exception as e:
            logger.error(f"解析数据包失败 {packet.packet_id}: {e}")
            self._record_transfer_history(packet, success=False, error=str(e))
            raise

    async def send_data(
        self,
        source_node: str,
        target_node: str,
        data: Any,
        data_type: str = "general",
        format_type: DataFormat = DataFormat.JSON,
        metadata: Dict[str, Any] = None,
        message_router=None
    ) -> bool:
        """发送数据"""

        try:
            # 准备数据包
            packet = await self.prepare_data_packet(
                source_node, target_node, data, data_type, format_type, metadata
            )

            # 检查数据大小
            if packet.size > self.config.max_size:
                raise ValueError(f"数据包过大: {packet.size} > {self.config.max_size}")

            # 创建传输消息
            transfer_message = AgentMessage(
                header=MessageHeader(
                    message_type=MessageType.DATA_TRANSFER,
                    source=source_node,
                    destination=target_node,
                    priority=MessagePriority.NORMAL
                ),
                payload=DataTransferMessage(
                    from_node=source_node,
                    to_node=target_node,
                    data_type=data_type,
                    data_content=packet.__dict__,
                    data_schema=metadata.get('schema') if metadata else None,
                    compression=packet.compression.value,
                    encryption=packet.encryption.value
                )
            )

            # 发送消息
            if message_router:
                success = await message_router.route_message(transfer_message)
            else:
                # 模拟发送
                success = True

            logger.info(f"数据发送完成: {packet.packet_id} -> {success}")
            return success

        except Exception as e:
            logger.error(f"数据发送失败: {e}")
            return False

    async def receive_data(
        self,
        transfer_message: DataTransferMessage,
        target_type: Type[T] = None
    ) -> T:
        """接收数据"""

        try:
            # 从消息中提取数据包
            packet_data = transfer_message.data_content
            packet = DataPacket(**packet_data)

            # 解析数据包
            data = await self.extract_data_packet(packet, target_type)

            logger.info(f"数据接收完成: {packet.packet_id}")
            return data

        except Exception as e:
            logger.error(f"数据接收失败: {e}")
            raise

    def _generate_packet_id(self, source_node: str, target_node: str, data: Any) -> str:
        """生成数据包ID"""
        content = f"{source_node}-{target_node}-{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()

    def _calculate_checksum(self, data: bytes) -> str:
        """计算校验和"""
        return hashlib.sha256(data).hexdigest()

    def _record_transfer_history(
        self,
        packet: DataPacket,
        success: bool,
        error: str = None
    ):
        """记录传输历史"""
        history_item = {
            'packet_id': packet.packet_id,
            'source_node': packet.source_node,
            'target_node': packet.target_node,
            'data_type': packet.data_type,
            'size': packet.size,
            'format': packet.format.value,
            'compression': packet.compression.value,
            'encryption': packet.encryption.value,
            'success': success,
            'error': error,
            'timestamp': datetime.now()
        }

        self.transfer_history.append(history_item)

        # 限制历史记录大小
        if len(self.transfer_history) > 1000:
            self.transfer_history = self.transfer_history[-500:]  # 保留最近500条

    def get_transfer_statistics(self, time_window: int = 3600) -> Dict[str, Any]:
        """获取传输统计"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        recent_transfers = [
            item for item in self.transfer_history
            if item['timestamp'] > cutoff_time
        ]

        total_transfers = len(recent_transfers)
        successful_transfers = sum(1 for item in recent_transfers if item['success'])
        total_size = sum(item['size'] for item in recent_transfers)

        return {
            'time_window_seconds': time_window,
            'total_transfers': total_transfers,
            'successful_transfers': successful_transfers,
            'failed_transfers': total_transfers - successful_transfers,
            'success_rate': successful_transfers / total_transfers if total_transfers > 0 else 0,
            'total_bytes_transferred': total_size,
            'average_transfer_size': total_size / total_transfers if total_transfers > 0 else 0,
            'transfers_per_minute': total_transfers / (time_window / 60) if time_window > 0 else 0
        }

    def cleanup_cache(self):
        """清理过期缓存"""
        self.cache.clear_expired()

    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            'cache_size': len(self.cache.cache),
            'max_cache_size': self.cache.max_size,
            'cache_utilization': len(self.cache.cache) / self.cache.max_size,
            'cache_hit_rate': 0.0  # 需要实现命中率追踪
        }


# ==================== 数据传递工具函数 ====================

class DataPipeline:
    """数据管道"""

    def __init__(self, transfer_manager: DataTransferManager):
        self.transfer_manager = transfer_manager
        self.pipeline_stages: List[Callable] = []

    def add_stage(self, stage_func: Callable):
        """添加管道阶段"""
        self.pipeline_stages.append(stage_func)

    async def process(self, data: Any, source_node: str, target_nodes: List[str]) -> List[Any]:
        """处理数据管道"""
        current_data = data

        # 执行管道阶段
        for stage in self.pipeline_stages:
            if asyncio.iscoroutinefunction(stage):
                current_data = await stage(current_data)
            else:
                current_data = stage(current_data)

        # 发送到目标节点
        results = []
        for target in target_nodes:
            success = await self.transfer_manager.send_data(
                source_node, target, current_data
            )
            results.append(success)

        return results


class DataAggregator:
    """数据聚合器"""

    def __init__(self):
        self.aggregated_data: Dict[str, List[Any]] = defaultdict(list)
        self.aggregation_rules: Dict[str, Callable] = {}

    def add_aggregation_rule(self, data_type: str, rule: Callable):
        """添加聚合规则"""
        self.aggregation_rules[data_type] = rule

    def add_data(self, data_type: str, data: Any, source_node: str):
        """添加数据"""
        self.aggregated_data[data_type].append({
            'data': data,
            'source': source_node,
            'timestamp': datetime.now()
        })

    def aggregate(self, data_type: str) -> Any:
        """聚合数据"""
        if data_type not in self.aggregated_data:
            return None

        data_list = self.aggregated_data[data_type]

        if data_type in self.aggregation_rules:
            rule = self.aggregation_rules[data_type]
            return rule(data_list)

        # 默认聚合：简单合并
        return [item['data'] for item in data_list]

    def clear(self, data_type: str = None):
        """清理数据"""
        if data_type:
            self.aggregated_data.pop(data_type, None)
        else:
            self.aggregated_data.clear()


# ==================== 使用示例 ====================

async def example_data_transfer():
    """数据传递使用示例"""

    # 创建传递管理器
    config = DataTransferConfig(
        enable_compression=True,
        compression_threshold=512,
        enable_caching=True
    )
    transfer_manager = DataTransferManager(config)

    # 示例数据
    test_data = {
        "user_query": "用户问题",
        "context": {"session_id": "123"},
        "metadata": {"timestamp": datetime.now()}
    }

    # 发送数据
    success = await transfer_manager.send_data(
        source_node="agent_1",
        target_node="agent_2",
        data=test_data,
        data_type="user_input",
        format_type=DataFormat.JSON
    )

    print(f"数据发送结果: {success}")

    # 获取统计信息
    stats = transfer_manager.get_transfer_statistics()
    print(f"传输统计: {stats}")

if __name__ == "__main__":
    asyncio.run(example_data_transfer())