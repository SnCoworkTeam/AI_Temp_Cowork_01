# 文档生成工具

## 脚本说明

### generate-api-docs.py
从FastAPI应用生成OpenAPI规范和Postman集合。

**使用方法**:
```bash
python scripts/docs/generate-api-docs.py
```

**输出**:
- `docs/api-docs/openapi/*-openapi.json`
- `docs/api-docs/postman/*-postman.json`

### generate-code-docs.py
从代码注释生成代码文档。

**使用方法**:
```bash
python scripts/docs/generate-code-docs.py
```

**输出**:
- `docs/auto-generated/code-docs/**/*.md`

### generate-dependency-graph.py
生成模块依赖关系图。

**使用方法**:
```bash
python scripts/docs/generate-dependency-graph.py
```

**输出**:
- `docs/auto-generated/dependency-graphs/dependencies.dot`
- `docs/auto-generated/dependency-graphs/dependencies.mmd`
- `docs/auto-generated/dependency-graphs/dependencies.png` (需要Graphviz)

### generate-api-reference.py
从OpenAPI规范生成API参考文档。

**使用方法**:
```bash
python scripts/docs/generate-api-reference.py
```

**输出**:
- `docs/auto-generated/api-reference/*-api-reference.md`

### generate-all.py
运行所有文档生成脚本。

**使用方法**:
```bash
python scripts/docs/generate-all.py
```

### check-documentation.py
检查文档完整性。

**使用方法**:
```bash
python scripts/docs/check-documentation.py
```

## 依赖安装

```bash
pip install -r scripts/docs/requirements.txt
```

## CI/CD集成

在CI/CD流水线中自动生成文档：

```yaml
- name: Generate Documentation
  run: |
    pip install -r scripts/docs/requirements.txt
    python scripts/docs/generate-all.py
```









