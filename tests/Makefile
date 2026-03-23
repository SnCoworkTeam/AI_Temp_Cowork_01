# Makefile for running tests
# 使用方法: make test-unit, make test-integration, etc.

.PHONY: help test-unit test-integration test-performance test-security test-all coverage clean

help:
	@echo "可用命令:"
	@echo "  make test-unit          - 运行单元测试"
	@echo "  make test-integration   - 运行集成测试"
	@echo "  make test-performance   - 运行性能测试"
	@echo "  make test-security      - 运行安全测试"
	@echo "  make test-all           - 运行所有测试"
	@echo "  make coverage           - 运行测试并生成覆盖率报告"
	@echo "  make clean              - 清理测试缓存和临时文件"

test-unit:
	pytest -m unit -v

test-integration:
	pytest -m integration -v

test-performance:
	pytest -m performance -v

test-security:
	pytest -m security -v

test-all:
	pytest -v

coverage:
	pytest --cov=. --cov-report=html --cov-report=term --cov-report=json
	@echo "覆盖率报告已生成: htmlcov/index.html"

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.json
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete









