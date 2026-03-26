# 项目管理功能测试指南

本目录包含项目管理功能的独立测试脚本，每个脚本只测试一个功能模块。

## 测试脚本列表

### 1. 项目查询功能测试
**文件**: `test-project-list.ps1`
**功能**: 测试项目列表和详情查询
- ✅ 获取项目列表（无参数）
- ✅ 分页查询
- ✅ 状态过滤
- ✅ 获取项目详情

**运行方式**:
```powershell
pwsh -File test-project-list.ps1
```

**是否需要Token**: 可选（查询功能通常不需要认证）

---

### 2. 项目创建功能测试
**文件**: `test-project-create.ps1`
**功能**: 测试项目创建
- ✅ 创建新项目
- ✅ 验证项目编码唯一性
- ✅ 返回创建的项目信息

**运行方式**:
```powershell
pwsh -File test-project-create.ps1
```

**是否需要Token**: **必需**

**注意事项**:
- 会自动生成唯一的项目编码（格式：TEST-YYYYMMDDHHmmss）
- 创建成功后请保存项目ID，用于后续测试

---

### 3. 项目更新功能测试
**文件**: `test-project-update.ps1`
**功能**: 测试项目信息更新
- ✅ 获取项目当前信息
- ✅ 更新项目信息
- ✅ 验证更新结果

**运行方式**:
```powershell
pwsh -File test-project-update.ps1
```

**是否需要Token**: **必需**

**需要输入**: 项目ID（从创建测试中获得）

---

### 4. 项目删除功能测试
**文件**: `test-project-delete.ps1`
**功能**: 测试项目删除
- ✅ 获取项目信息确认
- ✅ 删除项目（需要确认）
- ✅ 验证删除结果

**运行方式**:
```powershell
pwsh -File test-project-delete.ps1
```

**是否需要Token**: **必需**

**需要输入**: 项目ID

**⚠️ 警告**: 删除操作不可逆，会级联删除相关数据（阶段、任务、里程碑、周报、风险）

---

### 5. 周报功能测试
**文件**: `test-weekly-report.ps1`
**功能**: 测试周报的查询和创建
- ✅ 获取周报列表
- ✅ 按项目筛选周报
- ✅ 创建周报

**运行方式**:
```powershell
pwsh -File test-weekly-report.ps1
```

**是否需要Token**: 创建周报需要，查询可选

**需要输入**: 
- 查询：项目ID（可选）
- 创建：项目ID（必需）

---

### 6. 月报功能测试
**文件**: `test-monthly-report.ps1`
**功能**: 测试月报的查询和创建
- ✅ 获取月报列表
- ✅ 按项目筛选月报
- ✅ 创建月报

**运行方式**:
```powershell
pwsh -File test-monthly-report.ps1
```

**是否需要Token**: 创建月报需要，查询可选

**需要输入**: 
- 查询：项目ID（可选）
- 创建：项目ID（必需）

---

## 测试顺序建议

### 完整功能测试流程
1. **查询测试** → `test-project-list.ps1` （验证基础查询功能）
2. **创建测试** → `test-project-create.ps1` （创建测试项目，保存项目ID）
3. **更新测试** → `test-project-update.ps1` （使用步骤2的项目ID）
4. **周报测试** → `test-weekly-report.ps1` （使用步骤2的项目ID）
5. **月报测试** → `test-monthly-report.ps1` （使用步骤2的项目ID）
6. **删除测试** → `test-project-delete.ps1` （清理测试数据，使用步骤2的项目ID）

### 快速验证流程
如果只想验证基本功能：
1. `test-project-list.ps1` - 验证查询
2. `test-project-create.ps1` - 验证创建
3. `test-project-update.ps1` - 验证更新

---

## 获取认证Token

### 方法1: 从浏览器获取
1. 登录系统
2. 打开浏览器开发者工具（F12）
3. 进入 Application/Storage → Local Storage
4. 查找 `access_token` 或 `token` 字段
5. 复制token值

### 方法2: 从登录接口获取
```powershell
$loginData = @{
    username = "your_username"
    password = "your_password"
} | ConvertTo-Json

$response = Invoke-RestMethod -Method POST -Uri "http://43.143.139.197:8080/api/v1/auth/login" -Body $loginData -ContentType "application/json"
$token = $response.access_token
```

---

## 常见问题

### 1. 401 Unauthorized
**原因**: Token无效或已过期
**解决**: 重新登录获取新Token

### 2. 400 Bad Request
**原因**: 请求数据格式错误或缺少必需字段
**解决**: 检查请求数据格式，确保所有必需字段都已提供

### 3. 404 Not Found
**原因**: 项目ID不存在
**解决**: 确认项目ID是否正确，或先运行创建测试

### 4. 500 Internal Server Error
**原因**: 服务器内部错误
**解决**: 检查服务器日志，联系管理员

---

## 测试结果说明

每个测试脚本会显示：
- ✅ **成功**: 操作成功完成
- ❌ **失败**: 操作失败，会显示错误信息
- ⏭️ **跳过**: 由于缺少必要信息而跳过

测试完成后会显示测试结果汇总。

---

## 注意事项

1. **测试环境**: 所有测试都针对生产服务器 `43.143.139.197:8080`
2. **测试数据**: 创建的测试项目会保留在数据库中，建议测试完成后删除
3. **并发测试**: 不建议同时运行多个测试脚本
4. **数据清理**: 测试完成后记得删除测试项目，避免污染数据

---

## 联系支持

如果测试过程中遇到问题，请：
1. 检查服务器状态
2. 查看服务器日志
3. 确认网络连接
4. 验证Token有效性

