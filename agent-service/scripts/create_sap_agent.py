"""
创建SAP查询智能体脚本
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models.agent_models import AgentCreate, AgentCapability
from src.core.agent_manager import agent_manager


async def create_sap_agent():
    """创建SAP查询智能体"""
    sap_agent_data = AgentCreate(
        name="SAP查询智能体",
        description="专门用于SAP ERP数据查询和分析的智能体，集成sap-odata-to-mcp-server。可以查询销售订单、采购订单、物料、客户、供应商等数据，并对查询结果进行深入分析。",
        capabilities=[AgentCapability.DATA_ANALYSIS],
        system_prompt="""你是一个专业的SAP ERP数据查询和分析专家。

你的主要职责：
1. 通过MCP工具（sap_query）查询SAP系统中的各种业务数据
2. 理解用户的自然语言查询需求，自动转换为合适的SAP查询
3. 对查询结果进行深入分析，提供业务洞察和建议

可查询的数据类型：
- 销售订单（I_SalesOrder）：包括订单号、客户、日期、金额、状态等
- 采购订单：包括订单号、供应商、日期、金额等
- 物料主数据：包括物料号、描述、价格等
- 客户主数据：包括客户号、名称、地址等
- 供应商主数据：包括供应商号、名称等

查询能力：
- 支持自然语言查询，如"查询9月份的销售订单"
- 支持日期范围过滤，如"查询2024年9月的订单"
- 支持条件过滤，如"查询金额大于10000的订单"
- 自动解析日期条件（如"9月份"、"上个月"等）

分析能力：
- 数据概览和统计
- 趋势分析
- 异常识别
- 业务建议

使用MCP工具：
- 工具名称：sap_query
- 参数：table（表名，如I_SalesOrder）、query（查询条件）

请始终使用sap_query工具来查询SAP数据，不要直接回答假设的数据。""",
        config={
            "preferred_tools": ["sap_query"],
            "auto_analysis": True,
            "default_table": "I_SalesOrder"
        },
        metadata={
            "mcp_server": "sap-mcp-server",
            "integration_type": "mcp_tool",
            "version": "1.0.0"
        }
    )
    
    try:
        agent = await agent_manager.create_agent(sap_agent_data, created_by="system")
        print(f"✅ SAP查询智能体创建成功！")
        print(f"   ID: {agent.id}")
        print(f"   名称: {agent.name}")
        print(f"   描述: {agent.description}")
        print(f"   能力: {[c.value for c in agent.capabilities]}")
        return agent
    except Exception as e:
        print(f"❌ 创建SAP查询智能体失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(create_sap_agent())


