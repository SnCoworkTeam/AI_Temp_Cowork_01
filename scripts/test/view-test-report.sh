#!/bin/bash
# 查看测试报告脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "=========================================="
echo -e "${BLUE}📊 测试报告查看器${NC}"
echo "=========================================="
echo ""

# 检查测试结果目录
if [ ! -d "test-results" ]; then
    echo -e "${YELLOW}⚠️  测试结果目录不存在，请先运行测试${NC}"
    exit 1
fi

# 显示最新测试报告
show_latest_report() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📋 最新测试报告${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ -f "test-results/test-report.md" ]; then
        cat test-results/test-report.md
    else
        echo -e "${YELLOW}⚠️  未找到测试报告，请先运行测试${NC}"
    fi
}

# 显示测试统计
show_statistics() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📈 测试统计${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # 统计JUnit XML报告
    if ls test-results/*-results.xml 1> /dev/null 2>&1; then
        echo -e "${BLUE}JUnit XML报告:${NC}"
        for xml_file in test-results/*-results.xml; do
            if [ -f "$xml_file" ]; then
                tests=$(grep -o 'tests="[0-9]*"' "$xml_file" | grep -o '[0-9]*' | head -1)
                failures=$(grep -o 'failures="[0-9]*"' "$xml_file" | grep -o '[0-9]*' | head -1)
                errors=$(grep -o 'errors="[0-9]*"' "$xml_file" | grep -o '[0-9]*' | head -1)
                name=$(basename "$xml_file" -results.xml)
                echo "  - $name: 总计=$tests, 失败=$failures, 错误=$errors"
            fi
        done
    fi
    
    # 显示覆盖率
    if [ -f "coverage.json" ]; then
        echo ""
        echo -e "${BLUE}代码覆盖率:${NC}"
        coverage=$(python3 -c "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.2f}%\")" 2>/dev/null || echo "N/A")
        echo "  总覆盖率: $coverage"
    fi
}

# 显示测试日志
show_logs() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📝 测试日志${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if ls test-results/*-output.log 1> /dev/null 2>&1; then
        echo -e "${BLUE}可用的测试日志:${NC}"
        ls -lh test-results/*-output.log | awk '{print "  - " $9 " (" $5 ")"}'
        echo ""
        read -p "输入要查看的日志文件名（或按Enter查看最新）: " log_file
        if [ -z "$log_file" ]; then
            log_file=$(ls -t test-results/*-output.log | head -1)
        fi
        if [ -f "$log_file" ]; then
            echo ""
            echo -e "${BLUE}日志内容（最后50行）:${NC}"
            tail -50 "$log_file"
        fi
    else
        echo -e "${YELLOW}⚠️  未找到测试日志${NC}"
    fi
}

# 显示覆盖率报告
show_coverage() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 代码覆盖率报告${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ -d "coverage-report" ]; then
        echo -e "${BLUE}覆盖率报告目录:${NC}"
        ls -lh coverage-report/ | grep -E "\.html$|\.json$" | awk '{print "  - " $9 " (" $5 ")"}'
        echo ""
        echo -e "${GREEN}💡 提示: 在浏览器中打开 coverage-report/ 目录下的HTML文件查看详细覆盖率报告${NC}"
    else
        echo -e "${YELLOW}⚠️  未找到覆盖率报告${NC}"
    fi
}

# 主菜单
main_menu() {
    while true; do
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}📊 测试报告查看器 - 主菜单${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "1. 查看最新测试报告"
        echo "2. 查看测试统计"
        echo "3. 查看测试日志"
        echo "4. 查看代码覆盖率"
        echo "5. 查看所有报告"
        echo "6. 运行新测试"
        echo "0. 退出"
        echo ""
        read -p "请选择 [0-6]: " choice
        
        case $choice in
            1) show_latest_report ;;
            2) show_statistics ;;
            3) show_logs ;;
            4) show_coverage ;;
            5) 
                show_latest_report
                show_statistics
                show_coverage
                ;;
            6)
                echo ""
                echo -e "${BLUE}运行测试...${NC}"
                bash scripts/test/run-tests-simple.sh
                ;;
            0)
                echo ""
                echo -e "${GREEN}退出${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选择${NC}"
                ;;
        esac
    done
}

# 如果提供了参数，直接执行对应功能
case "${1:-}" in
    latest|report)
        show_latest_report
        ;;
    stats|statistics)
        show_statistics
        ;;
    logs|log)
        show_logs
        ;;
    coverage|cov)
        show_coverage
        ;;
    all)
        show_latest_report
        show_statistics
        show_coverage
        ;;
    *)
        main_menu
        ;;
esac

