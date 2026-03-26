"""
智能数据质量检测服务
使用AI自动检测和修复数据质量问题
"""
import logging
import httpx
import os
import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..services.metadata_catalog import MetadataCatalogService

logger = logging.getLogger(__name__)


class IntelligentQualityService:
    """智能数据质量检测服务"""
    
    def __init__(self, db: Session):
        """
        初始化智能质量检测服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.catalog = MetadataCatalogService(db)
        self.llm_base_url = os.getenv("LLM_BASE_URL", "http://chat-service:8006")
        self.llm_api_key = os.getenv("OPENAI_API_KEY", "")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.enabled = os.getenv("INTELLIGENT_QUALITY_ENABLED", "true").lower() == "true"
    
    async def detect_quality_issues(
        self,
        entity_id: Optional[int] = None,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检测数据质量问题
        
        Args:
            entity_id: 实体ID（如果提供，只检测该实体）
            entity_type: 实体类型（如果提供，只检测该类型）
        
        Returns:
            质量问题列表
        """
        try:
            issues = []
            
            # 获取实体列表
            if entity_id:
                entity = self.catalog.get_business_entity(entity_id)
                entities = [entity] if entity else []
            else:
                entities = self.catalog.list_business_entities(limit=1000)
                if entity_type:
                    entities = [e for e in entities if e.entity_type == entity_type]
            
            # 检测问题
            for entity in entities:
                entity_issues = self._check_entity_quality(entity)
                issues.extend(entity_issues)
            
            # LLM增强的问题分析
            if self.enabled and issues:
                enhanced_issues = await self._enhance_issue_analysis(issues)
                return enhanced_issues
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to detect quality issues: {e}", exc_info=True)
            return []
    
    def _check_entity_quality(self, entity: Any) -> List[Dict[str, Any]]:
        """检查实体质量"""
        issues = []
        
        # 检查1: 缺少名称
        if not entity.name or not entity.name.strip():
            issues.append({
                "entity_id": entity.id,
                "type": "missing_name",
                "severity": "high",
                "description": "实体缺少名称",
                "suggestion": "为实体添加名称"
            })
        
        # 检查2: 缺少描述
        if not entity.description or not entity.description.strip():
            issues.append({
                "entity_id": entity.id,
                "type": "missing_description",
                "severity": "medium",
                "description": "实体缺少描述",
                "suggestion": "为实体添加描述，有助于理解和使用"
            })
        
        # 检查3: 名称过长或过短
        if entity.name:
            if len(entity.name) > 200:
                issues.append({
                    "entity_id": entity.id,
                    "type": "name_too_long",
                    "severity": "low",
                    "description": f"实体名称过长（{len(entity.name)}字符）",
                    "suggestion": "考虑缩短名称"
                })
            elif len(entity.name) < 2:
                issues.append({
                    "entity_id": entity.id,
                    "type": "name_too_short",
                    "severity": "medium",
                    "description": "实体名称过短",
                    "suggestion": "使用更具描述性的名称"
                })
        
        return issues
    
    async def _enhance_issue_analysis(
        self,
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """使用LLM增强问题分析"""
        if not self.enabled or not issues:
            return issues
        
        try:
            # 批量分析问题
            prompt = f"""
分析以下数据质量问题，为每个问题提供更详细的修复建议：

问题列表:
{json.dumps(issues[:10], indent=2, ensure_ascii=False)}

请为每个问题提供：
1. 更详细的问题分析
2. 具体的修复步骤
3. 预防措施

返回JSON格式：
{{
    "enhanced_issues": [
        {{
            "entity_id": 实体ID,
            "type": "问题类型",
            "detailed_analysis": "详细分析",
            "fix_steps": ["步骤1", "步骤2"],
            "prevention": "预防措施"
        }}
    ]
}}
"""
            
            response = await self.http_client.post(
                f"{self.llm_base_url}/api/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个数据质量专家。分析数据质量问题，提供详细的修复建议。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"}
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                enhanced_data = json.loads(content)
                enhanced_issues = enhanced_data.get("enhanced_issues", [])
                
                # 合并原始问题和增强分析
                for i, issue in enumerate(issues[:len(enhanced_issues)]):
                    enhanced = enhanced_issues[i]
                    issue.update({
                        "detailed_analysis": enhanced.get("detailed_analysis", ""),
                        "fix_steps": enhanced.get("fix_steps", []),
                        "prevention": enhanced.get("prevention", "")
                    })
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to enhance issue analysis: {e}", exc_info=True)
            return issues
    
    async def calculate_quality_score(
        self,
        entity_id: int
    ) -> Dict[str, Any]:
        """
        计算实体质量分数
        
        Args:
            entity_id: 实体ID
        
        Returns:
            质量分数和详情
        """
        try:
            entity = self.catalog.get_business_entity(entity_id)
            if not entity:
                return {
                    "entity_id": entity_id,
                    "error": "Entity not found"
                }
            
            score = 100.0
            deductions = []
            
            # 检查各项质量指标
            if not entity.name or not entity.name.strip():
                score -= 20
                deductions.append({"reason": "缺少名称", "deduction": 20})
            
            if not entity.description or not entity.description.strip():
                score -= 15
                deductions.append({"reason": "缺少描述", "deduction": 15})
            
            if not entity.display_name or not entity.display_name.strip():
                score -= 10
                deductions.append({"reason": "缺少显示名称", "deduction": 10})
            
            # 检查元数据完整性
            if hasattr(entity, 'metadata') and entity.metadata:
                metadata_keys = len(entity.metadata) if isinstance(entity.metadata, dict) else 0
                if metadata_keys < 3:
                    score -= 5
                    deductions.append({"reason": "元数据不完整", "deduction": 5})
            
            score = max(score, 0.0)
            
            return {
                "entity_id": entity_id,
                "quality_score": round(score, 2),
                "deductions": deductions,
                "grade": self._get_quality_grade(score)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {e}", exc_info=True)
            return {
                "entity_id": entity_id,
                "error": str(e)
            }
    
    def _get_quality_grade(self, score: float) -> str:
        """获取质量等级"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()




