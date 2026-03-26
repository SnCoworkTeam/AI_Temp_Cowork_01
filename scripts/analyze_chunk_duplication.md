# Chunk重复问题分析

## 问题描述
接收了653个chunk，很多是重复的。

## 可能的原因

### 1. 思考内容流式输出（已修复）
- 每个增量都是一个chunk
- 已通过只保留最新chunk修复

### 2. Execution chunk数量
- 每个agent: agent_start + agent_complete = 2个chunk
- 每层: layer_start + layer_complete = 2个chunk
- 其他: execution_start, synthesizing, execution_complete = 3个chunk
- 如果有10个agent分5层: 1 + 5*2 + 10*2 + 1 + 1 = 33个execution chunk

### 3. final_result可能包含大量数据
- final_result可能包含所有agent_results的摘要
- 如果agent_results很大，final_result也会很大

### 4. 可能的重复
- agent_result在agent_complete时只发送元数据（good）
- 但final_result可能包含完整的agent_results数据

## 优化建议

1. **减少final_result中的数据量**
   - 不要在final_result中包含完整的agent_results
   - 只包含摘要信息

2. **前端去重**
   - 对于相同stage的chunk，只保留最新的
   - 特别是agent_complete，如果同一个agent有多个complete，只保留最后一个

3. **压缩chunk数据**
   - 移除不必要的字段
   - 只发送前端需要的数据

