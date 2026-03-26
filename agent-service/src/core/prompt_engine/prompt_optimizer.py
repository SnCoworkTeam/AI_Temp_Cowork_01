"""
提示词优化器
"""
import re
import logging
from typing import List, Dict, Any
from datetime import datetime

from ...models.prompt_models import (
    PromptTemplateConfig, PromptContext, OptimizedPrompt, PromptExample
)

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """提示词优化器 - 优化和增强提示词"""
    
    async def optimize_prompt(
        self,
        template: PromptTemplateConfig,
        user_input: str,
        context: PromptContext
    ) -> OptimizedPrompt:
        """
        优化提示词
        
        Args:
            template: 基础模板
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            优化后的提示词
        """
        # 1. 处理系统提示词中的占位符
        system_prompt = await self._process_system_prompt(
            template.system_prompt, context
        )
        
        # 2. 构建消息列表
        messages = await self._build_messages(
            system_prompt, user_input, template.examples, context
        )
        
        # 3. 调整生成参数
        generation_params = await self._adjust_generation_params(template, context)
        
        return OptimizedPrompt(
            messages=messages,
            temperature=generation_params['temperature'],
            max_tokens=generation_params['max_tokens'],
            template_name=template.name,
            metadata={
                "optimized_at": datetime.now().isoformat(),
                "context_used": bool(context.conversation_history),
                "examples_count": len(template.examples),
                "messages_count": len(messages)
            }
        )
    
    async def _process_system_prompt(
        self, 
        system_prompt: str, 
        context: PromptContext
    ) -> str:
        """处理系统提示词中的动态占位符"""
        processed_prompt = system_prompt
        
        # 替换用户信息
        if context.user_profile:
            user_name = context.user_profile.get('name', '用户')
            processed_prompt = processed_prompt.replace('{{user_name}}', user_name)
            user_role = context.user_profile.get('role', '')
            if user_role:
                processed_prompt = processed_prompt.replace('{{user_role}}', user_role)
        
        # 替换当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        processed_prompt = processed_prompt.replace('{{current_time}}', current_time)
        current_date = datetime.now().strftime('%Y-%m-%d')
        processed_prompt = processed_prompt.replace('{{current_date}}', current_date)
        
        # 替换可用工具
        if context.available_tools:
            tools_list = ', '.join(context.available_tools[:10])  # 最多显示10个
            processed_prompt = processed_prompt.replace('{{available_tools}}', tools_list)
            tools_count = len(context.available_tools)
            processed_prompt = processed_prompt.replace('{{tools_count}}', str(tools_count))
        
        # 替换会话ID
        if context.session_id:
            processed_prompt = processed_prompt.replace('{{session_id}}', context.session_id)
        
        # 清理未替换的占位符
        processed_prompt = re.sub(r'\{\{[^}]+\}\}', '', processed_prompt)
        
        return processed_prompt
    
    async def _build_messages(
        self,
        system_prompt: str,
        user_input: str,
        examples: List[PromptExample],
        context: PromptContext
    ) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []
        
        # 1. 添加系统提示词
        messages.append({"role": "system", "content": system_prompt})
        
        # 2. 添加对话历史（如果有）
        if context.conversation_history:
            # 只取最近3轮对话，避免过长
            recent_history = context.conversation_history[-6:]  # 3轮对话（6条消息）
            messages.extend(recent_history)
        
        # 3. 添加示例（few-shot learning）
        for example in examples[:2]:  # 最多2个示例
            messages.extend([
                {"role": "user", "content": example.user},
                {"role": "assistant", "content": example.assistant}
            ])
        
        # 4. 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    async def _adjust_generation_params(
        self, 
        template: PromptTemplateConfig, 
        context: PromptContext
    ) -> Dict[str, Any]:
        """根据上下文调整生成参数"""
        params = {
            'temperature': template.temperature,
            'max_tokens': template.max_tokens,
            'top_p': template.top_p
        }
        
        # 根据对话历史调整温度
        if context.conversation_history:
            # 有历史对话时，稍微提高创造性
            params['temperature'] = min(template.temperature + 0.1, 1.0)
        
        # 根据任务复杂度调整max_tokens
        if context.task_context:
            complexity = context.task_context.get('complexity', 'medium')
            if complexity == 'high':
                params['max_tokens'] = min(template.max_tokens + 1000, 4000)
            elif complexity == 'low':
                params['max_tokens'] = max(template.max_tokens - 500, 500)
        
        return params





































