#!/bin/bash
# 快速测试元数据前置意图识别功能

echo "=========================================="
echo "元数据前置意图识别快速测试"
echo "=========================================="

# 测试邮件发送意图
echo ""
echo "测试1: 邮件发送意图识别"
curl -X POST http://localhost:8010/api/v1/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "发送邮件给yubin.liu@pcitc.com，主题是会议通知",
    "user_id": "test_user"
  }' | jq '.'

# 等待一下
sleep 2

# 测试SAP查询意图
echo ""
echo "测试2: SAP查询意图识别"
curl -X POST http://localhost:8010/api/v1/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "查询销售订单",
    "user_id": "test_user"
  }' | jq '.'

# 等待一下
sleep 2

# 查看性能指标
echo ""
echo "测试3: 查看性能指标"
curl -X GET http://localhost:8010/api/v1/performance/metrics | jq '.'

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="


