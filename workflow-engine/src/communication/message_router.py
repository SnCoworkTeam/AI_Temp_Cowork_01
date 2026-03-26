"""
智能体通信消息路由器实现
提供消息路由、队列管理、协调控制的核心功能
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
import logging
import weakref

from shared_libs.luminaos_common.schemas.agent_communication import (
    AgentMessage, MessageHeader, MessagePayload,
    MessageType, MessagePriority, MessageDeliveryMode,
    RoutingRule, MessageQueue, CommunicationMetrics,
    CommunicationProtocolConfig, CoordinationState,
    SynchronizationPoint, ExecutionMode
)

logger = logging.getLogger(__name__)


class MessageRoutingEngine:
    """消息路由引擎"""

    def __init__(self, config: CommunicationProtocolConfig):
        self.config = config
        self.routing_rules: List[RoutingRule] = []
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.metrics = CommunicationMetrics(
            time_window={"start": datetime.now(), "end": datetime.now()}
        )
        self.active_connections: Dict[str, Any] = {}
        self.dead_letter_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def start(self):
        """启动路由引擎"""
        self._running = True
        logger.info("消息路由引擎启动")

        # 启动后台任务
        asyncio.create_task(self._metrics_collector())
        asyncio.create_task(self._queue_monitor())
        asyncio.create_task(self._dead_letter_processor())

    async def stop(self):
        """停止路由引擎"""
        self._running = False
        logger.info("消息路由引擎停止")

    def add_routing_rule(self, rule: RoutingRule):
        """添加路由规则"""
        # 按优先级插入
        inserted = False
        for i, existing_rule in enumerate(self.routing_rules):
            if rule.priority < existing_rule.priority:
                self.routing_rules.insert(i, rule)
                inserted = True
                break

        if not inserted:
            self.routing_rules.append(rule)

        logger.info(f"添加路由规则: {rule.name} (优先级: {rule.priority})")

    def create_queue(self, queue_config: MessageQueue):
        """创建消息队列"""
        queue = asyncio.Queue(maxsize=queue_config.max_size)
        self.message_queues[queue_config.queue_id] = queue
        logger.info(f"创建消息队列: {queue_config.queue_name}")

    async def route_message(self, message: AgentMessage) -> bool:
        """路由消息"""
        try:
            # 更新指标
            self.metrics.message_count += 1
            message_size = len(json.dumps(message.dict()).encode())
            self.metrics.message_size_total += message_size

            # 应用路由规则
            matched_rules = self._match_routing_rules(message)

            if not matched_rules:
                logger.warning(f"消息无匹配规则: {message.header.message_id}")
                await self.dead_letter_queue.put(message)
                return False

            # 执行路由
            for rule in matched_rules:
                await self._execute_routing_rule(message, rule)

            self.metrics.delivery_success_rate = self._calculate_success_rate()
            return True

        except Exception as e:
            logger.error(f"消息路由失败: {e}")
            self.metrics.error_count += 1
            await self.dead_letter_queue.put(message)
            return False

    def _match_routing_rules(self, message: AgentMessage) -> List[RoutingRule]:
        """匹配路由规则"""
        matched = []

        for rule in self.routing_rules:
            if not rule.enabled:
                continue

            # 检查消息类型匹配
            if rule.message_type and rule.message_type != message.header.message_type:
                continue

            # 检查源模式匹配
            if rule.source_pattern and not re.match(rule.source_pattern, message.header.source):
                continue

            # 检查目标模式匹配
            if (rule.destination_pattern and message.header.destination and
                not re.match(rule.destination_pattern, message.header.destination)):
                continue

            # 检查工作流ID匹配
            if rule.workflow_id and rule.workflow_id != message.header.workflow_id:
                continue

            matched.append(rule)

        return matched

    async def _execute_routing_rule(self, message: AgentMessage, rule: RoutingRule):
        """执行路由规则"""
        try:
            # 应用转换规则
            transformed_message = await self._apply_transform_rules(message, rule.transform_rules)

            # 根据传递模式执行路由
            if rule.delivery_mode == MessageDeliveryMode.DIRECT:
                await self._route_direct(transformed_message, rule.target_nodes)
            elif rule.delivery_mode == MessageDeliveryMode.BROADCAST:
                await self._route_broadcast(transformed_message, rule.target_nodes)
            elif rule.delivery_mode == MessageDeliveryMode.MULTICAST:
                await self._route_multicast(transformed_message, rule.target_nodes)
            elif rule.delivery_mode == MessageDeliveryMode.ASYNC:
                await self._route_async(transformed_message, rule.target_nodes)

        except Exception as e:
            logger.error(f"执行路由规则失败 {rule.rule_id}: {e}")
            raise

    async def _route_direct(self, message: AgentMessage, target_nodes: List[str]):
        """直接路由"""
        for target in target_nodes:
            await self._deliver_to_target(message, target)

    async def _route_broadcast(self, message: AgentMessage, target_nodes: List[str]):
        """广播路由"""
        tasks = [self._deliver_to_target(message, target) for target in target_nodes]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _route_multicast(self, message: AgentMessage, target_nodes: List[str]):
        """组播路由"""
        # 基于目标节点的订阅主题进行路由
        for target in target_nodes:
            if target in self.subscribers:
                for callback in self.subscribers[target]:
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"组播回调失败 {target}: {e}")

    async def _route_async(self, message: AgentMessage, target_nodes: List[str]):
        """异步路由"""
        # 将消息放入异步队列
        for target in target_nodes:
            if target in self.message_queues:
                try:
                    await self.message_queues[target].put(message)
                except asyncio.QueueFull:
                    logger.warning(f"队列已满: {target}")
                    await self.dead_letter_queue.put(message)

    async def _deliver_to_target(self, message: AgentMessage, target: str):
        """传递消息到目标"""
        start_time = datetime.now()

        try:
            # 检查目标连接
            if target in self.active_connections:
                connection = self.active_connections[target]
                await connection.send_message(message)
            elif target in self.subscribers:
                # 本地订阅者
                for callback in self.subscribers[target]:
                    await callback(message)
            else:
                # 尝试创建连接或加入队列
                if target not in self.message_queues:
                    self.message_queues[target] = asyncio.Queue()
                await self.message_queues[target].put(message)

            # 记录延迟
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self._update_latency_metrics(latency)

        except Exception as e:
            logger.error(f"消息传递失败 to {target}: {e}")
            raise

    async def _apply_transform_rules(self, message: AgentMessage, transform_rules: List[Dict[str, Any]]) -> AgentMessage:
        """应用转换规则"""
        if not transform_rules:
            return message

        transformed = message.copy(deep=True)

        for rule in transform_rules:
            rule_type = rule.get("type")

            if rule_type == "header_modify":
                # 修改消息头
                header_changes = rule.get("changes", {})
                for key, value in header_changes.items():
                    if hasattr(transformed.header, key):
                        setattr(transformed.header, key, value)

            elif rule_type == "payload_transform":
                # 转换载荷数据
                transform_func = rule.get("function")
                if transform_func:
                    transformed.payload = await self._apply_payload_transform(transformed.payload, transform_func)

            elif rule_type == "filter":
                # 数据过滤
                filter_rules = rule.get("rules", [])
                transformed.payload.data = self._apply_data_filter(transformed.payload.data, filter_rules)

        return transformed

    async def _apply_payload_transform(self, payload: MessagePayload, transform_func: str) -> MessagePayload:
        """应用载荷转换函数"""
        # 这里可以实现自定义的转换逻辑
        # 例如数据格式转换、字段映射等
        return payload

    def _apply_data_filter(self, data: Dict[str, Any], filter_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """应用数据过滤规则"""
        filtered_data = data.copy()

        for rule in filter_rules:
            action = rule.get("action")
            field = rule.get("field")

            if action == "remove" and field in filtered_data:
                del filtered_data[field]
            elif action == "mask" and field in filtered_data:
                filtered_data[field] = "***masked***"

        return filtered_data

    def subscribe(self, target: str, callback: Callable):
        """订阅消息"""
        self.subscribers[target].append(callback)
        logger.info(f"添加订阅者: {target}")

    def unsubscribe(self, target: str, callback: Callable):
        """取消订阅"""
        if target in self.subscribers and callback in self.subscribers[target]:
            self.subscribers[target].remove(callback)
            logger.info(f"移除订阅者: {target}")

    async def get_queue_message(self, queue_id: str) -> Optional[AgentMessage]:
        """从队列获取消息"""
        if queue_id in self.message_queues:
            try:
                return await asyncio.wait_for(
                    self.message_queues[queue_id].get(),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                return None
        return None

    async def _metrics_collector(self):
        """指标收集器"""
        while self._running:
            await asyncio.sleep(60)  # 每分钟收集一次

            # 计算吞吐量
            time_diff = (datetime.now() - self.metrics.time_window["start"]).total_seconds()
            if time_diff > 0:
                self.metrics.throughput_per_second = self.metrics.message_count / time_diff

            # 记录队列深度
            max_depth = 0
            for queue in self.message_queues.values():
                max_depth = max(max_depth, queue.qsize())
            self.metrics.queue_depth_max = max_depth

    async def _queue_monitor(self):
        """队列监控器"""
        while self._running:
            await asyncio.sleep(30)  # 每30秒检查一次

            for queue_id, queue in self.message_queues.items():
                if queue.qsize() > queue.maxsize * 0.8:
                    logger.warning(f"队列接近满载: {queue_id} ({queue.qsize()}/{queue.maxsize})")

    async def _dead_letter_processor(self):
        """死信队列处理器"""
        while self._running:
            try:
                # 从死信队列获取消息
                message = await asyncio.wait_for(self.dead_letter_queue.get(), timeout=5.0)

                # 记录死信
                logger.error(f"死信消息: {message.header.message_id}")

                # 可以实现重试逻辑或持久化存储

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"处理死信消息失败: {e}")

    def _calculate_success_rate(self) -> float:
        """计算传递成功率"""
        total = self.metrics.message_count
        errors = self.metrics.error_count
        if total > 0:
            return (total - errors) / total
        return 0.0

    def _update_latency_metrics(self, latency: float):
        """更新延迟指标"""
        # 简化的延迟统计，实际应该使用更复杂的统计算法
        current_avg = self.metrics.delivery_latency_avg
        count = self.metrics.message_count

        self.metrics.delivery_latency_avg = (current_avg * (count - 1) + latency) / count

    def get_metrics(self) -> CommunicationMetrics:
        """获取通信指标"""
        return self.metrics

    def get_queue_status(self) -> Dict[str, Dict[str, Any]]:
        """获取队列状态"""
        status = {}
        for queue_id, queue in self.message_queues.items():
            status[queue_id] = {
                "size": queue.qsize(),
                "max_size": queue.maxsize,
                "utilization": queue.qsize() / queue.maxsize if queue.maxsize > 0 else 0
            }
        return status


class WorkflowCoordinator:
    """工作流协调器"""

    def __init__(self, routing_engine: MessageRoutingEngine):
        self.routing_engine = routing_engine
        self.coordination_states: Dict[str, CoordinationState] = {}
        self.sync_points: Dict[str, SynchronizationPoint] = {}
        self.execution_plans: Dict[str, Any] = {}
        self._coordinator_running = False

    async def start_coordination(self, workflow_id: str, execution_id: str, execution_plan: Dict[str, Any]):
        """开始协调执行"""
        # 初始化协调状态
        coord_state = CoordinationState(
            execution_id=execution_id,
            workflow_id=workflow_id,
            current_stage="initializing",
            pending_nodes=execution_plan.get("node_order", [])
        )

        self.coordination_states[execution_id] = coord_state
        self.execution_plans[execution_id] = execution_plan

        logger.info(f"开始工作流协调: {workflow_id} (执行ID: {execution_id})")

        # 根据执行模式启动协调
        execution_mode = execution_plan.get("execution_mode", ExecutionMode.SEQUENTIAL)

        if execution_mode == ExecutionMode.SEQUENTIAL:
            await self._coordinate_sequential_execution(execution_id)
        elif execution_mode == ExecutionMode.PARALLEL:
            await self._coordinate_parallel_execution(execution_id)
        elif execution_mode == ExecutionMode.PIPELINE:
            await self._coordinate_pipeline_execution(execution_id)

    async def _coordinate_sequential_execution(self, execution_id: str):
        """协调串行执行"""
        state = self.coordination_states[execution_id]
        plan = self.execution_plans[execution_id]

        for node_id in plan.get("node_order", []):
            # 检查依赖
            if await self._check_dependencies(execution_id, node_id):
                await self._start_node_execution(execution_id, node_id)
                await self._wait_for_node_completion(execution_id, node_id)
            else:
                logger.error(f"节点依赖未满足: {node_id}")
                break

    async def _coordinate_parallel_execution(self, execution_id: str):
        """协调并行执行"""
        state = self.coordination_states[execution_id]
        plan = self.execution_plans[execution_id]

        # 启动所有可以并行的节点
        parallel_tasks = []
        for node_id in plan.get("node_order", []):
            if await self._check_dependencies(execution_id, node_id):
                task = asyncio.create_task(self._execute_node(execution_id, node_id))
                parallel_tasks.append(task)

        # 等待所有节点完成
        if parallel_tasks:
            await asyncio.gather(*parallel_tasks, return_exceptions=True)

    async def _coordinate_pipeline_execution(self, execution_id: str):
        """协调流水线执行"""
        state = self.coordination_states[execution_id]
        plan = self.execution_plans[execution_id]

        # 流水线执行：数据在节点间流动
        for stage in plan.get("pipeline_stages", []):
            stage_tasks = []
            for node_id in stage:
                if await self._check_dependencies(execution_id, node_id):
                    task = asyncio.create_task(self._execute_node(execution_id, node_id))
                    stage_tasks.append(task)

            # 等待当前阶段完成
            if stage_tasks:
                await asyncio.gather(*stage_tasks)

    async def _check_dependencies(self, execution_id: str, node_id: str) -> bool:
        """检查节点依赖"""
        plan = self.execution_plans[execution_id]
        dependencies = plan.get("dependencies", {}).get(node_id, [])

        if not dependencies:
            return True

        state = self.coordination_states[execution_id]

        for dep_node in dependencies:
            if dep_node not in state.completed_nodes:
                return False

        return True

    async def _start_node_execution(self, execution_id: str, node_id: str):
        """启动节点执行"""
        # 发送执行开始消息
        from shared_libs.luminaos_common.schemas.agent_communication import ExecutionStartMessage

        message = AgentMessage(
            header=MessageHeader(
                message_type=MessageType.EXECUTION_START,
                source="workflow_coordinator",
                destination=node_id,
                execution_id=execution_id
            ),
            payload=ExecutionStartMessage(
                agent_id=node_id,  # 简化处理
                node_id=node_id,
                input_data={},
                execution_config={}
            )
        )

        await self.routing_engine.route_message(message)

        # 更新状态
        state = self.coordination_states[execution_id]
        state.running_nodes.append(node_id)
        if node_id in state.pending_nodes:
            state.pending_nodes.remove(node_id)

    async def _wait_for_node_completion(self, execution_id: str, node_id: str):
        """等待节点完成"""
        # 这里应该订阅完成消息
        # 简化实现：模拟等待
        await asyncio.sleep(1)

    async def _execute_node(self, execution_id: str, node_id: str):
        """执行节点"""
        await self._start_node_execution(execution_id, node_id)
        await self._wait_for_node_completion(execution_id, node_id)

    async def handle_node_completion(self, execution_id: str, node_id: str, success: bool):
        """处理节点完成"""
        if execution_id not in self.coordination_states:
            return

        state = self.coordination_states[execution_id]

        if node_id in state.running_nodes:
            state.running_nodes.remove(node_id)

        if success:
            state.completed_nodes.append(node_id)
        else:
            state.failed_nodes.append(node_id)

        # 检查是否可以启动下一个节点
        await self._check_next_nodes(execution_id)

    async def _check_next_nodes(self, execution_id: str):
        """检查下一个可执行的节点"""
        state = self.coordination_states[execution_id]
        plan = self.execution_plans[execution_id]

        for node_id in state.pending_nodes[:]:  # 创建副本以避免修改时出错
            if await self._check_dependencies(execution_id, node_id):
                await self._start_node_execution(execution_id, node_id)

    def create_sync_point(self, sync_point: SynchronizationPoint):
        """创建同步点"""
        self.sync_points[sync_point.sync_id] = sync_point
        logger.info(f"创建同步点: {sync_point.sync_id} ({sync_point.sync_type})")

    async def wait_at_sync_point(self, sync_id: str, node_id: str) -> bool:
        """在同步点等待"""
        if sync_id not in self.sync_points:
            return False

        sync_point = self.sync_points[sync_id]

        if node_id not in sync_point.waiting_nodes:
            sync_point.waiting_nodes.append(node_id)

        # 检查是否所有必需节点都到达
        if set(sync_point.required_nodes).issubset(set(sync_point.waiting_nodes)):
            # 释放所有等待的节点
            logger.info(f"同步点满足条件: {sync_id}")
            return True

        return False

    def get_coordination_state(self, execution_id: str) -> Optional[CoordinationState]:
        """获取协调状态"""
        return self.coordination_states.get(execution_id)


# ==================== 使用示例 ====================

async def example_usage():
    """使用示例"""

    # 创建配置
    config = CommunicationProtocolConfig(
        protocol_version="1.0",
        default_timeout=30,
        max_retry_count=3
    )

    # 创建路由引擎
    routing_engine = MessageRoutingEngine(config)
    await routing_engine.start()

    # 添加路由规则
    rule = RoutingRule(
        name="agent_execution_rule",
        priority=1,
        message_type=MessageType.EXECUTION_START,
        target_nodes=["agent_node_1", "agent_node_2"],
        delivery_mode=MessageDeliveryMode.DIRECT
    )
    routing_engine.add_routing_rule(rule)

    # 创建协调器
    coordinator = WorkflowCoordinator(routing_engine)

    # 示例消息路由
    message = AgentMessage(
        header=MessageHeader(
            message_type=MessageType.EXECUTION_START,
            source="workflow_engine",
            destination="agent_node_1"
        ),
        payload=MessagePayload(data={"test": "data"})
    )

    success = await routing_engine.route_message(message)
    print(f"消息路由结果: {success}")

    # 获取指标
    metrics = routing_engine.get_metrics()
    print(f"通信指标: {metrics.dict()}")

if __name__ == "__main__":
    asyncio.run(example_usage())