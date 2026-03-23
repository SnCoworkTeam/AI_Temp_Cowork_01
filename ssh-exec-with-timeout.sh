#!/bin/bash
# SSH执行命令，带10秒超时和自动重连
# 用法: ssh-exec-with-timeout.sh "command"

COMMAND="$1"
CONFIG_FILE="remote.ssh"
HOST="enterprise-ai-server"
MAX_RETRIES=3
TIMEOUT=10

for i in $(seq 1 $MAX_RETRIES); do
    if [ $i -gt 1 ]; then
        echo "重试连接 ($i/$MAX_RETRIES)..." >&2
        sleep 2
    fi
    
    # 执行SSH命令，设置连接超时和执行超时
    timeout $TIMEOUT ssh -F "$CONFIG_FILE" -o ConnectTimeout=$TIMEOUT "$HOST" "$COMMAND" 2>&1
    
    EXIT_CODE=$?
    
    # 如果成功或非超时错误，退出
    if [ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -ne 124 ]; then
        exit $EXIT_CODE
    fi
    
    # 如果是超时，继续重试
    if [ $EXIT_CODE -eq 124 ]; then
        echo "命令超时，重新连接..." >&2
    fi
done

echo "达到最大重试次数，执行失败" >&2
exit 1

