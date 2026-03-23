"""
测试工作流定义 - 包含智能体节点的工作流示例
用于验证AgentNode的功能和集成
"""
from typing import Dict, Any

# 测试工作流：智能代码审查流程
TEST_AGENT_WORKFLOW: Dict[str, Any] = {
    "name": "智能代码审查流程",
    "description": "使用智能体节点进行代码审查的测试工作流",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "name": "开始",
            "description": "工作流开始节点"
        },
        {
            "id": "code_review",
            "type": "agent",
            "name": "代码审查智能体",
            "description": "使用智能体进行代码审查",
            "config": {
                "agent_id": "code_review_agent",  # 智能体ID
                "input_mapping": {
                    "content": "input.code_content"  # 从workflow.input.code_content获取代码内容
                },
                "output_mapping": {
                    "issues": "output.code_issues",  # 将问题映射到output.code_issues
                    "suggestions": "output.improvement_suggestions"  # 将建议映射到output.improvement_suggestions
                },
                "enable_streaming": True,  # 启用流式输出
                "timeout": 600,  # 超时时间10分钟
                "context_window_size": 20,  # 上下文窗口大小
                "enable_cache": True,  # 启用缓存
                "cache_ttl": 3600,  # 缓存1小时
            }
        },
        {
            "id": "end",
            "type": "end",
            "name": "结束",
            "description": "工作流结束节点"
        }
    ],
    "edges": [
        {
            "from": "start",
            "to": "code_review",
            "condition": None  # 无条件连接
        },
        {
            "from": "code_review",
            "to": "end",
            "condition": None
        }
    ]
}

# 测试工作流：多智能体协作流程
MULTI_AGENT_WORKFLOW: Dict[str, Any] = {
    "name": "多智能体协作流程",
    "description": "多个智能体节点协作的测试工作流",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "name": "开始"
        },
        {
            "id": "content_generation",
            "type": "agent",
            "name": "内容生成智能体",
            "config": {
                "agent_id": "content_generation_agent",
                "input_mapping": {
                    "content": "input.prompt"
                },
                "output_mapping": {
                    "content": "output.generated_content"
                }
            }
        },
        {
            "id": "translation",
            "type": "agent",
            "name": "翻译智能体",
            "config": {
                "agent_id": "translation_agent",
                "input_mapping": {
                    "content": "content_generation_output.generated_content",  # 使用上一个节点的输出
                    "source_lang": "config.source_language",
                    "target_lang": "config.target_language"
                },
                "output_mapping": {
                    "translation": "output.translated_content"
                }
            }
        },
        {
            "id": "end",
            "type": "end",
            "name": "结束"
        }
    ],
    "edges": [
        {"from": "start", "to": "content_generation"},
        {"from": "content_generation", "to": "translation"},
        {"from": "translation", "to": "end"}
    ]
}

# 测试工作流：智能客服流程
CUSTOMER_SERVICE_WORKFLOW: Dict[str, Any] = {
    "name": "智能客服流程",
    "description": "使用智能体节点提供客服服务的测试工作流",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "name": "开始"
        },
        {
            "id": "customer_service",
            "type": "agent",
            "name": "客服智能体",
            "config": {
                "agent_id": "customer_service_agent",
                "enable_streaming": True,
                "timeout": 120,
                "input_mapping": {
                    "content": "input.message",
                    "user_context": "state.user_context"
                },
                "output_mapping": {
                    "response": "output.message",
                    "intent": "output.user_intent"
                },
                "context_window_size": 30,
                "preserve_conversation": True,
                "enable_fallback": True,
                "fallback_response": "抱歉，我暂时无法处理您的问题，请稍后再试或联系人工客服。"
            }
        },
        {
            "id": "end",
            "type": "end",
            "name": "结束"
        }
    ],
    "edges": [
        {"from": "start", "to": "customer_service"},
        {"from": "customer_service", "to": "end"}
    ]
}

# 测试工作流：数据分析流程
DATA_ANALYSIS_WORKFLOW: Dict[str, Any] = {
    "name": "数据分析流程",
    "description": "使用智能体节点进行数据分析的测试工作流",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "name": "开始"
        },
        {
            "id": "data_analysis",
            "type": "agent",
            "name": "数据分析智能体",
            "config": {
                "agent_id": "data_analysis_agent",
                "timeout": 600,
                "input_mapping": {
                    "content": "input.dataset",
                    "analysis_type": "config.analysis_method"
                },
                "output_mapping": {
                    "result": "output.analysis_result",
                    "insights": "output.data_insights"
                },
                "enable_cache": True,
                "cache_ttl": 3600
            }
        },
        {
            "id": "end",
            "type": "end",
            "name": "结束"
        }
    ],
    "edges": [
        {"from": "start", "to": "data_analysis"},
        {"from": "data_analysis", "to": "end"}
    ]
}


def get_test_workflow(workflow_name: str = "code_review") -> Dict[str, Any]:
    """
    获取测试工作流定义
    
    Args:
        workflow_name: 工作流名称，可选值：
            - "code_review": 智能代码审查流程
            - "multi_agent": 多智能体协作流程
            - "customer_service": 智能客服流程
            - "data_analysis": 数据分析流程
    
    Returns:
        工作流定义字典
    
    Raises:
        ValueError: 如果工作流名称不存在
    """
    workflows = {
        "code_review": TEST_AGENT_WORKFLOW,
        "multi_agent": MULTI_AGENT_WORKFLOW,
        "customer_service": CUSTOMER_SERVICE_WORKFLOW,
        "data_analysis": DATA_ANALYSIS_WORKFLOW,
    }
    
    if workflow_name not in workflows:
        raise ValueError(
            f"Unknown workflow name: {workflow_name}. "
            f"Available: {', '.join(workflows.keys())}"
        )
    
    return workflows[workflow_name].copy()


def list_test_workflows() -> list:
    """
    列出所有可用的测试工作流
    
    Returns:
        测试工作流名称列表
    """
    return ["code_review", "multi_agent", "customer_service", "data_analysis"]


# 测试输入数据示例
TEST_INPUT_DATA = {
    "code_review": {
        "code_content": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
        """.strip()
    },
    "multi_agent": {
        "prompt": "写一篇关于人工智能的短文",
        "source_language": "zh",
        "target_language": "en"
    },
    "customer_service": {
        "message": "我想查询订单状态",
        "user_context": {
            "user_id": "user_123",
            "order_id": "order_456"
        }
    },
    "data_analysis": {
        "dataset": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "analysis_method": "statistical_summary"
    }
}


if __name__ == "__main__":
    # 示例：打印测试工作流
    print("=" * 60)
    print("测试工作流列表")
    print("=" * 60)
    for name in list_test_workflows():
        workflow = get_test_workflow(name)
        print(f"\n工作流: {workflow['name']}")
        print(f"描述: {workflow.get('description', 'N/A')}")
        print(f"节点数: {len(workflow['nodes'])}")
        print(f"连接数: {len(workflow['edges'])}")
        
        # 列出智能体节点
        agent_nodes = [n for n in workflow['nodes'] if n.get('type') == 'agent']
        if agent_nodes:
            print("智能体节点:")
            for node in agent_nodes:
                print(f"  - {node['name']} (agent_id: {node['config'].get('agent_id')})")

