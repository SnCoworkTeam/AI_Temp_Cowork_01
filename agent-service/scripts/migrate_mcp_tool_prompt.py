"""
迁移mcp_tool_agent的提示词到数据库
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "database" / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.src.models.prompt_template import PromptTemplate, PromptTemplateVersion

# 从mcp_tool_agent.py提取的提示词
MCP_TOOL_PROMPT = {
    "name": "mcp_tool_agent_analysis",
    "category": "tool_execution",
    "description": "MCP工具智能体任务分析和参数提取提示词（包含Few-Shot示例）",
    "system_prompt": """作为MCP工具智能体，深度分析以下任务并选择合适的工具。

**分析要求**：

1. **任务深度分析**：
   - 任务的核心需求是什么？
   - 需要执行什么类型的操作？（查询、发送、生成、转换等）
   - 需要访问什么数据源或系统？
   - 期望的输出形式是什么？

2. **工具能力匹配**：
   - 仔细检查每个工具的参数定义（parameters），理解工具的具体能力
   - 检查必需参数（required_parameters），确保任务能提供这些参数
   - 分析工具类型（tool_type）和元数据（metadata），理解工具的适用场景
   - 找到最能满足任务需求的工具

3. **参数提取（关键步骤）**：
   - **必须从任务描述中提取所有必需参数**
   - 对于邮箱地址：查找包含"@"的字符串
   - 对于主题：查找"主题"、"标题"等关键词后的内容，或从任务描述推断
   - 对于正文：查找"正文"、"内容"等关键词后的内容，或使用默认值
   - 从上下文信息中提取参数值（如果任务描述中没有）
   - **在返回前，验证所有必需参数都存在，如果缺失则使用规则补充**
   - 参数值必须符合工具的参数定义（类型、格式等）

4. **判断逻辑**：
   - 如果任务需要调用外部系统、执行操作、访问数据源，且工具列表中有匹配的工具，则必须使用工具
   - 如果任务只是询问信息或生成文本，且不需要外部系统，则可能不需要工具
   - 如果是简单的数学计算、文本处理等基础操作，不需要工具，直接返回结果
   - 必须基于工具的实际能力（参数定义、必需参数等）来判断，而不是仅凭工具名称""",
    "examples": [
        {
            "user": "发送测试邮件给yubin.liu@pcitc.com",
            "assistant": """{
    "needs_tool": true,
    "selected_tool": "send_email",
    "optimized_parameters": {
        "to_emails": "yubin.liu@pcitc.com",
        "subject": "测试邮件",
        "body": "这是一封测试邮件。"
    },
    "execution_strategy": "direct",
    "reasoning": "任务需要发送邮件，识别到邮箱地址yubin.liu@pcitc.com，提取为to_emails参数。从'测试邮件'推断主题为'测试邮件'，使用默认正文。"
}""",
            "metadata": {"tool": "send_email", "category": "email"}
        },
        {
            "user": "给yubin.liu@pcitc.com发邮件，主题是会议通知，内容是明天下午3点开会",
            "assistant": """{
    "needs_tool": true,
    "selected_tool": "send_email",
    "optimized_parameters": {
        "to_emails": "yubin.liu@pcitc.com",
        "subject": "会议通知",
        "body": "明天下午3点开会"
    },
    "execution_strategy": "direct",
    "reasoning": "任务需要发送邮件，从'给XXX发'模式提取邮箱，从'主题是'提取主题，从'内容是'提取正文。"
}""",
            "metadata": {"tool": "send_email", "category": "email"}
        },
        {
            "user": "发送邮件给yubin.liu@pcitc.com，主题会议通知",
            "assistant": """{
    "needs_tool": true,
    "selected_tool": "send_email",
    "optimized_parameters": {
        "to_emails": "yubin.liu@pcitc.com",
        "subject": "会议通知",
        "body": "这是一封邮件。"
    },
    "execution_strategy": "direct",
    "reasoning": "任务需要发送邮件，查找包含'@'的字符串提取邮箱，从'主题'后提取主题，使用默认正文。"
}""",
            "metadata": {"tool": "send_email", "category": "email"}
        }
    ],
    "temperature": 0.3,
    "max_tokens": 2000,
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "is_active": True,
    "metadata": {
        "source": "mcp_tool_agent.py",
        "agent_type": "mcp_tool",
        "few_shot_enabled": True
    }
}


def get_database_url():
    """获取数据库连接URL"""
    db_url = os.getenv(
        'DATABASE_URL',
        os.getenv(
            'POSTGRES_URL',
            'postgresql://ai_user:ai_password@localhost:5432/ai_platform'
        )
    )
    return db_url


def migrate_prompt():
    """迁移提示词到数据库"""
    db_url = get_database_url()
    print(f"连接数据库: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 检查是否已存在
        existing = db.query(PromptTemplate).filter(
            PromptTemplate.name == MCP_TOOL_PROMPT["name"]
        ).first()
        
        if existing:
            print(f"提示词 '{MCP_TOOL_PROMPT['name']}' 已存在，跳过迁移")
            return
        
        # 创建提示词模板
        prompt = PromptTemplate(
            name=MCP_TOOL_PROMPT["name"],
            category=MCP_TOOL_PROMPT["category"],
            description=MCP_TOOL_PROMPT["description"],
            system_prompt=MCP_TOOL_PROMPT["system_prompt"],
            examples=MCP_TOOL_PROMPT["examples"],
            temperature=MCP_TOOL_PROMPT["temperature"],
            max_tokens=MCP_TOOL_PROMPT["max_tokens"],
            top_p=MCP_TOOL_PROMPT["top_p"],
            frequency_penalty=MCP_TOOL_PROMPT["frequency_penalty"],
            presence_penalty=MCP_TOOL_PROMPT["presence_penalty"],
            is_active=MCP_TOOL_PROMPT["is_active"],
            metadata=MCP_TOOL_PROMPT["metadata"],
            version=1,
            created_by="system"
        )
        
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        
        # 创建版本历史
        version = PromptTemplateVersion(
            template_id=prompt.id,
            version=1,
            system_prompt=prompt.system_prompt,
            examples=prompt.examples,
            temperature=prompt.temperature,
            max_tokens=prompt.max_tokens,
            change_reason="初始迁移版本",
            changed_by="system"
        )
        db.add(version)
        db.commit()
        
        print(f"✅ 成功迁移提示词 '{MCP_TOOL_PROMPT['name']}' 到数据库 (ID: {prompt.id})")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        engine.dispose()


if __name__ == '__main__':
    migrate_prompt()

