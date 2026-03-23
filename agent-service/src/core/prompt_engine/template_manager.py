"""
模板管理器
"""
import os
import yaml
import logging
from typing import Dict, Optional
from pathlib import Path

from ...models.prompt_models import TaskCategory, PromptTemplateConfig, PromptExample

logger = logging.getLogger(__name__)

# 延迟导入数据库相关模块，避免循环依赖
_db_session = None


class TemplateManager:
    """模板管理器 - 管理提示词模板的加载和访问"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.templates: Dict[TaskCategory, PromptTemplateConfig] = {}
        self.config_path = config_path or self._get_default_config_path()
        self._load_templates()
    
    def get_template(self, task_category: TaskCategory) -> Optional[PromptTemplateConfig]:
        """获取指定任务类别的模板"""
        return self.templates.get(task_category)
    
    def get_template_by_name(self, template_name: str) -> Optional[PromptTemplateConfig]:
        """通过名称获取模板（支持字符串名称，不限于TaskCategory枚举）"""
        # 首先尝试作为TaskCategory枚举
        try:
            category = TaskCategory(template_name)
            return self.templates.get(category)
        except ValueError:
            # 如果不是枚举值，从YAML中查找
            return self._get_template_from_yaml_by_name(template_name)
    
    def _get_template_from_yaml_by_name(self, template_name: str) -> Optional[PromptTemplateConfig]:
        """从YAML文件中通过名称获取模板"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data or 'prompt_templates' not in config_data:
                return None
            
            templates_data = config_data.get('prompt_templates', {})
            template_data = templates_data.get(template_name)
            
            if not template_data:
                return None
            
            # 解析示例
            examples = []
            for ex_data in template_data.get('examples', []):
                examples.append(PromptExample(
                    user=ex_data.get('user', ''),
                    assistant=ex_data.get('assistant', ''),
                    metadata=ex_data.get('metadata', {})
                ))
            
            return PromptTemplateConfig(
                name=template_data.get('name', template_name),
                description=template_data.get('description', ''),
                system_prompt=template_data.get('system_prompt', ''),
                examples=examples,
                temperature=template_data.get('temperature', 0.3),
                max_tokens=template_data.get('max_tokens', 2000),
                top_p=template_data.get('top_p', 0.9),
                frequency_penalty=template_data.get('frequency_penalty', 0.0),
                presence_penalty=template_data.get('presence_penalty', 0.0),
                stop_sequences=template_data.get('stop_sequences', []),
                output_format=template_data.get('output_format'),
                dynamic_placeholders=template_data.get('dynamic_placeholders', [])
            )
        except Exception as e:
            logger.error(f"Failed to get template by name {template_name}: {e}")
            return None
    
    def get_all_templates(self) -> Dict[TaskCategory, PromptTemplateConfig]:
        """获取所有模板"""
        return self.templates.copy()
    
    def reload_templates(self):
        """重新加载模板"""
        logger.info("Reloading prompt templates...")
        self._load_templates()
        logger.info(f"Reloaded {len(self.templates)} templates")
    
    def _load_templates(self):
        """加载模板配置"""
        try:
            # 首先加载代码中定义的模板（作为基础）
            code_templates = self._load_code_templates()
            
            # 然后加载YAML配置文件（覆盖代码模板）
            yaml_templates = self._load_yaml_templates()
            
            # 然后加载数据库中的模板（覆盖YAML和代码模板）
            db_templates = self._load_database_templates()
            
            # 合并模板，优先级：数据库 > YAML > 代码
            self.templates = {**code_templates, **yaml_templates, **db_templates}
            
            logger.info(f"Loaded {len(self.templates)} prompt templates "
                       f"({len(code_templates)} from code, {len(yaml_templates)} from YAML, {len(db_templates)} from database)")
            
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {e}", exc_info=True)
            # 使用代码中定义的基础模板作为后备
            self.templates = self._load_code_templates()
            logger.warning("Using code templates only as fallback")
    
    def _load_yaml_templates(self) -> Dict[TaskCategory, PromptTemplateConfig]:
        """从YAML文件加载模板"""
        yaml_templates = {}
        
        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.debug(f"Prompt config file not found: {self.config_path}, using code templates only")
            return yaml_templates
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data or 'prompt_templates' not in config_data:
                logger.warning("YAML config file exists but has no 'prompt_templates' section")
                return yaml_templates
            
            templates_data = config_data.get('prompt_templates', {})
            
            for category_name, template_data in templates_data.items():
                try:
                    category = TaskCategory(category_name)
                    
                    # 解析示例
                    examples = []
                    for ex_data in template_data.get('examples', []):
                        examples.append(PromptExample(
                            user=ex_data.get('user', ''),
                            assistant=ex_data.get('assistant', ''),
                            metadata=ex_data.get('metadata', {})
                        ))
                    
                    template_config = PromptTemplateConfig(
                        name=template_data.get('name', category_name),
                        description=template_data.get('description', ''),
                        system_prompt=template_data.get('system_prompt', ''),
                        examples=examples,
                        temperature=template_data.get('temperature', 0.3),
                        max_tokens=template_data.get('max_tokens', 2000),
                        top_p=template_data.get('top_p', 0.9),
                        frequency_penalty=template_data.get('frequency_penalty', 0.0),
                        presence_penalty=template_data.get('presence_penalty', 0.0),
                        stop_sequences=template_data.get('stop_sequences', []),
                        output_format=template_data.get('output_format'),
                        dynamic_placeholders=template_data.get('dynamic_placeholders', [])
                    )
                    yaml_templates[category] = template_config
                    
                    logger.debug(f"Loaded template for {category_name} from YAML")
                    
                except ValueError:
                    logger.warning(f"Unknown task category in YAML: {category_name}, skipping")
                except Exception as e:
                    logger.error(f"Failed to load template for {category_name}: {e}")
            
            logger.info(f"Loaded {len(yaml_templates)} templates from YAML config")
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config: {e}")
        except Exception as e:
            logger.error(f"Failed to load YAML config: {e}", exc_info=True)
        
        return yaml_templates
    
    def _load_code_templates(self) -> Dict[TaskCategory, PromptTemplateConfig]:
        """加载代码中定义的基础模板"""
        try:
            from ..prompt_templates.base_templates import BASE_TEMPLATES
            logger.debug(f"Loaded {len(BASE_TEMPLATES)} templates from code")
            return BASE_TEMPLATES
        except ImportError as e:
            logger.error(f"Failed to import BASE_TEMPLATES: {e}")
            return {}
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 尝试多个可能的路径
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / 'config' / 'prompt_templates.yaml',
            Path('/app/config/prompt_templates.yaml'),  # Docker环境
            Path('./config/prompt_templates.yaml'),  # 相对路径
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Using prompt config file: {path}")
                return str(path)
        
        # 如果都不存在，返回第一个作为默认路径
        default_path = possible_paths[0]
        logger.info(f"Prompt config file not found, will use default path: {default_path}")
        return str(default_path)
    
    def _load_database_templates(self) -> Dict[TaskCategory, PromptTemplateConfig]:
        """从数据库加载模板"""
        db_templates = {}
        
        try:
            # 尝试导入数据库相关模块
            from ...core.database import get_db
            from database.src.models.prompt_template import PromptTemplate
            from sqlalchemy.orm import Session
            
            # 获取数据库会话
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # 查询所有激活的提示词模板
                prompts = db.query(PromptTemplate).filter(
                    PromptTemplate.is_active == True
                ).all()
                
                for prompt in prompts:
                    try:
                        # 尝试将category转换为TaskCategory枚举
                        category = TaskCategory(prompt.category)
                        
                        # 转换examples
                        examples = []
                        if prompt.examples:
                            if isinstance(prompt.examples, list):
                                for ex in prompt.examples:
                                    if isinstance(ex, dict):
                                        examples.append(PromptExample(
                                            user=ex.get('user', ''),
                                            assistant=ex.get('assistant', ''),
                                            metadata=ex.get('metadata', {})
                                        ))
                        
                        template_config = PromptTemplateConfig(
                            name=prompt.name,
                            description=prompt.description or '',
                            system_prompt=prompt.system_prompt or '',
                            examples=examples,
                            temperature=prompt.temperature or 0.3,
                            max_tokens=prompt.max_tokens or 2000,
                            top_p=prompt.top_p or 0.9,
                            frequency_penalty=prompt.frequency_penalty or 0.0,
                            presence_penalty=prompt.presence_penalty or 0.0,
                            stop_sequences=prompt.stop_sequences or [],
                            output_format=prompt.output_format,
                            dynamic_placeholders=prompt.dynamic_placeholders or []
                        )
                        
                        db_templates[category] = template_config
                        logger.debug(f"Loaded template '{prompt.name}' from database for category {category.value}")
                        
                    except ValueError:
                        # category不是有效的TaskCategory，跳过
                        logger.warning(f"Unknown task category '{prompt.category}' for prompt '{prompt.name}', skipping")
                    except Exception as e:
                        logger.error(f"Failed to load template '{prompt.name}' from database: {e}")
                
                logger.info(f"Loaded {len(db_templates)} templates from database")
                
            finally:
                db.close()
                
        except ImportError:
            logger.debug("Database modules not available, skipping database template loading")
        except Exception as e:
            logger.warning(f"Failed to load templates from database: {e}")
        
        return db_templates
























