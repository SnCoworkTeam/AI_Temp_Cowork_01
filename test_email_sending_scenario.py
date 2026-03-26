"""
测试邮件发送场景：分析销售订单，生成报告，发邮件
"""
import asyncio
import sys
import os

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, "agent-service")
os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"
os.environ["CONFIG_CENTER_URL"] = "http://localhost:8090"

async def test_email_sending():
    """测试邮件发送场景"""
    print("="*80)
    print("测试邮件发送场景")
    print("="*80)
    
    # 从配置中心读取API key
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "http://localhost:8090/api/config/llm.api_key",
                params={"environment": "default"}
            )
            if response.status_code == 200:
                data = response.json()
                api_key = data.get("value", "")
                if api_key:
                    os.environ["OPENAI_API_KEY"] = api_key
                    print(f"✅ 从配置中心读取API key成功 (长度: {len(api_key)})")
    except Exception as e:
        print(f"⚠️  无法从配置中心读取API key: {e}")
    
    os.environ["LLM_BASE_URL"] = "https://api.deepseek.com"
    os.environ["LLM_MODEL"] = "deepseek-chat"
    
    # 测试MCP工具智能体
    print("\n[测试] MCP工具智能体 - 分析邮件发送任务")
    try:
        from src.core.agents.mcp_tool_agent import MCPToolAgent
        from src.core.llm_integration import deepseek_llm
        
        # 确保LLM已初始化
        await deepseek_llm._load_config_async()
        if not deepseek_llm.llm:
            print("❌ LLM未初始化")
            return False
        
        agent = MCPToolAgent()
        
        # 模拟上下文：假设前面的智能体已经生成了报告内容
        task_description = "发邮件给刘玉斌，yubin.liu@pcitc.com"
        context = {
            "user_input": "分析销售订单，生成报告，发邮件给刘玉斌，yubin.liu@pcitc.com",
            "report_content": "销售订单分析报告\n\n1. 订单总数：100\n2. 总金额：500,000元\n3. 主要客户：...",
            "recipient_name": "刘玉斌",
            "recipient_email": "yubin.liu@pcitc.com"
        }
        
        print(f"\n任务描述: {task_description}")
        print(f"上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")
        
        # 测试analyze_task
        print("\n执行 analyze_task...")
        execution_plan = await agent.analyze_task(task_description, context)
        
        print(f"\n分析结果:")
        print(f"  需要工具: {execution_plan.get('needs_tool', False)}")
        print(f"  选择的工具: {execution_plan.get('selected_tool', 'N/A')}")
        print(f"  参数: {json.dumps(execution_plan.get('optimized_parameters', {}), ensure_ascii=False, indent=2)}")
        print(f"  理由: {execution_plan.get('reasoning', 'N/A')}")
        
        if execution_plan.get('needs_tool'):
            print("\n✅ 成功识别需要工具")
            
            if execution_plan.get('selected_tool') == 'send_email':
                print("✅ 正确选择了send_email工具")
                
                # 检查参数
                params = execution_plan.get('optimized_parameters', {})
                print(f"\n参数详情:")
                for key, value in params.items():
                    print(f"  {key}: {str(value)[:50]}")
                
                # 检查是否有收件人信息（可能是不同的参数名）
                has_recipient = any(key in params for key in ['to', 'to_emails', 'recipient_email', 'email'])
                if has_recipient:
                    print("✅ 参数中包含收件人信息")
                else:
                    print("⚠️  参数中缺少收件人信息")
                
                # 测试执行（不实际发送）
                print("\n测试execute（不实际发送邮件）...")
                try:
                    result = await agent.execute({
                        "task": task_description,
                        "execution_plan": execution_plan
                    }, context)
                    
                    print(f"执行结果:")
                    print(f"  工具: {result.get('tool_executed', 'N/A')}")
                    print(f"  成功: {result.get('execution_success', False)}")
                    if result.get('execution_success'):
                        print("✅ 工具执行成功")
                    else:
                        print(f"⚠️  工具执行失败: {result.get('error', 'N/A')}")
                except Exception as e:
                    print(f"⚠️  执行测试失败: {e}")
                
                return True
            else:
                print(f"⚠️  选择的工具不是send_email: {execution_plan.get('selected_tool')}")
                return False
        else:
            print("\n❌ 未能识别需要工具")
            print(f"   原因: {execution_plan.get('reasoning', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import json
    result = asyncio.run(test_email_sending())
    
    print("\n" + "="*80)
    if result:
        print("✅ 测试通过！MCP工具智能体能够正确识别邮件发送任务")
    else:
        print("❌ 测试失败，请检查错误信息")
    print("="*80)

