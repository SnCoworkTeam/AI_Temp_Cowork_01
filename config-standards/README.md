# 统一代码质量检查配置包

本项目提供统一的代码质量检查配置，用于所有微服务项目。

## 📦 包含的配置包

### 前端配置

- **@enterprise-ai/eslint-config**: ESLint统一配置
- **@enterprise-ai/prettier-config**: Prettier统一配置
- **@enterprise-ai/typescript-config**: TypeScript基础配置

### 后端配置

- **@enterprise-ai/python-config**: Python代码质量配置
  - Black (代码格式化)
  - isort (导入排序)
  - Ruff (静态分析)
  - mypy (类型检查)
  - Pylint (代码质量)

## 🚀 使用方法

### 前端服务 (Next.js)

#### 1. 安装依赖

```bash
cd web-ui
npm install --save-dev @enterprise-ai/eslint-config @enterprise-ai/prettier-config prettier eslint-config-prettier
```

#### 2. 配置ESLint

创建或更新 `.eslintrc.json`:

```json
{
  "extends": ["@enterprise-ai/eslint-config"]
}
```

#### 3. 配置Prettier

创建 `.prettierrc.js`:

```javascript
module.exports = require('@enterprise-ai/prettier-config');
```

#### 4. 配置TypeScript

更新 `tsconfig.json`:

```json
{
  "extends": "@enterprise-ai/typescript-config/tsconfig.base.json",
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

#### 5. 配置Git钩子

```bash
npm install --save-dev husky lint-staged
npx husky init
```

复制 `config-standards/templates/.lintstagedrc.js` 到项目根目录。

### 后端服务 (Python)

#### 1. 复制配置文件

```bash
cp config-standards/packages/python-config/pyproject.toml project_management/
cp config-standards/packages/python-config/mypy.ini project_management/
cp config-standards/packages/python-config/.pylintrc project_management/
```

#### 2. 安装工具

```bash
pip install black isort ruff mypy pylint
```

#### 3. 运行检查

```bash
# 格式化
black project_management/src/

# 导入排序
isort project_management/src/

# 静态分析
ruff check project_management/src/

# 类型检查
mypy project_management/src/
```

## 📝 配置说明

### ESLint规则

- TypeScript严格模式
- React Hooks规则
- Next.js最佳实践
- Prettier集成

### Prettier规则

- 单引号
- 行长度: 100
- 尾随逗号: ES5
- 换行符: LF

### Python规则

- 行长度: 120
- Black格式化
- isort导入排序
- Ruff静态分析
- mypy类型检查

## 🔧 自定义配置

每个服务可以在继承基础配置后，添加项目特定的规则覆盖。

### 前端示例

```json
{
  "extends": ["@enterprise-ai/eslint-config"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "off"  // 项目特定规则
  }
}
```

### 后端示例

在 `pyproject.toml` 中添加项目特定配置：

```toml
[tool.ruff.lint]
ignore = ["E501", "自定义规则"]
```

## 📚 更多信息

详细的使用说明和最佳实践，请参考各配置包的文档。

