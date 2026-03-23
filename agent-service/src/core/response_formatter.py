"""
响应格式化器
将智能体的响应格式化为用户友好的格式
"""
import json
import re
from typing import Dict, Any, Optional


class ResponseFormatter:
    """响应格式化器"""
    
    @staticmethod
    def format_agent_response(result: Dict[str, Any]) -> str:
        """
        格式化智能体响应为易读的文本格式
        
        Args:
            result: 智能体执行结果
            
        Returns:
            格式化后的响应文本
        """
        # 如果是简单的计算问题，直接提取结果
        if result.get("agent_type") == "mcp_tool" and result.get("decision") == "no_tool_needed":
            reason = result.get("reason", "")
            
            # 尝试从 reason 中提取计算结果
            # 例如："可以直接计算得出结果40238"
            calculation_match = re.search(r'结果[：:]\s*(\d+)', reason)
            if calculation_match:
                return f"**计算结果：{calculation_match.group(1)}**\n\n计算过程：\n{reason}"
            
            # 如果是简单的数学表达式，尝试计算
            math_expr_match = re.search(r'(\d+(?:\s*[+\-*/]\s*\d+)+)', reason)
            if math_expr_match:
                try:
                    expr = math_expr_match.group(1).replace(' ', '')
                    result_value = eval(expr)
                    return f"**计算结果：{result_value}**\n\n计算表达式：{expr}"
                except:
                    pass
            
            # 简化显示，只显示关键信息
            return ResponseFormatter._format_simple_response(result)
        
        # 如果有 output 字段，优先使用
        if "output" in result and result["output"]:
            return str(result["output"])
        
        # 如果有 response 字段
        if "response" in result and result["response"]:
            return str(result["response"])
        
        # 如果有 final_response 字段
        if "final_response" in result and result["final_response"]:
            return str(result["final_response"])
        
        # 如果有 processed_result
        if "processed_result" in result:
            processed = result["processed_result"]
            if isinstance(processed, dict):
                summary = processed.get("summary", "")
                if summary:
                    return summary
                # 尝试格式化整个 processed_result
                return ResponseFormatter._format_dict_response(processed)
        
        # 如果有 raw_result
        if "raw_result" in result:
            raw = result["raw_result"]
            if isinstance(raw, dict):
                return ResponseFormatter._format_dict_response(raw)
            return str(raw)
        
        # 默认格式化整个结果
        return ResponseFormatter._format_dict_response(result)
    
    @staticmethod
    def _format_simple_response(result: Dict[str, Any]) -> str:
        """格式化简单响应"""
        lines = []
        
        # 提取关键信息
        decision = result.get("decision")
        reason = result.get("reason", "")
        error = result.get("error")
        
        if decision == "no_tool_needed":
            # 简化显示，提取关键信息
            if reason:
                # 尝试提取计算结果
                calc_match = re.search(r'(\d+(?:\s*[+\-*/]\s*\d+)+)\s*[=等于]\s*(\d+)', reason)
                if calc_match:
                    expr = calc_match.group(1)
                    result_val = calc_match.group(2)
                    return f"**计算结果：{result_val}**\n\n计算表达式：{expr.replace(' ', '')}"
                
                # 提取数字结果
                num_match = re.search(r'结果[：:]\s*(\d+)', reason)
                if num_match:
                    return f"**计算结果：{num_match.group(1)}**"
                
                # 简化 reason 显示
                simplified = reason.split('\n')[0] if '\n' in reason else reason
                if len(simplified) > 200:
                    simplified = simplified[:200] + "..."
                return simplified
        
        if error:
            return f"❌ 错误：{error}"
        
        # 默认返回 JSON（格式化）
        return ResponseFormatter._format_dict_response(result)
    
    @staticmethod
    def _format_dict_response(data: Dict[str, Any], indent: int = 0) -> str:
        """格式化字典响应为易读格式"""
        lines = []
        max_indent = 2  # 最多显示2层嵌套
        
        def format_value(key: str, value: Any, level: int = 0):
            if level > max_indent:
                return f"{'  ' * level}{key}: {str(value)[:100]}..."
            
            if isinstance(value, dict):
                if not value:  # 空字典
                    return f"{'  ' * level}{key}: {{}}"
                
                # 如果是简单的键值对，单行显示
                if len(value) <= 3 and all(not isinstance(v, (dict, list)) for v in value.values()):
                    items = ', '.join(f"{k}: {v}" for k, v in value.items())
                    return f"{'  ' * level}{key}: {{{items}}}"
                
                # 多行显示
                lines.append(f"{'  ' * level}{key}:")
                for k, v in value.items():
                    format_value(k, v, level + 1)
            elif isinstance(value, list):
                if not value:  # 空列表
                    return f"{'  ' * level}{key}: []"
                
                # 如果列表很短，单行显示
                if len(value) <= 3:
                    items = ', '.join(str(v) for v in value)
                    return f"{'  ' * level}{key}: [{items}]"
                
                # 多行显示
                lines.append(f"{'  ' * level}{key}:")
                for i, item in enumerate(value[:5]):  # 最多显示5项
                    if isinstance(item, dict):
                        lines.append(f"{'  ' * (level + 1)}[{i}]:")
                        for k, v in item.items():
                            format_value(k, v, level + 2)
                    else:
                        lines.append(f"{'  ' * (level + 1)}[{i}]: {item}")
                if len(value) > 5:
                    lines.append(f"{'  ' * (level + 1)}... (还有 {len(value) - 5} 项)")
            else:
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                lines.append(f"{'  ' * level}{key}: {value_str}")
        
        for key, value in data.items():
            format_value(key, value)
        
        return '\n'.join(lines) if lines else json.dumps(data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def format_for_display(result: Dict[str, Any]) -> str:
        """
        格式化响应用于前端显示
        
        Args:
            result: 智能体执行结果
            
        Returns:
            格式化后的 Markdown 格式文本
        """
        formatted = ResponseFormatter.format_agent_response(result)
        
        # 如果是纯文本，直接返回
        if not formatted.startswith('{') and not formatted.startswith('['):
            return formatted
        
        # 如果是 JSON，尝试美化
        try:
            data = json.loads(formatted)
            return ResponseFormatter._format_dict_response(data)
        except:
            return formatted

