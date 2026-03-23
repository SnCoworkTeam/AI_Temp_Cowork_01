#!/usr/bin/env python3
import requests
import json

url = 'http://localhost:8001/api/v1/dynamic-workflow/execute'
payload = {'user_input': '查询组织架构'}

print('开始测试工作流执行...')
agent_status = {}
final_result = None
chunk_count = 0

try:
    response = requests.post(url, json=payload, stream=True, timeout=300)
    response.raise_for_status()
    
    for line in response.iter_lines():
        if not line:
            continue
        try:
            if line.startswith(b'data: '):
                line = line[6:]
            chunk = json.loads(line.decode('utf-8'))
            chunk_count += 1
            
            chunk_type = chunk.get('type', '')
            stage = chunk.get('stage', '')
            
            if chunk_type == 'execution' and stage == 'agent_complete':
                agent_id = chunk.get('agent_id', 'unknown')
                agent_result = chunk.get('agent_result', {})
                success = agent_result.get('success', True)
                agent_status[agent_id] = success
                status_icon = '✓' if success else '✗'
                print(f'{status_icon} {agent_id}: success={success}')
            elif stage == 'execution_complete':
                final_result = chunk.get('final_result') or chunk.get('result')
                print(f'执行完成，最终结果: {"有" if final_result else "无"}')
        except:
            pass
    
    print(f'\n总计: {chunk_count} chunks, {len(agent_status)} agents')
    failed = [aid for aid, s in agent_status.items() if not s]
    if failed:
        print(f'失败的智能体: {failed}')
    else:
        print('所有智能体执行成功')
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()

