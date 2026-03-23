"""
语义索引状态报告
"""
import requests
import json
from datetime import datetime

def get_summary():
    """获取状态摘要"""
    print("=" * 80)
    print("语义索引构建状态报告")
    print("=" * 80)
    print(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 服务状态
    print("1. 服务状态")
    print("-" * 80)
    services = {
        "SAP元数据代理": "http://localhost:8015",
        "知识库服务": "http://localhost:8004",
        "元数据服务": "http://localhost:8005"
    }
    
    for name, url in services.items():
        try:
            response = requests.get(f"{url}/api/health", timeout=5)
            status = "✓ 运行中" if response.status_code == 200 else f"✗ HTTP {response.status_code}"
        except:
            status = "✗ 未运行或无法访问"
        print(f"  {name}: {status}")
    
    # 2. 元数据统计
    print("\n2. 元数据统计")
    print("-" * 80)
    try:
        response = requests.get(
            "http://localhost:8005/api/data-assets",
            params={"limit": 10, "source_system": "SAP"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 0
            print(f"  SAP数据资产: 至少 {count} 个（实际可能有109,022个）")
        else:
            print(f"  ✗ 无法获取元数据统计")
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
    
    # 3. 知识库状态
    print("\n3. 知识库文档状态")
    print("-" * 80)
    try:
        response = requests.get(
            "http://localhost:8004/api/documents",
            params={"page": 1, "page_size": 100},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            documents = data.get("documents", [])
            
            # 统计SAP相关
            sap_count = 0
            sap_processed = 0
            sap_processing = 0
            sap_failed = 0
            
            for doc in documents:
                metadata = doc.get("metadata", {})
                category = doc.get("category", "")
                tags = doc.get("tags", [])
                
                is_sap = (
                    "sap" in category.lower() or
                    any("sap" in str(tag).lower() for tag in tags) or
                    "data_asset" in str(metadata.get("type", "")).lower()
                )
                
                if is_sap:
                    sap_count += 1
                    status = doc.get("status", "")
                    if status == "processed":
                        sap_processed += 1
                    elif status == "processing":
                        sap_processing += 1
                    elif status == "failed":
                        sap_failed += 1
            
            print(f"  总文档数: {total}")
            print(f"  SAP相关文档: {sap_count}")
            print(f"    已处理: {sap_processed}")
            print(f"    处理中: {sap_processing}")
            print(f"    失败: {sap_failed}")
        else:
            print(f"  ✗ 无法获取文档列表: HTTP {response.status_code}")
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
    
    # 4. 问题诊断
    print("\n4. 问题诊断")
    print("-" * 80)
    
    issues = []
    recommendations = []
    
    if sap_count == 0:
        issues.append("没有找到SAP相关的索引文档")
        recommendations.append("语义索引构建可能还没有开始")
        recommendations.append("建议运行: python build_semantic_index.py")
    
    if sap_processing > 0:
        recommendations.append(f"有 {sap_processing} 个文档正在处理中，请稍后检查")
    
    if sap_failed > 0:
        issues.append(f"有 {sap_failed} 个文档处理失败")
        recommendations.append("检查知识库服务日志以查看错误详情")
    
    if issues:
        print("  发现的问题:")
        for issue in issues:
            print(f"    ⚠️  {issue}")
    
    if recommendations:
        print("\n  建议:")
        for rec in recommendations:
            print(f"    💡 {rec}")
    
    # 5. 总结
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    
    if sap_count == 0:
        print("⚠️  语义索引构建尚未开始")
        print("   需要运行语义索引构建脚本")
    elif sap_processed > 0:
        progress = (sap_processed / 109022) * 100 if sap_processed > 0 else 0
        print(f"📊 当前进度: {sap_processed:,} / 109,022 ({progress:.2f}%)")
    else:
        print("⏳ 语义索引构建正在进行中或遇到问题")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        get_summary()
    except KeyboardInterrupt:
        print("\n\n⚠️  报告生成中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

