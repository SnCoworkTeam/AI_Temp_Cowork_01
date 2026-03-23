"""
智能体状态同步和协调机制
提供分布式智能体的状态同步、一致性保证和协调控制
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Set, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from shared_libs.luminaos_common.schemas.agent_communication import (
    StateSyncMessage, CoordinationRequest, CoordinationResponse,
    DependencyNotifyMessage, SynchronizationPoint, CoordinationState,
    AgentMessage, MessageHeader, MessageType, ExecutionMode
)

logger = logging.getLogger(__name__)


class StateType(str, Enum):
    """状态类型"""
    EXECUTION = "execution"
    DATA = "data"
    CONTEXT = "context"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"


class SyncStrategy(str, Enum):
    """同步策略"""
    IMMEDIATE = "immediate"      # 立即同步
    BATCH = "batch"             # 批量同步
    PERIODIC = "periodic"        # 周期性同步
    EVENT_DRIVEN = "event_driven" # 事件驱动同步
    LAZY = "lazy"               # 懒惰同步


class ConsistencyLevel(str, Enum):
    """一致性级别"""
    STRONG = "strong"           # 强一致性
    EVENTUAL = "eventual"       # 最终一致性
    WEAK = "weak"              # 弱一致性
    CAUSAL = "causal"          # 因果一致性


class ConflictResolutionStrategy(str, Enum):
    """冲突解决策略"""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MANUAL_RESOLUTION = "manual_resolution"
    MERGE = "merge"
    VERSIONED = "versioned"


@dataclass
class StateEntry:
    """状态条目"""
    state_id: str
    node_id: str
    state_type: StateType
    state_data: Dict[str, Any]
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.now)
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncConfiguration:
    """同步配置"""
    strategy: SyncStrategy = SyncStrategy.EVENT_DRIVEN
    consistency_level: ConsistencyLevel = ConsistencyLevel.EVENTUAL
    conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS
    sync_interval: int = 30  # 秒
    batch_size: int = 100
    max_retries: int = 3
    timeout: float = 10.0
    enable_compression: bool = True
    enable_encryption: bool = False


class StateManager:
    """状态管理器"""

    def __init__(self, node_id: str, config: SyncConfiguration = None):
        self.node_id = node_id
        self.config = config or SyncConfiguration()
        self.local_states: Dict[str, StateEntry] = {}
        self.remote_states: Dict[str, Dict[str, StateEntry]] = defaultdict(dict)
        self.state_subscriptions: Dict[str, List[Callable]] = defaultdict(list)
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.conflict_log: List[Dict[str, Any]] = []
        self._running = False
        self._sync_tasks: Set[asyncio.Task] = set()

    async def start(self):
        """启动状态管理器"""
        self._running = True
        logger.info(f"状态管理器启动: {self.node_id}")

        # 启动同步任务
        if self.config.strategy == SyncStrategy.PERIODIC:
            task = asyncio.create_task(self._periodic_sync_worker())
            self._sync_tasks.add(task)

        if self.config.strategy in [SyncStrategy.BATCH, SyncStrategy.EVENT_DRIVEN]:
            task = asyncio.create_task(self._queue_sync_worker())
            self._sync_tasks.add(task)

    async def stop(self):
        """停止状态管理器"""
        self._running = False

        # 取消所有同步任务
        for task in self._sync_tasks:
            task.cancel()

        await asyncio.gather(*self._sync_tasks, return_exceptions=True)
        logger.info(f"状态管理器停止: {self.node_id}")

    async def set_state(
        self,
        state_id: str,
        state_type: StateType,
        state_data: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """设置本地状态"""
        try:
            # 创建状态条目
            entry = StateEntry(
                state_id=state_id,
                node_id=self.node_id,
                state_type=state_type,
                state_data=state_data,
                metadata=metadata or {}
            )

            # 检查版本冲突
            if state_id in self.local_states:
                entry.version = self.local_states[state_id].version + 1

            # 计算校验和
            entry.checksum = self._calculate_checksum(state_data)

            # 保存本地状态
            self.local_states[state_id] = entry

            # 触发状态变更事件
            await self._notify_state_change(state_id, entry)

            # 根据同步策略处理同步
            if self.config.strategy == SyncStrategy.IMMEDIATE:
                await self._sync_state_immediately(entry)
            elif self.config.strategy in [SyncStrategy.BATCH, SyncStrategy.EVENT_DRIVEN]:
                await self.sync_queue.put(entry)

            logger.debug(f"状态已设置: {state_id} (版本: {entry.version})")
            return True

        except Exception as e:
            logger.error(f"设置状态失败 {state_id}: {e}")
            return False

    async def get_state(self, state_id: str, node_id: str = None) -> Optional[StateEntry]:
        """获取状态"""
        if node_id is None or node_id == self.node_id:
            # 获取本地状态
            return self.local_states.get(state_id)
        else:
            # 获取远程状态
            return self.remote_states.get(node_id, {}).get(state_id)

    async def get_all_states(self, state_type: StateType = None) -> List[StateEntry]:
        """获取所有状态"""
        states = []

        # 本地状态
        for entry in self.local_states.values():
            if state_type is None or entry.state_type == state_type:
                states.append(entry)

        # 远程状态
        for remote_node_states in self.remote_states.values():
            for entry in remote_node_states.values():
                if state_type is None or entry.state_type == state_type:
                    states.append(entry)

        return states

    async def sync_state_with_nodes(self, target_nodes: List[str], state_ids: List[str] = None):
        """与指定节点同步状态"""
        states_to_sync = []

        if state_ids:
            # 同步指定状态
            for state_id in state_ids:
                if state_id in self.local_states:
                    states_to_sync.append(self.local_states[state_id])
        else:
            # 同步所有状态
            states_to_sync = list(self.local_states.values())

        for target_node in target_nodes:
            for state_entry in states_to_sync:
                await self._send_sync_message(target_node, state_entry)

    async def handle_sync_message(self, sync_message: StateSyncMessage):
        """处理同步消息"""
        try:
            state_data = sync_message.current_state
            remote_entry = StateEntry(
                state_id=sync_message.node_id,  # 使用节点ID作为状态ID
                node_id=sync_message.node_id,
                state_type=StateType(sync_message.state_type),
                state_data=state_data,
                version=sync_message.state_version,
                timestamp=sync_message.sync_timestamp
            )

            # 检查冲突
            conflict_resolved = await self._resolve_state_conflict(remote_entry)

            if conflict_resolved:
                # 更新远程状态
                self.remote_states[remote_entry.node_id][remote_entry.state_id] = remote_entry
                logger.debug(f"远程状态已更新: {remote_entry.state_id} from {remote_entry.node_id}")

                # 触发订阅者
                await self._notify_remote_state_change(remote_entry)

        except Exception as e:
            logger.error(f"处理同步消息失败: {e}")

    async def subscribe_state_changes(self, state_id: str, callback: Callable):
        """订阅状态变更"""
        self.state_subscriptions[state_id].append(callback)
        logger.debug(f"添加状态订阅: {state_id}")

    async def unsubscribe_state_changes(self, state_id: str, callback: Callable):
        """取消订阅状态变更"""
        if state_id in self.state_subscriptions:
            if callback in self.state_subscriptions[state_id]:
                self.state_subscriptions[state_id].remove(callback)
                logger.debug(f"移除状态订阅: {state_id}")

    async def _notify_state_change(self, state_id: str, entry: StateEntry):
        """通知状态变更"""
        if state_id in self.state_subscriptions:
            for callback in self.state_subscriptions[state_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(entry)
                    else:
                        callback(entry)
                except Exception as e:
                    logger.error(f"状态变更通知失败 {state_id}: {e}")

    async def _notify_remote_state_change(self, entry: StateEntry):
        """通知远程状态变更"""
        # 通知全局状态订阅者
        if "*" in self.state_subscriptions:
            for callback in self.state_subscriptions["*"]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(entry)
                    else:
                        callback(entry)
                except Exception as e:
                    logger.error(f"远程状态变更通知失败: {e}")

    async def _resolve_state_conflict(self, remote_entry: StateEntry) -> bool:
        """解决状态冲突"""
        state_id = remote_entry.state_id
        local_entry = self.local_states.get(state_id)

        if not local_entry:
            # 没有本地状态，直接接受
            return True

        # 检查版本冲突
        if remote_entry.version <= local_entry.version:
            # 远程版本较旧，忽略
            return False

        # 根据冲突解决策略处理
        if self.config.conflict_resolution == ConflictResolutionStrategy.LAST_WRITE_WINS:
            return remote_entry.timestamp >= local_entry.timestamp

        elif self.config.conflict_resolution == ConflictResolutionStrategy.FIRST_WRITE_WINS:
            return remote_entry.timestamp < local_entry.timestamp

        elif self.config.conflict_resolution == ConflictResolutionStrategy.VERSIONED:
            # 创建新版本
            remote_entry.version = max(local_entry.version, remote_entry.version) + 1
            return True

        elif self.config.conflict_resolution == ConflictResolutionStrategy.MERGE:
            # 尝试合并状态
            merged_data = await self._merge_state_data(local_entry.state_data, remote_entry.state_data)
            remote_entry.state_data = merged_data
            remote_entry.version = max(local_entry.version, remote_entry.version) + 1
            return True

        elif self.config.conflict_resolution == ConflictResolutionStrategy.MANUAL_RESOLUTION:
            # 记录冲突，等待手动解决
            self._log_conflict(local_entry, remote_entry)
            return False

        return True

    async def _merge_state_data(self, local_data: Dict[str, Any], remote_data: Dict[str, Any]) -> Dict[str, Any]:
        """合并状态数据"""
        merged = local_data.copy()

        for key, value in remote_data.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                # 递归合并字典
                merged[key] = await self._merge_state_data(merged[key], value)
            elif isinstance(merged[key], list) and isinstance(value, list):
                # 合并列表（去重）
                merged[key] = list(set(merged[key] + value))
            else:
                # 选择较新的值
                merged[key] = value

        return merged

    def _log_conflict(self, local_entry: StateEntry, remote_entry: StateEntry):
        """记录冲突"""
        conflict = {
            'state_id': local_entry.state_id,
            'local_version': local_entry.version,
            'remote_version': remote_entry.version,
            'local_timestamp': local_entry.timestamp,
            'remote_timestamp': remote_entry.timestamp,
            'local_node': local_entry.node_id,
            'remote_node': remote_entry.node_id,
            'conflict_time': datetime.now()
        }
        self.conflict_log.append(conflict)
        logger.warning(f"状态冲突记录: {conflict}")

    async def _send_sync_message(self, target_node: str, entry: StateEntry):
        """发送同步消息"""
        sync_message = StateSyncMessage(
            node_id=entry.node_id,
            state_type=entry.state_type.value,
            current_state=entry.state_data,
            state_version=entry.version,
            sync_timestamp=entry.timestamp
        )

        # 这里应该通过消息路由器发送
        # message_router.send_message(target_node, sync_message)
        logger.debug(f"发送同步消息到 {target_node}: {entry.state_id}")

    async def _sync_state_immediately(self, entry: StateEntry):
        """立即同步状态"""
        # 这里应该实现立即同步逻辑
        logger.debug(f"立即同步状态: {entry.state_id}")

    async def _periodic_sync_worker(self):
        """周期性同步工作器"""
        while self._running:
            try:
                await asyncio.sleep(self.config.sync_interval)

                if self.local_states:
                    logger.debug("执行周期性状态同步")
                    # 同步所有本地状态
                    for entry in self.local_states.values():
                        await self.sync_queue.put(entry)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"周期性同步失败: {e}")

    async def _queue_sync_worker(self):
        """队列同步工作器"""
        batch = []

        while self._running:
            try:
                # 等待队列中的状态
                entry = await asyncio.wait_for(self.sync_queue.get(), timeout=1.0)
                batch.append(entry)

                # 批量处理
                if len(batch) >= self.config.batch_size:
                    await self._process_sync_batch(batch)
                    batch.clear()

            except asyncio.TimeoutError:
                # 超时，处理当前批次
                if batch:
                    await self._process_sync_batch(batch)
                    batch.clear()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"队列同步失败: {e}")

    async def _process_sync_batch(self, batch: List[StateEntry]):
        """处理同步批次"""
        logger.debug(f"处理同步批次: {len(batch)} 个状态")

        for entry in batch:
            try:
                await self._sync_state_immediately(entry)
            except Exception as e:
                logger.error(f"同步状态失败 {entry.state_id}: {e}")

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """计算状态数据校验和"""
        import hashlib
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def get_sync_statistics(self) -> Dict[str, Any]:
        """获取同步统计"""
        return {
            'local_states_count': len(self.local_states),
            'remote_nodes_count': len(self.remote_states),
            'total_remote_states': sum(len(states) for states in self.remote_states.values()),
            'conflicts_count': len(self.conflict_log),
            'sync_queue_size': self.sync_queue.qsize(),
            'subscriptions_count': len(self.state_subscriptions)
        }


class DistributedCoordinator:
    """分布式协调器"""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.active_coordinations: Dict[str, CoordinationState] = {}
        self.sync_points: Dict[str, SynchronizationPoint] = {}
        self.coordination_locks: Dict[str, asyncio.Lock] = {}
        self.pending_requests: Dict[str, CoordinationRequest] = {}
        self.response_handlers: Dict[str, Callable] = {}

    async def initiate_coordination(
        self,
        coordination_id: str,
        participating_nodes: List[str],
        coordination_type: str,
        coordination_data: Dict[str, Any] = None
    ) -> bool:
        """发起协调"""
        try:
            # 创建协调锁
            if coordination_id not in self.coordination_locks:
                self.coordination_locks[coordination_id] = asyncio.Lock()

            async with self.coordination_locks[coordination_id]:
                # 发送协调请求
                request = CoordinationRequest(
                    request_type=coordination_type,
                    requesting_node=self.node_id,
                    target_nodes=participating_nodes,
                    coordination_data=coordination_data or {}
                )

                self.pending_requests[coordination_id] = request

                # 向所有参与节点发送请求
                for node in participating_nodes:
                    await self._send_coordination_request(node, request)

                logger.info(f"发起协调: {coordination_id} ({coordination_type})")
                return True

        except Exception as e:
            logger.error(f"发起协调失败 {coordination_id}: {e}")
            return False

    async def handle_coordination_request(self, request: CoordinationRequest) -> CoordinationResponse:
        """处理协调请求"""
        try:
            # 根据请求类型处理
            if request.request_type == "dependency_check":
                return await self._handle_dependency_check(request)
            elif request.request_type == "resource_allocation":
                return await self._handle_resource_allocation(request)
            elif request.request_type == "execution_order":
                return await self._handle_execution_order(request)
            else:
                return CoordinationResponse(
                    request_id=request.requesting_node,
                    responding_node=self.node_id,
                    response_type="reject",
                    reason=f"Unknown request type: {request.request_type}"
                )

        except Exception as e:
            logger.error(f"处理协调请求失败: {e}")
            return CoordinationResponse(
                request_id=request.requesting_node,
                responding_node=self.node_id,
                response_type="reject",
                reason=str(e)
            )

    async def _handle_dependency_check(self, request: CoordinationRequest) -> CoordinationResponse:
        """处理依赖检查"""
        # 实现依赖检查逻辑
        dependencies_satisfied = True  # 简化实现

        return CoordinationResponse(
            request_id=request.requesting_node,
            responding_node=self.node_id,
            response_type="accept" if dependencies_satisfied else "reject",
            response_data={"dependencies_satisfied": dependencies_satisfied}
        )

    async def _handle_resource_allocation(self, request: CoordinationRequest) -> CoordinationResponse:
        """处理资源分配"""
        # 实现资源分配逻辑
        resources_available = True  # 简化实现

        return CoordinationResponse(
            request_id=request.requesting_node,
            responding_node=self.node_id,
            response_type="accept" if resources_available else "defer",
            response_data={"resources_available": resources_available}
        )

    async def _handle_execution_order(self, request: CoordinationRequest) -> CoordinationResponse:
        """处理执行顺序"""
        # 实现执行顺序协调逻辑
        order_accepted = True  # 简化实现

        return CoordinationResponse(
            request_id=request.requesting_node,
            responding_node=self.node_id,
            response_type="accept" if order_accepted else "reject",
            response_data={"execution_order_accepted": order_accepted}
        )

    async def create_barrier(
        self,
        barrier_id: str,
        required_nodes: List[str],
        timeout: int = 60
    ) -> SynchronizationPoint:
        """创建同步屏障"""
        sync_point = SynchronizationPoint(
            sync_id=barrier_id,
            sync_type="barrier",
            required_nodes=required_nodes,
            timeout=timeout
        )

        self.sync_points[barrier_id] = sync_point
        logger.info(f"创建同步屏障: {barrier_id}")
        return sync_point

    async def wait_at_barrier(self, barrier_id: str) -> bool:
        """在屏障等待"""
        if barrier_id not in self.sync_points:
            return False

        sync_point = self.sync_points[barrier_id]

        # 添加到等待节点
        if self.node_id not in sync_point.waiting_nodes:
            sync_point.waiting_nodes.append(self.node_id)

        # 检查是否所有节点都到达
        if set(sync_point.required_nodes).issubset(set(sync_point.waiting_nodes)):
            logger.info(f"屏障条件满足: {barrier_id}")
            return True

        # 等待其他节点
        start_time = datetime.now()
        while datetime.now() - start_time < timedelta(seconds=sync_point.timeout):
            await asyncio.sleep(0.1)

            if set(sync_point.required_nodes).issubset(set(sync_point.waiting_nodes)):
                return True

        logger.warning(f"屏障超时: {barrier_id}")
        return False

    async def notify_barrier_arrival(self, barrier_id: str, node_id: str):
        """通知屏障到达"""
        if barrier_id in self.sync_points:
            sync_point = self.sync_points[barrier_id]
            if node_id not in sync_point.waiting_nodes:
                sync_point.waiting_nodes.append(node_id)
                logger.debug(f"节点到达屏障: {node_id} -> {barrier_id}")

    async def _send_coordination_request(self, target_node: str, request: CoordinationRequest):
        """发送协调请求"""
        # 这里应该通过消息路由器发送
        logger.debug(f"发送协调请求到 {target_node}: {request.request_type}")

    def get_coordination_status(self) -> Dict[str, Any]:
        """获取协调状态"""
        return {
            'active_coordinations': len(self.active_coordinations),
            'sync_points': len(self.sync_points),
            'pending_requests': len(self.pending_requests),
            'coordination_locks': len(self.coordination_locks)
        }


# ==================== 使用示例 ====================

async def example_state_sync():
    """状态同步使用示例"""

    # 创建状态管理器
    config = SyncConfiguration(
        strategy=SyncStrategy.EVENT_DRIVEN,
        consistency_level=ConsistencyLevel.EVENTUAL
    )

    state_manager = StateManager("node_1", config)
    await state_manager.start()

    # 设置状态
    await state_manager.set_state(
        "user_session",
        StateType.CONTEXT,
        {"user_id": "123", "session_data": {"last_action": "query"}}
    )

    # 订阅状态变更
    async def on_state_change(entry: StateEntry):
        print(f"状态变更: {entry.state_id} -> {entry.state_data}")

    await state_manager.subscribe_state_changes("user_session", on_state_change)

    # 获取统计信息
    stats = state_manager.get_sync_statistics()
    print(f"同步统计: {stats}")

    await state_manager.stop()

if __name__ == "__main__":
    asyncio.run(example_state_sync())