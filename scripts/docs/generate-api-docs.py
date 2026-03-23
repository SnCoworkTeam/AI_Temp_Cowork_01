#!/usr/bin/env python3
"""
API文档生成脚本
从FastAPI应用自动生成OpenAPI规范和Postman集合
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def get_openapi_spec(service_name: str) -> Dict[str, Any]:
    """获取服务的OpenAPI规范"""
    try:
        if service_name == "mcp-gateway":
            from mcp_gateway.src.main import app as mcp_app
            return mcp_app.openapi()
        elif service_name == "workflow-engine":
            from workflow_engine.src.main import app as workflow_app
            return workflow_app.openapi()
        elif service_name == "auth-service":
            from auth_service.src.main import app as auth_app
            return auth_app.openapi()
        elif service_name == "knowledge-base":
            from knowledge_base.src.main import app as kb_app
            return kb_app.openapi()
    except Exception as e:
        print(f"警告: 无法获取 {service_name} 的OpenAPI规范: {e}")
        return None
    return None


def generate_openapi_spec(service_name: str, output_dir: Path):
    """生成OpenAPI规范文件"""
    print(f"生成 {service_name} 的OpenAPI规范...")
    
    spec = get_openapi_spec(service_name)
    if not spec:
        print(f"  跳过 {service_name}（服务未配置）")
        return
    
    # 保存JSON格式
    json_file = output_dir / f"{service_name}-openapi.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    # 保存YAML格式（如果可用）
    try:
        import yaml
        yaml_file = output_dir / f"{service_name}-openapi.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(spec, f, default_flow_style=False, allow_unicode=True)
    except ImportError:
        print("  提示: 安装pyyaml以生成YAML格式")
    
    print(f"  ✅ OpenAPI规范已保存: {json_file}")


def generate_postman_collection(service_name: str, openapi_spec: Dict[str, Any], output_dir: Path):
    """从OpenAPI规范生成Postman集合"""
    print(f"生成 {service_name} 的Postman集合...")
    
    if not openapi_spec:
        return
    
    collection = {
        "info": {
            "name": f"{service_name} API",
            "description": openapi_spec.get("info", {}).get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }
    
    # 转换OpenAPI路径到Postman请求
    paths = openapi_spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                request = {
                    "name": details.get("summary", f"{method.upper()} {path}"),
                    "request": {
                        "method": method.upper(),
                        "header": [],
                        "url": {
                            "raw": f"{{{{base_url}}}}{path}",
                            "host": ["{{base_url}}"],
                            "path": path.split("/")
                        }
                    },
                    "response": []
                }
                
                # 添加参数
                parameters = details.get("parameters", [])
                if parameters:
                    request["request"]["url"]["query"] = []
                    for param in parameters:
                        if param.get("in") == "query":
                            request["request"]["url"]["query"].append({
                                "key": param.get("name"),
                                "value": "",
                                "description": param.get("description", "")
                            })
                
                # 添加请求体
                request_body = details.get("requestBody", {})
                if request_body:
                    content = request_body.get("content", {})
                    if "application/json" in content:
                        request["request"]["body"] = {
                            "mode": "raw",
                            "raw": "{}",
                            "options": {
                                "raw": {
                                    "language": "json"
                                }
                            }
                        }
                
                collection["item"].append(request)
    
    # 保存Postman集合
    collection_file = output_dir / f"{service_name}-postman.json"
    with open(collection_file, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Postman集合已保存: {collection_file}")


def generate_all_api_docs():
    """生成所有服务的API文档"""
    print("开始生成API文档...")
    
    docs_dir = project_root / "docs"
    api_docs_dir = docs_dir / "api-docs"
    openapi_dir = api_docs_dir / "openapi"
    postman_dir = api_docs_dir / "postman"
    
    # 创建目录
    openapi_dir.mkdir(parents=True, exist_ok=True)
    postman_dir.mkdir(parents=True, exist_ok=True)
    
    services = [
        "mcp-gateway",
        "workflow-engine",
        "auth-service",
        "knowledge-base"
    ]
    
    for service in services:
        print(f"\n处理服务: {service}")
        
        # 生成OpenAPI规范
        spec = get_openapi_spec(service)
        if spec:
            generate_openapi_spec(service, openapi_dir)
            generate_postman_collection(service, spec, postman_dir)
        else:
            print(f"  跳过 {service}（无法获取OpenAPI规范）")
    
    print("\n✅ API文档生成完成")


if __name__ == "__main__":
    generate_all_api_docs()









