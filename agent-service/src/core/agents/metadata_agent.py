"""
元数据智能体（优化版）
提供业务上下文和语义理解，带缓存、批量查询和性能优化
增强版：集成EA感知和语义引擎
"""
import logging
import os
import sys
import httpx
import time
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)

# EA服务集成
EA_SERVICES_AVAILABLE = False
EAKnowledgeGraph = None
EAHybridQuery = None

try:
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from metadata_service.src.services.ea_knowledge_graph import EAKnowledgeGraph
    from metadata_service.src.services.ea_hybrid_query import EAHybridQuery
    EA_SERVICES_AVAILABLE = True
    logger.info("EA服务模块加载成功")
except ImportError as e:
    EA_SERVICES_AVAILABLE = False
    logger.warning(f"EA服务模块未找到，EA增强功能将不可用: {e}")

# 语义引擎集成
SEMANTIC_ENGINE_AVAILABLE = False
EnterpriseSemanticEngine = None

try:
    from services.enterprise_semantic_engine import EnterpriseSemanticEngine
    SEMANTIC_ENGINE_AVAILABLE = True
    logger.info("语义引擎模块加载成功")
except ImportError as e:
    SEMANTIC_ENGINE_AVAILABLE = False
    logger.warning(f"语义引擎模块未找到，语义增强功能将不可用: {e}")


class MetadataAgent(IntelligentAgent):
    """元数据智能体（优化版）- 提供业务上下文和语义理解，带缓存和性能优化，集成EA感知和语义引擎"""
    
    def __init__(self, metadata_service=None):
        """
        初始化元数据智能体
        
        Args:
            metadata_service: Metadata Service客户端（可选，默认使用metadata_client）
        """
        super().__init__(
            agent_id="metadata_agent",
            name="元数据智能体",
            description="提供业务上下文和语义理解，包括业务语义、实体映射、上下文增强、约束分析、EA感知、语义搜索",
            capabilities={
                "business_semantics": "业务语义理解",
                "entity_mapping": "实体映射",
                "context_enrichment": "上下文增强",
                "constraint_analysis": "约束分析",
                "ea_awareness": "企业架构感知",
                "semantic_search": "语义搜索"
            }
        )
        # 延迟导入避免循环依赖
        if metadata_service is None:
            from ...services.metadata_client import metadata_client
            self.metadata_service = metadata_client
        else:
            self.metadata_service = metadata_service
        self.llm = deepseek_llm
        
        # EA服务初始化（延迟初始化，避免阻塞）
        self.ea_graph_service = None
        self.ea_hybrid_query = None
        self._ea_db = None  # 保存数据库会话，用于后续查询
        self._ea_service_initialized = False
        
        # 语义引擎初始化
        self.semantic_engine = None
        if SEMANTIC_ENGINE_AVAILABLE and EnterpriseSemanticEngine:
            try:
                self.semantic_engine = EnterpriseSemanticEngine()
                logger.info("语义引擎初始化成功")
            except Exception as e:
                logger.warning(f"语义引擎初始化失败: {e}，将使用原有功能")
                self.semantic_engine = None
        
        # 动态API配置（去除硬编码）
        self._api_config = {
            "base_url": os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005"),
            "endpoints": {
                "business_entities": "/api/business-entities",
                "data_assets": "/api/data-assets",
                "business_rules": "/api/business-rules",
                "search": "/api/search"
            },
            "timeouts": {
                "default": 5.0,
                "batch": 10.0,
                "complex": 15.0
            },
            "retry": {
                "max_retries": 3,
                "retry_delay": 1.0
            }
        }
        self._api_config_loaded = False
        
        # 缓存机制
        self._entity_cache: Dict[str, Dict[str, Any]] = {}
        self._entity_cache_ttl: float = 3600.0  # 1小时缓存
        
        self._data_source_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._data_source_cache_ttl: float = 1800.0  # 30分钟缓存
        
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
        self._analysis_cache_ttl: float = 600.0  # 10分钟缓存
        
        # 共享HTTP客户端（连接池）
        self._http_client: Optional[httpx.AsyncClient] = None
    
    def _is_cache_valid(self, cache_time: Optional[float], ttl: float) -> bool:
        """检查缓存是否有效"""
        if cache_time is None:
            return False
        return (time.time() - cache_time) < ttl
    
    def _generate_cache_key(self, task: str, context: Dict[str, Any]) -> str:
        """生成缓存键"""
        key_data = {
            "task": task,
            "context_keys": sorted(context.keys())
        }
        for key in ["user_input", "query", "request"]:
            if key in context:
                key_data[key] = str(context[key])[:100]
        
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端（单例，带连接池）"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self._api_config["timeouts"]["default"],
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                verify=True,
                follow_redirects=True
            )
        return self._http_client
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    async def _load_api_config(self):
        """动态加载API配置（如果metadata-service支持）- 优化版：快速失败，不阻塞"""
        if self._api_config_loaded:
            return
        
        # 使用更短的超时时间（0.5秒），快速失败，不阻塞
        try:
            client = await self._get_http_client()
            response = await asyncio.wait_for(
                client.get(f"{self._api_config['base_url']}/api/config", timeout=0.5),
                timeout=0.5
            )
            if response.status_code == 200:
                config = response.json()
                if config:
                    self._api_config.update(config)
                    logger.info("Loaded API config from metadata-service")
        except (asyncio.TimeoutError, httpx.ConnectError, httpx.ConnectTimeout, httpx.HTTPStatusError, Exception):
            # 任何错误都快速跳过，使用默认配置，不记录详细日志（避免日志噪音）
            pass
        finally:
            # 无论成功或失败，都标记为已加载，避免重复尝试
            self._api_config_loaded = True
    
    def _get_optimal_query_params(
        self,
        task_complexity: str,
        query_type: str
    ) -> Dict[str, Any]:
        """基于任务复杂度动态确定查询参数"""
        base_params = {
            "simple": {"limit": 5, "timeout": 3.0},
            "medium": {"limit": 10, "timeout": 5.0},
            "complex": {"limit": 20, "timeout": 10.0},
            "exploratory": {"limit": 50, "timeout": 15.0}
        }
        
        params = base_params.get(task_complexity, base_params["medium"]).copy()
        
        # 根据查询类型调整
        if query_type == "business_entities":
            params["include_relations"] = True
        elif query_type == "data_sources":
            params["include_schema"] = True
        
        return params
    
    def _estimate_task_complexity(self, task: str, context: Dict[str, Any]) -> str:
        """估算任务复杂度"""
        task_lower = task.lower()
        context_str = str(context).lower()
        
        # 简单任务：单一操作、明确目标
        if any(keyword in task_lower for keyword in ["查询", "查", "获取", "get", "fetch"]):
            if len(task) < 50 and len(context_str) < 200:
                return "simple"
        
        # 复杂任务：多步骤、需要分析
        if any(keyword in task_lower for keyword in ["分析", "analyze", "生成报告", "generate report", "综合", "comprehensive"]):
            return "complex"
        
        # 探索性任务：需要探索多个选项
        if any(keyword in task_lower for keyword in ["探索", "explore", "发现", "discover", "查找所有", "find all"]):
            return "exploratory"
        
        # 默认中等复杂度
        return "medium"
    
    def _parse_response(
        self,
        data: Any,
        *possible_keys: str
    ) -> List[Dict[str, Any]]:
        """动态解析API响应（支持多种格式）"""
        if isinstance(data, list):
            return data
        
        if isinstance(data, dict):
            # 尝试多个可能的键
            for key in possible_keys:
                if key in data:
                    value = data[key]
                    if isinstance(value, list):
                        return value
                    elif isinstance(value, dict) and "items" in value:
                        return value["items"]
            
            # 如果都不匹配，尝试常见的响应格式
            for common_key in ["results", "data", "entities", "assets", "items"]:
                if common_key in data:
                    value = data[common_key]
                    if isinstance(value, list):
                        return value
        
        logger.warning(f"Unexpected response format: {type(data)}")
        return []
    
    async def _fetch_with_retry(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """带重试的API调用（带超时保护，避免阻塞）"""
        max_retries = max_retries or self._api_config["retry"]["max_retries"]
        retry_delay = retry_delay or self._api_config["retry"]["retry_delay"]
        
        timeout = timeout or self._api_config["timeouts"]["default"]
        
        for attempt in range(max_retries):
            try:
                client = await self._get_http_client()
                # 使用超时保护，避免长时间阻塞
                response = await asyncio.wait_for(
                    client.get(url, params=params, timeout=timeout),
                    timeout=timeout + 1.0  # 额外1秒缓冲
                )
                response.raise_for_status()
                return response.json()
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    logger.warning(f"API call timeout (attempt {attempt + 1}/{max_retries}): {url}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"API call timeout after {max_retries} attempts: {url}")
                    return None  # 返回None而不是raise，避免中断工作流
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException, httpx.NetworkError) as e:
                # 连接错误或超时，记录但不中断工作流
                if attempt < max_retries - 1:
                    logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数退避
                else:
                    logger.warning(f"API call failed after {max_retries} attempts: {e}, returning None")
                    return None  # 返回None而不是raise，避免中断工作流
            except httpx.HTTPStatusError as e:
                # HTTP错误不重试，直接返回None
                if e.response.status_code == 404:
                    logger.debug(f"API endpoint not found: {url}")
                else:
                    logger.warning(f"API returned error {e.response.status_code}: {url}")
                return None
        
        return None
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析任务的元数据需求（优化版：带缓存）
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            元数据增强计划
        """
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(task_description, context)
            if cache_key in self._analysis_cache:
                cached = self._analysis_cache[cache_key]
                if self._is_cache_valid(cached.get("timestamp"), self._analysis_cache_ttl):
                    logger.debug(f"Using cached analysis result for: {task_description[:50]}")
                    return cached["result"]
            
            # 语义引擎增强：查询相关业务活动
            semantic_enhancement = {}
            if self.semantic_engine:
                try:
                    # 语义引擎的query_intent是同步方法，需要在executor中运行
                    loop = asyncio.get_event_loop()
                    semantic_result = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            self.semantic_engine.query_intent,
                            task_description,
                            context,
                            5,  # top_k
                            0.5  # min_score
                        ),
                        timeout=3.0  # 3秒超时，避免阻塞
                    )
                    if semantic_result and semantic_result.activities:
                        semantic_enhancement = {
                            "related_activities": [
                                {
                                    "id": act.id,
                                    "name": act.name,
                                    "description": act.description,
                                    "score": score
                                }
                                for act, score in zip(semantic_result.activities, semantic_result.scores)
                            ],
                            "semantic_keywords": context.get("query_keywords", [])
                        }
                        logger.info(f"语义引擎增强完成：找到{len(semantic_result.activities)}个相关活动")
                except Exception as e:
                    logger.warning(f"语义引擎查询失败: {e}，继续使用原有分析")
                    semantic_enhancement = {}
            
            prompt = f"""
作为元数据专家，分析这个任务的元数据需求：

任务: {task_description}
当前上下文: {json.dumps(context, ensure_ascii=False, indent=2)}
{f"语义增强信息: {json.dumps(semantic_enhancement, ensure_ascii=False, indent=2)}" if semantic_enhancement else ""}

请分析：
1. **业务实体识别**：涉及哪些业务概念？
2. **数据源映射**：需要什么数据源？
3. **约束条件**：有什么业务约束？
4. **上下文增强**：需要补充什么业务上下文？
{f"5. **语义关联**：基于语义增强信息，识别相关的业务活动和概念" if semantic_enhancement else ""}

返回JSON格式：
{{
    "needs_entity_mapping": true/false,
    "identified_entities": ["实体1", "实体2"],
    "needs_data_source_mapping": true/false,
    "required_data_types": ["数据类型1", "数据类型2"],
    "needs_business_rules": true/false,
    "business_domain": "业务域",
    "constraints": ["约束1", "约束2"],
    "enhancement_plan": {{
        "entities": true/false,
        "data_sources": true/false,
        "business_rules": true/false,
        "semantic_context": true/false
    }},
    {f'"semantic_enhancement": {json.dumps(semantic_enhancement, ensure_ascii=False)}' if semantic_enhancement else ''}
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "metadata_agent",
                fallback="你是一个元数据专家，擅长分析任务的元数据需求。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            # 解析响应
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    enhancement_plan = json.loads(response[json_start:json_end])
                else:
                    enhancement_plan = {
                        "needs_entity_mapping": False,
                        "identified_entities": []
                    }
            else:
                enhancement_plan = response
            
            # 缓存结果
            self._analysis_cache[cache_key] = {
                "result": enhancement_plan,
                "timestamp": time.time()
            }
            
            return enhancement_plan
            
        except Exception as e:
            logger.error(f"Metadata analysis failed: {e}", exc_info=True)
            return {
                "needs_entity_mapping": False,
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        提供元数据增强
        
        Args:
            input_data: 输入数据（包含task或enhancement_plan）
            context: 上下文信息
            
        Returns:
            元数据增强结果
        """
        try:
            # 获取增强计划
            task_description = input_data.get("task", "")
            enhancement_plan = input_data.get("enhancement_plan")
            
            if not enhancement_plan:
                # 如果没有增强计划，先分析任务
                enhancement_plan = await self.analyze_task(task_description, context)
            
            enhancements = {}
            
            # 估算任务复杂度（用于动态参数优化）
            task_complexity = self._estimate_task_complexity(task_description, context)
            
            # 业务实体增强
            if enhancement_plan.get("needs_entity_mapping"):
                try:
                    entities = await self._find_business_entities(
                        enhancement_plan.get("identified_entities", []),
                        task_complexity
                    )
                    enhancements["business_entities"] = entities
                except Exception as e:
                    logger.warning(f"Failed to find business entities: {e}")
                    # 降级：返回空列表而不是失败
                    enhancements["business_entities"] = []
            
            # 数据源映射
            if enhancement_plan.get("needs_data_source_mapping"):
                try:
                    data_sources = await self._find_data_sources(
                        enhancement_plan.get("required_data_types", []),
                        task_complexity
                    )
                    enhancements["data_sources"] = data_sources
                except Exception as e:
                    logger.warning(f"Failed to find data sources: {e}")
                    # 降级：返回空列表而不是失败
                    enhancements["data_sources"] = []
            
            # 业务规则增强
            if enhancement_plan.get("needs_business_rules"):
                try:
                    business_rules = await self._get_business_rules(
                        enhancement_plan.get("business_domain", ""),
                        task_complexity
                    )
                    enhancements["business_rules"] = business_rules
                except Exception as e:
                    logger.warning(f"Failed to get business rules: {e}")
                    # 降级：返回空列表而不是失败
                    enhancements["business_rules"] = []
            
            # 构建语义上下文
            semantic_context = await self._build_semantic_context(
                enhancements,
                context
            )
            
            return {
                "agent_type": "metadata",
                "execution_success": True,  # 显式标记为成功
                "enhancements_provided": enhancements,
                "semantic_context": semantic_context,
                "constraints_identified": enhancement_plan.get("constraints", []),
                "enhancement_plan": enhancement_plan
            }
            
        except Exception as e:
            logger.error(f"Metadata agent execution failed: {e}", exc_info=True)
            raise
    
    async def _find_business_entities(
        self,
        entity_names: List[str],
        task_complexity: str = "medium"
    ) -> List[Dict[str, Any]]:
        """查找业务实体（优化版：带缓存和批量查询）"""
        try:
            if not entity_names:
                return []
            
            await self._load_api_config()
            
            # 检查缓存
            cached_entities = []
            uncached_names = []
            
            for name in entity_names:
                cache_key = f"entity:{name.lower()}"
                if cache_key in self._entity_cache:
                    cached = self._entity_cache[cache_key]
                    if self._is_cache_valid(cached.get("timestamp"), self._entity_cache_ttl):
                        cached_entities.append(cached["entity"])
                    else:
                        uncached_names.append(name)
                else:
                    uncached_names.append(name)
            
            # 批量查询未缓存的实体
            if uncached_names:
                new_entities = await self._fetch_entities_batch(uncached_names, task_complexity)
                
                # 更新缓存
                for entity in new_entities:
                    entity_name = entity.get("name", "").lower()
                    if entity_name:
                        self._entity_cache[f"entity:{entity_name}"] = {
                            "entity": entity,
                            "timestamp": time.time()
                        }
                
                cached_entities.extend(new_entities)
            
            # 去重（基于ID或名称）
            seen = set()
            unique_entities = []
            for entity in cached_entities:
                entity_id = entity.get("id") or entity.get("name", "")
                if entity_id and entity_id not in seen:
                    seen.add(entity_id)
                    unique_entities.append(entity)
            
            logger.info(f"Found {len(unique_entities)} business entities for {entity_names} (cached: {len(cached_entities) - len(uncached_names) if uncached_names else len(cached_entities)})")
            return unique_entities
            
        except Exception as e:
            logger.error(f"Error finding business entities: {e}", exc_info=True)
            return []
    
    async def _fetch_entities_batch(
        self,
        entity_names: List[str],
        task_complexity: str
    ) -> List[Dict[str, Any]]:
        """批量获取业务实体（优化N+1问题）"""
        try:
            base_url = self._api_config["base_url"]
            endpoint = self._api_config["endpoints"]["business_entities"]
            query_params = self._get_optimal_query_params(task_complexity, "business_entities")
            
            # 尝试批量查询（如果API支持）
            try:
                client = await self._get_http_client()
                # 尝试使用搜索API批量查询
                response = await self._fetch_with_retry(
                    f"{base_url}{endpoint}",
                    params={
                        "search": " ".join(entity_names[:5]),  # 合并搜索词
                        "limit": query_params["limit"] * len(entity_names)  # 动态调整limit
                    }
                )
                
                if response:
                    entities = self._parse_response(response, "items", "results", "entities", "data")
                    # 过滤匹配的实体
                    matched_entities = []
                    entity_names_lower = [name.lower() for name in entity_names]
                    for entity in entities:
                        entity_name = entity.get("name", "").lower()
                        display_name = entity.get("display_name", "").lower()
                        if any(name in entity_name or name in display_name for name in entity_names_lower):
                            matched_entities.append(entity)
                    return matched_entities
            except Exception as e:
                logger.debug(f"Batch query failed, falling back to individual queries: {e}")
            
            # 降级：并行查询（如果批量API不支持）
            tasks = []
            for entity_name in entity_names:
                tasks.append(self._fetch_single_entity(entity_name, query_params))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            entities = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Failed to fetch entity: {result}")
                elif result:
                    if isinstance(result, list):
                        entities.extend(result)
                    else:
                        entities.append(result)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error fetching entities in batch: {e}")
            return []
    
    async def _fetch_single_entity(
        self,
        entity_name: str,
        query_params: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """获取单个业务实体"""
        try:
            base_url = self._api_config["base_url"]
            endpoint = self._api_config["endpoints"]["business_entities"]
            
            response = await self._fetch_with_retry(
                f"{base_url}{endpoint}",
                params={"search": entity_name, "limit": query_params["limit"]}
            )
            
            if response:
                return self._parse_response(response, "items", "results", "entities", "data")
            
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch entity '{entity_name}': {e}")
            return None
    
    async def _ensure_ea_service_initialized(self):
        """确保EA服务已初始化（延迟初始化）"""
        if self._ea_service_initialized:
            return
        
        if EA_SERVICES_AVAILABLE and EAKnowledgeGraph:
            try:
                from database.src.core.session import SessionLocal
                from database.src.models.enterprise_architecture_models import DataEntity
                
                # 在executor中初始化，避免阻塞
                # 使用SessionLocal()而不是get_db()，因为get_db()是生成器，不适合在executor中使用
                def init_ea_services():
                    # 确保SessionLocal已配置
                    from database.src.core.session import init_session_factory
                    try:
                        init_session_factory()
                    except:
                        pass  # 可能已经初始化
                    
                    db = SessionLocal()
                    try:
                        ea_graph = EAKnowledgeGraph(db)
                        ea_hybrid = None
                        if EAHybridQuery:
                            try:
                                from metadata_service.src.services.ea_vectorization_service import EAVectorizationService
                                ea_vector_service = EAVectorizationService(db)
                                ea_hybrid = EAHybridQuery(db, ea_graph, ea_vector_service)
                            except Exception as e:
                                logger.warning(f"EA混合查询引擎初始化失败: {e}，将只使用图谱查询")
                        return ea_graph, ea_hybrid, db
                    except Exception:
                        try:
                            db.close()
                        except:
                            pass
                        raise
                
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, init_ea_services)
                self.ea_graph_service, self.ea_hybrid_query, self._ea_db = result
                
                self._ea_service_initialized = True
                logger.info("EA服务初始化成功")
            except Exception as e:
                logger.warning(f"EA服务初始化失败: {e}，将使用原有功能")
                self.ea_graph_service = None
                self.ea_hybrid_query = None
                self._ea_db = None
                self._ea_service_initialized = True  # 标记为已尝试，避免重复尝试
    
    async def _find_data_sources(
        self,
        data_types: List[str],
        task_complexity: str = "medium"
    ) -> List[Dict[str, Any]]:
        """查找数据源（增强版：集成EA知识图谱查询）"""
        try:
            if not data_types:
                return []
            
            await self._load_api_config()
            
            # 确保EA服务已初始化
            await self._ensure_ea_service_initialized()
            
            # EA知识图谱增强：查询相关的数据实体
            ea_data_entities = []
            if self.ea_graph_service:
                try:
                    # 构建查询关键词
                    query_text = " ".join(data_types)
                    
                    # 使用EA知识图谱查询数据实体
                    # 从数据库查询DataEntity（使用已初始化的数据库会话）
                    from database.src.models.enterprise_architecture_models import DataEntity
                    
                    # 如果已有数据库会话，使用它；否则创建新会话
                    if self._ea_db:
                        db = self._ea_db
                    else:
                        from database.src.core.session import SessionLocal
                        db = SessionLocal()
                    
                    loop = asyncio.get_event_loop()
                    # 在executor中执行数据库查询
                    def query_entities():
                        try:
                            return db.query(DataEntity).filter(
                                DataEntity.name.ilike(f"%{query_text}%")
                            ).limit(5).all()
                        except Exception as e:
                            logger.warning(f"EA数据实体查询失败: {e}")
                            return []
                    
                    entities = await asyncio.wait_for(
                        loop.run_in_executor(None, query_entities),
                        timeout=2.0  # 2秒超时
                    )
                    
                    # 如果使用的是新创建的会话，关闭它
                    if not self._ea_db and db:
                        try:
                            db.close()
                        except:
                            pass
                    
                    if entities:
                        ea_data_entities = [
                            {
                                "id": entity.id,
                                "name": entity.name,
                                "display_name": entity.display_name or entity.name,
                                "asset_type": "data_entity",
                                "source_system": "ea_knowledge_graph",
                                "description": entity.description or "",
                                "metadata": {
                                    "ea_entity_type": "DataEntity",
                                    "entity_id": entity.id
                                }
                            }
                            for entity in entities
                        ]
                        logger.info(f"EA知识图谱增强完成：找到{len(ea_data_entities)}个数据实体")
                except Exception as e:
                    logger.warning(f"EA知识图谱查询失败: {e}，继续使用原有查询")
                    ea_data_entities = []
            
            # 检查缓存
            cached_sources = []
            uncached_types = []
            
            for data_type in data_types:
                cache_key = f"data_source:{data_type.lower()}"
                if cache_key in self._data_source_cache:
                    cached = self._data_source_cache[cache_key]
                    if self._is_cache_valid(cached.get("timestamp"), self._data_source_cache_ttl):
                        cached_sources.extend(cached["sources"])
                    else:
                        uncached_types.append(data_type)
                else:
                    uncached_types.append(data_type)
            
            # 批量查询未缓存的数据源
            if uncached_types:
                new_sources = await self._fetch_data_sources_batch(uncached_types, task_complexity)
                
                # 更新缓存（按类型分组）
                # 注意：由于批量查询返回的是所有类型的合并结果，我们需要按类型分别缓存
                # 这里简化处理，将所有结果缓存到每个类型下
                for data_type in uncached_types:
                    self._data_source_cache[f"data_source:{data_type.lower()}"] = {
                        "sources": new_sources,  # 缓存所有结果（可能包含其他类型，但这样可以避免重复查询）
                        "timestamp": time.time()
                    }
                
                cached_sources.extend(new_sources)
            
            # 合并EA知识图谱查询结果
            all_sources = cached_sources + ea_data_entities
            
            # 去重
            seen = set()
            unique_sources = []
            for source in all_sources:
                source_id = source.get("id") or source.get("name", "")
                if source_id and source_id not in seen:
                    seen.add(source_id)
                    unique_sources.append(source)
            
            # 特殊处理：如果查询的是组织架构相关数据，添加组织架构API数据源
            org_keywords = ["组织架构", "organization", "org", "部门", "员工", "组织", "enterprise_architecture"]
            if any(keyword in str(data_types).lower() for keyword in org_keywords):
                # 检查是否已经有组织架构数据源
                has_org_source = any(
                    source.get("asset_type") == "enterprise_architecture" or
                    source.get("name") == "organization_architecture" or
                    "组织架构" in str(source.get("display_name", "")).lower() or
                    "organization" in str(source.get("name", "")).lower()
                    for source in unique_sources
                )
                
                if not has_org_source:
                    # 添加组织架构API数据源
                    org_source = {
                        "id": "enterprise_architecture_api",
                        "name": "organization_architecture",
                        "display_name": "组织架构数据",
                        "asset_type": "enterprise_architecture",
                        "source_system": "metadata-service",
                        "source_path": "/api/enterprise-architecture/organizations",
                        "description": "企业组织架构数据，包括部门、岗位、人员等信息",
                        "status": "active",
                        "metadata": {
                            "api_endpoint": "/api/enterprise-architecture/organizations",
                            "query_method": "GET"
                        }
                    }
                    unique_sources.append(org_source)
                    logger.info("Added enterprise architecture API data source for organization query")
            
            logger.info(f"Found {len(unique_sources)} data sources for {data_types} (cached: {len(cached_sources) - len(uncached_types) if uncached_types else len(cached_sources)})")
            return unique_sources
            
        except Exception as e:
            logger.error(f"Error finding data sources: {e}", exc_info=True)
            return []
    
    async def _fetch_data_sources_batch(
        self,
        data_types: List[str],
        task_complexity: str
    ) -> List[Dict[str, Any]]:
        """批量获取数据源（优化N+1问题）"""
        try:
            base_url = self._api_config["base_url"]
            endpoint = self._api_config["endpoints"]["data_assets"]
            query_params = self._get_optimal_query_params(task_complexity, "data_sources")
            
            # 并行查询多个数据类型
            tasks = []
            for data_type in data_types:
                tasks.append(self._fetch_single_data_source(data_type, query_params))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            data_sources = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Failed to fetch data source: {result}")
                elif result:
                    if isinstance(result, list):
                        data_sources.extend(result)
                    else:
                        data_sources.append(result)
            
            return data_sources
            
        except Exception as e:
            logger.error(f"Error fetching data sources in batch: {e}")
            return []
    
    async def _fetch_single_data_source(
        self,
        data_type: str,
        query_params: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """获取单个数据源"""
        try:
            base_url = self._api_config["base_url"]
            endpoint = self._api_config["endpoints"]["data_assets"]
            
            response = await self._fetch_with_retry(
                f"{base_url}{endpoint}",
                params={"asset_type": data_type, "limit": query_params["limit"]}
            )
            
            if response:
                return self._parse_response(response, "items", "results", "assets", "data")
            
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch data source for '{data_type}': {e}")
            return None
    
    async def _get_business_rules(
        self,
        business_domain: str,
        task_complexity: str = "medium"
    ) -> List[Dict[str, Any]]:
        """获取业务规则（优化版：支持专门API和降级方案）"""
        try:
            if not business_domain:
                return []
            
            await self._load_api_config()
            
            # 首先尝试使用专门的业务规则API（如果存在）
            try:
                base_url = self._api_config["base_url"]
                endpoint = self._api_config["endpoints"].get("business_rules")
                
                if endpoint:
                    response = await self._fetch_with_retry(
                        f"{base_url}{endpoint}",
                        params={"domain": business_domain, "limit": 20}
                    )
                    
                    if response:
                        rules = self._parse_response(response, "items", "results", "rules", "data")
                        if rules:
                            logger.info(f"Found {len(rules)} business rules from API for domain '{business_domain}'")
                            return rules
            except Exception as e:
                logger.debug(f"Business rules API not available: {e}, trying fallback")
            
            # 降级：从业务实体中提取规则
            try:
                entities = await self._find_business_entities([business_domain], task_complexity)
                rules = []
                for entity in entities:
                    # 动态检测规则字段（不硬编码）
                    for rule_key in ["rules", "constraints", "business_rules", "validation_rules"]:
                        if rule_key in entity:
                            rule_value = entity[rule_key]
                            if isinstance(rule_value, list):
                                rules.extend(rule_value)
                            elif rule_value:
                                rules.append(rule_value)
                
                logger.info(f"Found {len(rules)} business rules from entities for domain '{business_domain}'")
                return rules
            except Exception as e:
                logger.warning(f"Failed to get business rules: {e}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting business rules: {e}", exc_info=True)
            return []
    
    async def _build_semantic_context(
        self,
        enhancements: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建语义上下文（优化版：带降级方案）"""
        semantic_context = {
            "business_entities": enhancements.get("business_entities", []),
            "data_sources": enhancements.get("data_sources", []),
            "business_rules": enhancements.get("business_rules", []),
            "context_summary": ""
        }
        
        # 使用LLM生成上下文摘要
        try:
            # 限制数据量，避免提示词过长
            entities_summary = json.dumps(enhancements.get('business_entities', [])[:5], ensure_ascii=False, indent=2)
            sources_summary = json.dumps(enhancements.get('data_sources', [])[:5], ensure_ascii=False, indent=2)
            rules_summary = json.dumps(enhancements.get('business_rules', [])[:3], ensure_ascii=False, indent=2)
            
            prompt = f"""
基于以下元数据增强信息，生成业务上下文摘要：

业务实体: {entities_summary}
数据源: {sources_summary}
业务规则: {rules_summary}

请生成简洁的业务上下文摘要（1-2句话）。
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "metadata_agent_context",
                fallback="你是一个业务上下文专家，擅长生成业务上下文摘要。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            semantic_context["context_summary"] = response if isinstance(response, str) else str(response)
            
        except Exception as e:
            logger.warning(f"Failed to build semantic context with LLM: {e}")
            # 降级：基于规则的摘要生成
            semantic_context["context_summary"] = self._generate_fallback_summary(enhancements)
        
        return semantic_context
    
    def _generate_fallback_summary(self, enhancements: Dict[str, Any]) -> str:
        """生成降级摘要（不使用LLM）"""
        parts = []
        
        entities = enhancements.get("business_entities", [])
        if entities:
            entity_names = [e.get("name", e.get("display_name", "")) for e in entities[:3]]
            parts.append(f"涉及业务实体：{', '.join(filter(None, entity_names))}")
        
        data_sources = enhancements.get("data_sources", [])
        if data_sources:
            source_names = [s.get("name", s.get("display_name", "")) for s in data_sources[:3]]
            parts.append(f"数据源：{', '.join(filter(None, source_names))}")
        
        rules = enhancements.get("business_rules", [])
        if rules:
            parts.append(f"包含{len(rules)}条业务规则")
        
        if parts:
            return "；".join(parts) + "。"
        else:
            return "已提供业务上下文增强信息。"

