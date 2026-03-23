"""
智能体节点配置模板
提供基础模板和常用预设，方便快速配置AgentNode
"""
from typing import Dict, Any

# 基础智能体节点配置模板
BASIC_AGENT_NODE_TEMPLATE: Dict[str, Any] = {
    "type": "agent",
    "name": "agent_node",
    "description": "智能体节点",
    "config": {
        # 必需配置
        "agent_id": "required",  # 必须指定智能体ID
        
        # 执行配置
        "execution_mode": "sync",  # sync/async，第一阶段使用sync
        "enable_streaming": False,  # 是否启用流式输出
        "timeout": 300,  # 超时时间（秒），默认5分钟
        
        # 重试配置
        "retry_count": 3,  # 重试次数
        "retry_delay": 5,  # 初始重试延迟（秒）
        "retry_backoff_multiplier": 2.0,  # 指数退避倍数
        "max_retry_delay": 60,  # 最大重试延迟（秒）
        
        # 上下文管理
        "context_window_size": 10,  # 上下文窗口大小（对话历史条数）
        "preserve_conversation": True,  # 是否保留对话历史
        
        # 输入输出映射
        "input_mapping": {},  # 输入字段映射，例如: {"content": "data.message"}
        "output_mapping": {},  # 输出字段映射，例如: {"result": "output.content"}
        
        # 缓存配置
        "enable_cache": True,  # 是否启用缓存
        "cache_ttl": 300,  # 缓存TTL（秒），默认5分钟
        "memory_cache_size": 1000,  # 内存缓存大小
        
        # 错误处理
        "enable_fallback": True,  # 是否启用降级策略
        "fallback_response": "智能体暂时不可用",  # 降级响应内容
    }
}

# 常用智能体节点配置预设
AGENT_NODE_PRESETS: Dict[str, Dict[str, Any]] = {
    "code_review_agent": {
        "type": "agent",
        "name": "code_review_agent",
        "description": "代码审查智能体",
        "config": {
            **BASIC_AGENT_NODE_TEMPLATE["config"],
            "agent_id": "code_review_agent",
            "enable_streaming": True,  # 代码审查需要实时反馈
            "timeout": 600,  # 代码审查可能需要更长时间
            "input_mapping": {
                "content": "input.code_content",  # 从input.code_content获取代码内容
                "review_rules": "config.quality_rules"  # 从config.quality_rules获取审查规则
            },
            "output_mapping": {
                "issues": "output.code_issues",  # 将问题映射到output.code_issues
                "suggestions": "output.improvement_suggestions"  # 将建议映射到output.improvement_suggestions
            },
            "context_window_size": 20,  # 代码审查需要更多上下文
        }
    },
    
    "data_analysis_agent": {
        "type": "agent",
        "name": "data_analysis_agent",
        "description": "数据分析智能体",
        "config": {
            **BASIC_AGENT_NODE_TEMPLATE["config"],
            "agent_id": "data_analysis_agent",
            "timeout": 600,  # 数据分析需要更长时间
            "input_mapping": {
                "content": "input.dataset",  # 从input.dataset获取数据集
                "analysis_type": "config.analysis_method"  # 从config.analysis_method获取分析方法
            },
            "output_mapping": {
                "result": "output.analysis_result",  # 将分析结果映射到output.analysis_result
                "insights": "output.data_insights"  # 将洞察映射到output.data_insights
            },
            "enable_cache": True,  # 数据分析结果可以缓存
            "cache_ttl": 3600,  # 缓存1小时
        }
    },
    
    "customer_service_agent": {
        "type": "agent",
        "name": "customer_service_agent",
        "description": "客服智能体",
        "config": {
            **BASIC_AGENT_NODE_TEMPLATE["config"],
            "agent_id": "customer_service_agent",
            "enable_streaming": True,  # 客服对话需要实时响应
            "timeout": 120,  # 客服对话超时时间较短
            "input_mapping": {
                "content": "input.message",  # 从input.message获取用户消息
                "user_context": "state.user_context"  # 从state.user_context获取用户上下文
            },
            "output_mapping": {
                "response": "output.message",  # 将回复映射到output.message
                "intent": "output.user_intent"  # 将用户意图映射到output.user_intent
            },
            "context_window_size": 30,  # 客服需要更多对话历史
            "preserve_conversation": True,  # 必须保留对话历史
            "enable_fallback": True,  # 客服必须启用降级
            "fallback_response": "抱歉，我暂时无法处理您的问题，请稍后再试或联系人工客服。",
        }
    },
    
    "content_generation_agent": {
        "type": "agent",
        "name": "content_generation_agent",
        "description": "内容生成智能体",
        "config": {
            **BASIC_AGENT_NODE_TEMPLATE["config"],
            "agent_id": "content_generation_agent",
            "timeout": 300,
            "input_mapping": {
                "content": "input.prompt",  # 从input.prompt获取生成提示
                "style": "config.content_style",  # 从config.content_style获取内容风格
                "length": "config.content_length"  # 从config.content_length获取内容长度
            },
            "output_mapping": {
                "content": "output.generated_content",  # 将生成内容映射到output.generated_content
                "metadata": "output.content_metadata"  # 将元数据映射到output.content_metadata
            },
            "enable_cache": True,  # 相同提示可以缓存
            "cache_ttl": 1800,  # 缓存30分钟
        }
    },
    
    "qa_agent": {
        "type": "agent",
        "name": "qa_agent",
        "description": "问答智能体",
        "config": {
            **BASIC_AGENT_NODE_TEMPLATE["config"],
            "agent_id": "qa_agent",
            "timeout": 180,
            "input_mapping": {
                "content": "input.question",  # 从input.question获取问题
                "context": "input.knowledge_base"  # 从input.knowledge_base获取知识库上下文
            },
            "output_mapping": {
                "answer": "output.answer",  # 将答案映射到output.answer
                "confidence": "output.confidence_score",  # 将置信度映射到output.confidence_score
                "sources": "output.source_references"  # 将来源映射到output.source_references
            },
            "context_window_size": 15,
            "enable_cache": True,  # 相同问题可以缓存
            "cache_ttl": 3600,  # 缓存1小时
        }
    },
    
    "translation_agent": {
        "type": "agent",
        "name": "translation_agent",
        "description": "翻译智能体",
        "config": {
            **BASIC_AGENT_NODE_TEMPLATE["config"],
            "agent_id": "translation_agent",
            "timeout": 120,
            "input_mapping": {
                "content": "input.text",  # 从input.text获取待翻译文本
                "source_lang": "config.source_language",  # 从config.source_language获取源语言
                "target_lang": "config.target_language"  # 从config.target_language获取目标语言
            },
            "output_mapping": {
                "translation": "output.translated_text",  # 将翻译结果映射到output.translated_text
                "detected_lang": "output.detected_language"  # 将检测到的语言映射到output.detected_language
            },
            "enable_cache": True,  # 翻译结果可以缓存
            "cache_ttl": 7200,  # 缓存2小时
        }
    },
}


def get_template(template_name: str = "basic") -> Dict[str, Any]:
    """
    获取配置模板
    
    Args:
        template_name: 模板名称，可选值：
            - "basic": 基础模板
            - "code_review_agent": 代码审查智能体
            - "data_analysis_agent": 数据分析智能体
            - "customer_service_agent": 客服智能体
            - "content_generation_agent": 内容生成智能体
            - "qa_agent": 问答智能体
            - "translation_agent": 翻译智能体
    
    Returns:
        配置模板字典
    
    Raises:
        ValueError: 如果模板名称不存在
    """
    if template_name == "basic":
        return BASIC_AGENT_NODE_TEMPLATE.copy()
    
    if template_name in AGENT_NODE_PRESETS:
        return AGENT_NODE_PRESETS[template_name].copy()
    
    raise ValueError(f"Unknown template name: {template_name}. Available: basic, {', '.join(AGENT_NODE_PRESETS.keys())}")


def create_agent_node_config(
    agent_id: str,
    name: str = "agent_node",
    description: str = "",
    **kwargs
) -> Dict[str, Any]:
    """
    创建智能体节点配置（便捷函数）
    
    Args:
        agent_id: 智能体ID（必需）
        name: 节点名称
        description: 节点描述
        **kwargs: 其他配置项，会覆盖模板默认值
    
    Returns:
        完整的节点配置字典
    
    Example:
        >>> config = create_agent_node_config(
        ...     agent_id="my_agent",
        ...     name="my_agent_node",
        ...     timeout=600,
        ...     enable_streaming=True
        ... )
    """
    config = BASIC_AGENT_NODE_TEMPLATE.copy()
    config["name"] = name
    config["description"] = description or f"智能体节点: {agent_id}"
    config["config"]["agent_id"] = agent_id
    
    # 更新配置项
    if "config" in kwargs:
        config["config"].update(kwargs["config"])
        del kwargs["config"]
    
    # 直接更新config中的字段
    for key, value in kwargs.items():
        if key in config["config"]:
            config["config"][key] = value
    
    return config


def list_available_presets() -> list:
    """
    列出所有可用的预设模板
    
    Returns:
        预设模板名称列表
    """
    return list(AGENT_NODE_PRESETS.keys())

