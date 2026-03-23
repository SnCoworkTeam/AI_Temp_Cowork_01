"""
提示词引擎核心
"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...models.prompt_models import (
    TaskCategory, PromptTemplateConfig, PromptContext, 
    OptimizedPrompt, PromptExample
)
from .template_manager import TemplateManager
from .prompt_optimizer import PromptOptimizer
from .prompt_validator import PromptValidator

logger = logging.getLogger(__name__)


class PromptEngine:
    """智能提示词引擎 - 嵌入在Agent服务中"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化提示词引擎
        
        Args:
            config_path: 提示词配置文件路径（可选）
        """
        self.template_manager = TemplateManager(config_path)
        self.prompt_optimizer = PromptOptimizer()
        self.prompt_validator = PromptValidator()
        self.cache: Dict[str, OptimizedPrompt] = {}
        self.cache_max_size = 1000
        
        logger.info("PromptEngine initialized successfully")
    
    async def get_optimized_prompt(
        self,
        task_category: TaskCategory,
        user_input: str,
        context: PromptContext,
        use_cache: bool = True
    ) -> OptimizedPrompt:
        """
        获取优化后的提示词
        
        Args:
            task_category: 任务分类
            user_input: 用户输入
            context: 提示词上下文
            use_cache: 是否使用缓存
            
        Returns:
            优化后的提示词配置
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(task_category, user_input, context)
        
        # 检查缓存
        if use_cache and cache_key in self.cache:
            logger.debug(f"Using cached prompt for {task_category.value}")
            return self.cache[cache_key]
        
        # 获取基础模板
        base_template = self.template_manager.get_template(task_category)
        if not base_template:
            logger.warning(f"No template found for task category: {task_category}, using fallback")
            return await self._get_fallback_prompt(task_category, user_input)
        
        # 优化提示词
        try:
            optimized_prompt = await self.prompt_optimizer.optimize_prompt(
                base_template, user_input, context
            )
        except Exception as e:
            logger.error(f"Failed to optimize prompt: {e}", exc_info=True)
            return await self._get_fallback_prompt(task_category, user_input)
        
        # 验证提示词
        validation_result = await self.prompt_validator.validate_prompt(optimized_prompt)
        if not validation_result.is_valid:
            logger.warning(f"Prompt validation failed: {validation_result.errors}")
            # 使用降级策略
            optimized_prompt = await self._get_fallback_prompt(task_category, user_input)
        elif validation_result.warnings:
            logger.debug(f"Prompt validation warnings: {validation_result.warnings}")
        
        # 缓存结果
        if use_cache:
            self.cache[cache_key] = optimized_prompt
            # 限制缓存大小
            if len(self.cache) > self.cache_max_size:
                self._clean_cache()
        
        logger.info(f"Generated optimized prompt for {task_category.value}, "
                   f"messages: {len(optimized_prompt.messages)}, "
                   f"template: {optimized_prompt.template_name}")
        
        return optimized_prompt
    
    async def batch_optimize_prompts(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Optional[OptimizedPrompt]]:
        """批量优化提示词"""
        results = {}
        
        for task in tasks:
            try:
                task_category = TaskCategory(task['category'])
                user_input = task['input']
                context_data = task.get('context', {})
                context = PromptContext(**context_data)
                
                optimized_prompt = await self.get_optimized_prompt(
                    task_category, user_input, context
                )
                results[task['id']] = optimized_prompt
                
            except Exception as e:
                logger.error(f"Failed to optimize prompt for task {task.get('id')}: {e}")
                results[task['id']] = None
        
        return results
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("Prompt cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "cache_size": len(self.cache),
            "cache_max_size": self.cache_max_size,
            "cache_keys": list(self.cache.keys())[:10]  # 只显示前10个键
        }
    
    def reload_templates(self):
        """重新加载模板"""
        self.template_manager.reload_templates()
        # 清空缓存，因为模板已更新
        self.clear_cache()
        logger.info("Templates reloaded and cache cleared")
    
    def _generate_cache_key(
        self, 
        task_category: TaskCategory, 
        user_input: str, 
        context: PromptContext
    ) -> str:
        """生成缓存键"""
        # 使用任务类别和用户输入的前100字符生成键
        key_data = {
            "category": task_category.value,
            "input_hash": hash(user_input[:100]),  # 只哈希前100字符
            "user_id": context.user_id or "anonymous",
            "session_id": context.session_id or "no_session"
        }
        return json.dumps(key_data, sort_keys=True)
    
    def _clean_cache(self):
        """清理缓存，保留最近使用的"""
        if len(self.cache) > self.cache_max_size:
            # 简单的LRU策略：删除前200个
            keys_to_remove = list(self.cache.keys())[:200]
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(f"Cleaned prompt cache, removed {len(keys_to_remove)} items, "
                       f"remaining: {len(self.cache)}")
    
    async def _get_fallback_prompt(
        self, 
        task_category: TaskCategory, 
        user_input: str
    ) -> OptimizedPrompt:
        """获取降级提示词"""
        # 尝试使用直接对话模板作为降级
        fallback_template = self.template_manager.get_template(TaskCategory.DIRECT_CHAT)
        
        if not fallback_template:
            # 如果连降级模板都没有，使用最基本的提示词
            messages = [
                {"role": "system", "content": "你是一个有用的AI助手。"},
                {"role": "user", "content": user_input}
            ]
            return OptimizedPrompt(
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                template_name="minimal_fallback",
                metadata={"is_fallback": True, "original_category": task_category.value}
            )
        
        # 使用直接对话模板
        messages = [
            {"role": "system", "content": fallback_template.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        return OptimizedPrompt(
            messages=messages,
            temperature=fallback_template.temperature,
            max_tokens=fallback_template.max_tokens,
            template_name="fallback_direct_chat",
            metadata={"is_fallback": True, "original_category": task_category.value}
        )





































