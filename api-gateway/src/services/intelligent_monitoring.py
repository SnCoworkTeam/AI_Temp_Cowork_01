"""
智能化监控服务
AI驱动的性能监控和优化建议
"""
import logging
import httpx
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class IntelligentMonitoringService:
    """智能化监控服务"""
    
    def __init__(self):
        """
        初始化智能化监控服务
        """
        self.llm_base_url = os.getenv("LLM_BASE_URL", "http://chat-service:8006")
        self.llm_api_key = os.getenv("OPENAI_API_KEY", "")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.enabled = os.getenv("INTELLIGENT_MONITORING_ENABLED", "true").lower() == "true"
    
    async def analyze_performance(
        self,
        metrics: Dict[str, Any],
        time_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        分析性能数据
        
        Args:
            metrics: 性能指标数据
            time_range: 时间范围
        
        Returns:
            性能分析结果
        """
        try:
            # 基础分析
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "metrics_summary": {},
                "anomalies": [],
                "recommendations": []
            }
            
            # 分析各项指标
            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, (list, dict)):
                    metric_analysis = self._analyze_metric(metric_name, metric_data)
                    analysis["metrics_summary"][metric_name] = metric_analysis
                    
                    # 检测异常
                    anomalies = self._detect_anomalies(metric_name, metric_data)
                    analysis["anomalies"].extend(anomalies)
            
            # 生成优化建议
            if self.enabled:
                recommendations = await self._generate_recommendations(analysis)
                analysis["recommendations"] = recommendations
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze performance: {e}", exc_info=True)
            return {
                "error": str(e)
            }
    
    def _analyze_metric(
        self,
        metric_name: str,
        metric_data: Any
    ) -> Dict[str, Any]:
        """分析单个指标"""
        summary = {
            "name": metric_name,
            "status": "normal"
        }
        
        if isinstance(metric_data, list):
            if len(metric_data) > 0:
                values = [item.get("value", 0) if isinstance(item, dict) else item for item in metric_data]
                summary["count"] = len(values)
                summary["min"] = min(values) if values else 0
                summary["max"] = max(values) if values else 0
                summary["avg"] = sum(values) / len(values) if values else 0
                
                # 判断状态
                if summary["avg"] > 1000:  # 示例阈值
                    summary["status"] = "warning"
                elif summary["avg"] > 5000:
                    summary["status"] = "critical"
        
        return summary
    
    def _detect_anomalies(
        self,
        metric_name: str,
        metric_data: Any
    ) -> List[Dict[str, Any]]:
        """检测异常"""
        anomalies = []
        
        if isinstance(metric_data, list):
            for i, item in enumerate(metric_data):
                value = item.get("value", 0) if isinstance(item, dict) else item
                timestamp = item.get("timestamp") if isinstance(item, dict) else None
                
                # 简单异常检测：值超过平均值3倍
                if i > 0:
                    prev_values = [d.get("value", 0) if isinstance(d, dict) else d for d in metric_data[:i]]
                    if prev_values:
                        avg = sum(prev_values) / len(prev_values)
                        if value > avg * 3:
                            anomalies.append({
                                "metric": metric_name,
                                "value": value,
                                "timestamp": timestamp,
                                "severity": "high" if value > avg * 5 else "medium",
                                "description": f"异常值检测：{value} 超过平均值 {avg:.2f} 的3倍"
                            })
        
        return anomalies
    
    async def _generate_recommendations(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成优化建议（LLM增强）"""
        if not self.enabled:
            return []
        
        try:
            prompt = f"""
分析以下性能数据，生成优化建议：

性能摘要:
{json.dumps(analysis.get("metrics_summary", {}), indent=2, ensure_ascii=False)}

异常检测:
{json.dumps(analysis.get("anomalies", []), indent=2, ensure_ascii=False)}

请生成3-5条优化建议，返回JSON格式：
{{
    "recommendations": [
        {{
            "type": "performance|scalability|reliability",
            "priority": "high|medium|low",
            "title": "建议标题",
            "description": "详细描述",
            "action": "具体操作建议"
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
                            "content": "你是一个系统性能优化专家。分析性能数据，生成实用的优化建议。"
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
                recommendations_data = json.loads(content)
                return recommendations_data.get("recommendations", [])
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}", exc_info=True)
            return []
    
    async def predict_issues(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_hours: int = 24
    ) -> Dict[str, Any]:
        """
        预测潜在问题
        
        Args:
            historical_data: 历史数据
            forecast_hours: 预测时间范围（小时）
        
        Returns:
            预测结果
        """
        try:
            # 简单预测：基于趋势分析
            predictions = {
                "forecast_hours": forecast_hours,
                "predictions": [],
                "confidence": 0.7
            }
            
            # 分析趋势
            if len(historical_data) > 10:
                recent_values = [d.get("value", 0) for d in historical_data[-10:]]
                trend = (recent_values[-1] - recent_values[0]) / len(recent_values)
                
                if trend > 0:
                    predictions["predictions"].append({
                        "type": "performance_degradation",
                        "severity": "medium",
                        "description": "检测到性能下降趋势",
                        "estimated_time": (datetime.now() + timedelta(hours=forecast_hours)).isoformat()
                    })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to predict issues: {e}", exc_info=True)
            return {
                "error": str(e)
            }
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()





