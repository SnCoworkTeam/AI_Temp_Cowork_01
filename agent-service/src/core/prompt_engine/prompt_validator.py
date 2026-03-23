"""
提示词验证器
"""
import logging
from typing import List
from ...models.prompt_models import OptimizedPrompt, PromptValidationResult

logger = logging.getLogger(__name__)


class PromptValidator:
    """提示词验证器 - 验证提示词的质量和有效性"""
    
    async def validate_prompt(self, prompt: OptimizedPrompt) -> PromptValidationResult:
        """
        验证提示词
        
        Args:
            prompt: 待验证的提示词
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        suggestions = []
        
        # 1. 验证消息列表
        if not prompt.messages or len(prompt.messages) == 0:
            errors.append("Messages list is empty")
        
        # 2. 验证系统提示词存在
        has_system = any(msg.get("role") == "system" for msg in prompt.messages)
        if not has_system:
            warnings.append("No system prompt found, may affect response quality")
        
        # 3. 验证用户输入存在
        has_user = any(msg.get("role") == "user" for msg in prompt.messages)
        if not has_user:
            errors.append("No user message found")
        
        # 4. 验证消息格式
        for i, msg in enumerate(prompt.messages):
            if "role" not in msg:
                errors.append(f"Message {i} missing 'role' field")
            if "content" not in msg:
                errors.append(f"Message {i} missing 'content' field")
            if msg.get("role") not in ["system", "user", "assistant"]:
                errors.append(f"Message {i} has invalid role: {msg.get('role')}")
        
        # 5. 验证参数范围
        if prompt.temperature < 0 or prompt.temperature > 2:
            errors.append(f"Temperature {prompt.temperature} is out of valid range [0, 2]")
        
        if prompt.max_tokens < 100 or prompt.max_tokens > 8000:
            warnings.append(f"Max tokens {prompt.max_tokens} may be outside optimal range")
        
        # 6. 检查消息长度
        total_length = sum(len(str(msg.get("content", ""))) for msg in prompt.messages)
        if total_length > 100000:  # 约100K字符
            warnings.append("Total prompt length is very long, may cause performance issues")
            suggestions.append("Consider reducing conversation history or prompt length")
        
        # 7. 检查是否有足够的上下文
        if len(prompt.messages) < 2:
            warnings.append("Prompt has very few messages, may lack context")
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.warning(f"Prompt validation failed with {len(errors)} errors: {errors}")
        elif warnings:
            logger.info(f"Prompt validation passed with {len(warnings)} warnings")
        
        return PromptValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )





































