#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一企业语义系统综合测试脚本
测试知识库、元数据管理、语义搜索和推理功能
"""
import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# 设置UTF-8编码
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 禁用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 服务器配置
BASE_URL = "http://43.143.139.197"
KNOWLEDGE_BASE_URL = f"{BASE_URL}:8004"
METADATA_SERVICE_URL = f"{BASE_URL}:8005"
VECTOR_COORDINATOR_URL = f"{BASE_URL}:8020"

class SemanticSystemTester:
    def __init__(self):
        self.results = {
            "knowledge_base": {"passed": [], "failed": []},
            "metadata_service": {"passed": [], "failed": []},
            "semantic_search": {"passed": [], "failed": []},
            "integration": {"passed": [], "failed": []},
        }

    def log(self, category: str, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✓" if success else "✗"
        print(f"{status} [{category}] {test_name}")
        if message:
            print(f"  {message}")

        if success:
            self.results[category]["passed"].append(test_name)
        else:
            self.results[category]["failed"].append({"test": test_name, "message": message})

    # ========== 知识库功能测试 ==========

    def test_knowledge_base_health(self):
        """测试知识库服务健康状态"""
        try:
            session = requests.Session()
            session.trust_env = False  # 忽略系统代理设置
            response = session.get(f"{KNOWLEDGE_BASE_URL}/api/health", timeout=5)
            success = response.status_code == 200
            self.log("knowledge_base", "健康检查", success,
                    f"状态码: {response.status_code}")
            return success
        except Exception as e:
            self.log("knowledge_base", "健康检查", False, str(e))
            return False

    def test_create_document(self):
        """测试创建文档"""
        try:
            doc_data = {
                "title": "测试文档 - 企业语义系统",
                "content": "这是一个测试文档，用于验证知识库的文档管理功能。包含企业语义、知识图谱、元数据管理等关键词。",
                "category": "测试",
                "tags": ["测试", "企业语义", "知识管理"]
            }
            response = requests.post(
                f"{KNOWLEDGE_BASE_URL}/api/documents",
                json=doc_data,
                timeout=10
            )
            success = response.status_code in [200, 201]
            result = response.json() if success else None
            self.log("knowledge_base", "创建文档", success,
                    f"文档ID: {result.get('id') if result else 'N/A'}")
            return result
        except Exception as e:
            self.log("knowledge_base", "创建文档", False, str(e))
            return None

    def test_search_documents(self, query: str = "企业语义"):
        """测试文档搜索"""
        try:
            response = requests.get(
                f"{KNOWLEDGE_BASE_URL}/api/search",
                params={"query": query, "top_k": 5},
                timeout=10
            )
            success = response.status_code == 200
            results = response.json() if success else None
            count = len(results.get("results", [])) if results else 0
            self.log("knowledge_base", "文档搜索", success,
                    f"查询: '{query}', 找到 {count} 个结果")
            return results
        except Exception as e:
            self.log("knowledge_base", "文档搜索", False, str(e))
            return None

    def test_knowledge_graph(self):
        """测试知识图谱功能"""
        try:
            response = requests.get(
                f"{KNOWLEDGE_BASE_URL}/api/knowledge-graph",
                timeout=10
            )
            success = response.status_code == 200
            data = response.json() if success else None
            nodes = len(data.get("nodes", [])) if data else 0
            edges = len(data.get("edges", [])) if data else 0
            self.log("knowledge_base", "知识图谱查询", success,
                    f"节点数: {nodes}, 关系数: {edges}")
            return data
        except Exception as e:
            self.log("knowledge_base", "知识图谱查询", False, str(e))
            return None

    # ========== 元数据服务测试 ==========

    def test_metadata_service_health(self):
        """测试元数据服务健康状态"""
        try:
            response = requests.get(f"{METADATA_SERVICE_URL}/api/health", timeout=5)
            success = response.status_code == 200
            self.log("metadata_service", "健康检查", success,
                    f"状态码: {response.status_code}")
            return success
        except Exception as e:
            self.log("metadata_service", "健康检查", False, str(e))
            return False

    def test_list_data_assets(self):
        """测试列出数据资产"""
        try:
            response = requests.get(
                f"{METADATA_SERVICE_URL}/api/data-assets",
                params={"page": 1, "page_size": 10},
                timeout=10
            )
            success = response.status_code == 200
            data = response.json() if success else None
            count = len(data.get("items", [])) if data else 0
            total = data.get("total", 0) if data else 0
            self.log("metadata_service", "列出数据资产", success,
                    f"返回 {count} 个资产, 总数: {total}")
            return data
        except Exception as e:
            self.log("metadata_service", "列出数据资产", False, str(e))
            return None

    def test_search_metadata(self, query: str = "SAP"):
        """测试元数据搜索"""
        try:
            response = requests.get(
                f"{METADATA_SERVICE_URL}/api/search",
                params={"query": query},
                timeout=10
            )
            success = response.status_code == 200
            results = response.json() if success else None
            count = len(results.get("results", [])) if results else 0
            self.log("metadata_service", "元数据搜索", success,
                    f"查询: '{query}', 找到 {count} 个结果")
            return results
        except Exception as e:
            self.log("metadata_service", "元数据搜索", False, str(e))
            return None

    def test_ontology(self):
        """测试本体（业务术语）功能"""
        try:
            response = requests.get(
                f"{METADATA_SERVICE_URL}/api/ontology",
                timeout=10
            )
            success = response.status_code == 200
            data = response.json() if success else None
            count = len(data.get("terms", [])) if data else 0
            self.log("metadata_service", "本体查询", success,
                    f"业务术语数量: {count}")
            return data
        except Exception as e:
            self.log("metadata_service", "本体查询", False, str(e))
            return None

    def test_entity_registry(self):
        """测试实体注册中心"""
        try:
            response = requests.get(
                f"{METADATA_SERVICE_URL}/api/entities",
                timeout=10
            )
            success = response.status_code == 200
            data = response.json() if success else None
            count = len(data.get("entities", [])) if data else 0
            self.log("metadata_service", "实体注册中心", success,
                    f"实体数量: {count}")
            return data
        except Exception as e:
            self.log("metadata_service", "实体注册中心", False, str(e))
            return None

    # ========== 语义搜索和推理测试 ==========

    def test_semantic_search(self, query: str = "采购订单流程"):
        """测试语义搜索"""
        try:
            response = requests.post(
                f"{KNOWLEDGE_BASE_URL}/api/search/semantic",
                json={"query": query, "top_k": 5},
                timeout=10
            )
            success = response.status_code == 200
            results = response.json() if success else None
            count = len(results.get("results", [])) if results else 0
            self.log("semantic_search", "语义搜索", success,
                    f"查询: '{query}', 找到 {count} 个结果")
            return results
        except Exception as e:
            self.log("semantic_search", "语义搜索", False, str(e))
            return None

    def test_recommendation(self):
        """测试智能推荐"""
        try:
            response = requests.get(
                f"{METADATA_SERVICE_URL}/api/recommendations",
                params={"entity_type": "data_asset", "limit": 5},
                timeout=10
            )
            success = response.status_code == 200
            data = response.json() if success else None
            count = len(data.get("recommendations", [])) if data else 0
            self.log("semantic_search", "智能推荐", success,
                    f"推荐数量: {count}")
            return data
        except Exception as e:
            self.log("semantic_search", "智能推荐", False, str(e))
            return None

    # ========== 系统集成测试 ==========

    def test_vector_coordinator(self):
        """测试向量协调服务"""
        try:
            response = requests.get(f"{VECTOR_COORDINATOR_URL}/api/health", timeout=5)
            success = response.status_code == 200
            self.log("integration", "向量协调服务", success,
                    f"状态码: {response.status_code}")
            return success
        except Exception as e:
            self.log("integration", "向量协调服务", False, str(e))
            return False

    def test_cross_service_search(self, query: str = "采购"):
        """测试跨服务搜索"""
        print(f"\n=== 跨服务搜索测试: '{query}' ===")

        # 在知识库中搜索
        kb_results = self.test_search_documents(query)

        # 在元数据服务中搜索
        md_results = self.test_search_metadata(query)

        kb_count = len(kb_results.get('results', [])) if kb_results and isinstance(kb_results, dict) else 0
        md_count = len(md_results.get('results', [])) if md_results and isinstance(md_results, dict) else 0

        success = kb_results is not None or md_results is not None
        self.log("integration", "跨服务搜索", success,
                f"知识库结果: {kb_count}个, 元数据结果: {md_count}个")
        return success

    # ========== 运行所有测试 ==========

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("统一企业语义系统综合测试")
        print("="*80)

        # 1. 知识库功能测试
        print("\n### 1. 知识库功能测试 ###\n")
        self.test_knowledge_base_health()
        doc = self.test_create_document()
        self.test_search_documents()
        self.test_knowledge_graph()

        # 2. 元数据服务测试
        print("\n### 2. 元数据服务测试 ###\n")
        self.test_metadata_service_health()
        self.test_list_data_assets()
        self.test_search_metadata()
        self.test_ontology()
        self.test_entity_registry()

        # 3. 语义搜索和推理测试
        print("\n### 3. 语义搜索和推理测试 ###\n")
        self.test_semantic_search()
        self.test_recommendation()

        # 4. 系统集成测试
        print("\n### 4. 系统集成测试 ###\n")
        self.test_vector_coordinator()
        self.test_cross_service_search()

        # 打印测试报告
        self.print_report()

    def print_report(self):
        """打印测试报告"""
        print("\n" + "="*80)
        print("测试报告")
        print("="*80)

        total_passed = 0
        total_failed = 0

        for category, results in self.results.items():
            passed = len(results["passed"])
            failed = len(results["failed"])
            total_passed += passed
            total_failed += failed

            print(f"\n### {category} ###")
            print(f"通过: {passed}, 失败: {failed}")

            if results["failed"]:
                print("\n失败的测试:")
                for fail in results["failed"]:
                    print(f"  - {fail['test']}: {fail['message']}")

        print("\n" + "="*80)
        print(f"总计: 通过 {total_passed}, 失败 {total_failed}")
        success_rate = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        print("="*80)

        # 保存报告到文件
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_passed": total_passed,
                "total_failed": total_failed,
                "success_rate": f"{success_rate:.1f}%"
            },
            "details": self.results
        }

        with open("semantic_system_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print("\n测试报告已保存到: semantic_system_test_report.json")

if __name__ == "__main__":
    tester = SemanticSystemTester()
    tester.run_all_tests()
