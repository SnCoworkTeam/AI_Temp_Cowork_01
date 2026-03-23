# 重启 Next.js 开发服务器指南

## 🚀 快速重启步骤

### 方法 1: 在运行开发服务器的终端中

1. **停止服务器**：
   - 在运行 `npm run dev` 的终端窗口中
   - 按 `Ctrl + C` 停止服务器

2. **清除缓存（推荐）**：
   ```powershell
   # 在 web-ui 目录下
   cd web-ui
   Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
   ```

3. **重新启动**：
   ```powershell
   npm run dev
   ```

### 方法 2: 如果找不到终端窗口

1. **查找并结束 Node.js 进程**：
   ```powershell
   # 查找 Next.js 进程
   Get-Process | Where-Object {$_.ProcessName -eq "node"} | Stop-Process -Force
   ```

2. **清除缓存并重启**：
   ```powershell
   cd web-ui
   Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
   npm run dev
   ```

## ✅ 验证服务器已重启

重启后，您应该看到：

```
▲ Next.js 14.0.4
- Local:        http://localhost:3000
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
```

## 🔍 检查路由是否生效

重启后，在浏览器中访问：
```
http://localhost:3000/api/knowledge/documents/test-id
```

应该返回错误（400 或 404），而不是路由未找到的错误。

## ⚠️ 注意事项

1. **保存工作**：重启前确保已保存所有文件更改
2. **等待启动**：服务器启动需要几秒钟
3. **检查端口**：确保 3000 端口没有被其他程序占用

## 🐛 如果重启后仍有问题

1. **检查文件是否存在**：
   ```
   web-ui/src/app/api/knowledge/documents/[id]/route.ts
   ```

2. **检查文件内容**：
   - 确保文件包含 `export async function DELETE`
   - 确保没有语法错误

3. **查看控制台输出**：
   - 检查是否有编译错误
   - 检查是否有路由注册信息

4. **尝试硬刷新浏览器**：
   - `Ctrl + Shift + R` (Windows)
   - `Cmd + Shift + R` (Mac)


