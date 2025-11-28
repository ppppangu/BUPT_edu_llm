# UV 包管理经验总结

> 本文档总结了使用 uv 管理 Python 项目的最佳实践，供项目复用。

## 一、项目结构

```
project/
├── pyproject.toml      # 核心配置文件
├── .python-version     # Python 版本锁定
├── uv.lock            # 依赖锁定文件（自动生成）
├── .venv/             # 虚拟环境（自动创建）
├── src/ 或 backend/    # 源码目录
└── tests/             # 测试目录
    ├── conftest.py    # 共享 fixtures
    ├── unit/          # 单元测试（mock 外部依赖）
    ├── integration/   # 集成测试（实际调用外部 API）
    └── e2e/           # 端到端测试（启动服务测试）
```

## 二、pyproject.toml 模板

```toml
[project]
name = "project-name"
version = "0.1.0"
description = "项目描述"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    # 生产依赖
    "fastapi>=0.104.1",
    "pydantic>=2.5.2",
]

[project.optional-dependencies]
dev = [
    # 开发/测试依赖（pip install -e ".[dev]" 方式）
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["backend"]  # 或 ["src/package_name"]

[dependency-groups]
dev = [
    # 开发/测试依赖（新标准，替代 tool.uv.dev-dependencies）
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "httpx>=0.24.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "-v --tb=short"
asyncio_mode = "auto"
markers = [
    "integration: marks tests as integration tests (require network)",
    "e2e: marks tests as end-to-end tests (require running server)",
    "slow: marks tests as slow running",
]
```

## 三、常用命令

### 初始化与安装

```bash
# 初始化新项目
uv init project-name
cd project-name

# 安装所有依赖（生产+开发）
uv sync

# 仅安装生产依赖
uv sync --no-dev

# 添加生产依赖
uv add fastapi pydantic

# 添加开发依赖
uv add --dev pytest pytest-cov
```

### 运行命令

```bash
# 运行 Python 脚本
uv run python -m backend.main

# 运行所有测试
uv run pytest

# 仅运行单元测试
uv run pytest tests/unit

# 仅运行集成测试
uv run pytest tests/integration -m integration

# 仅运行端到端测试
uv run pytest tests/e2e -m e2e

# 跳过集成测试和端到端测试
uv run pytest -m "not integration and not e2e"

# 运行测试并生成覆盖率报告
uv run pytest tests/unit --cov=backend --cov-report=html

# 运行特定测试文件
uv run pytest tests/unit/test_api.py

# 运行特定测试函数
uv run pytest tests/unit/test_api.py::TestHealthEndpoint::test_health_check
```

### 依赖管理

```bash
# 更新所有依赖
uv sync --upgrade

# 更新特定包
uv add package-name --upgrade

# 移除依赖
uv remove package-name

# 查看依赖树
uv tree

# 导出 requirements.txt（兼容性需要时）
uv pip compile pyproject.toml -o requirements.txt
```

## 四、最佳实践

### 1. 版本约束策略

```toml
dependencies = [
    # 推荐：使用 >= 允许小版本更新
    "fastapi>=0.104.1",

    # 锁定大版本，允许小版本更新
    "pydantic>=2.5.0,<3.0.0",

    # 精确版本（仅在必要时使用）
    "akshare==1.12.0",
]
```

### 2. Python 版本

- 在 `.python-version` 中指定版本（如 `3.11`）
- `requires-python` 设置最低兼容版本（如 `>=3.10`）

### 3. 开发依赖分离

使用 `[dependency-groups] dev` 而非 `[project.optional-dependencies]`：
- PEP 735 新标准，uv 原生支持
- `uv sync` 自动包含，`uv sync --no-dev` 排除
- 替代已废弃的 `[tool.uv] dev-dependencies`

### 4. 测试配置

将 pytest 配置放在 `pyproject.toml` 的 `[tool.pytest.ini_options]` 中，无需单独的 `pytest.ini`。

### 5. 锁定文件

- `uv.lock` 应提交到版本控制
- 确保团队和 CI/CD 环境一致

## 五、CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest --cov
```

## 六、从旧项目迁移

```bash
# 1. 在项目目录初始化
uv init --name project-name

# 2. 从 requirements.txt 导入依赖
uv add $(cat requirements.txt | grep -v '^#' | tr '\n' ' ')

# 3. 添加开发依赖
uv add --dev pytest pytest-cov httpx

# 4. 删除旧文件
rm requirements.txt requirements-dev.txt pytest.ini

# 5. 同步并生成锁定文件
uv sync
```

## 七、常见问题

### Q: uv sync 报错找不到包？
检查 `requires-python` 版本是否与当前 Python 兼容。

### Q: 如何在 Docker 中使用？
```dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
CMD ["uv", "run", "python", "-m", "backend.main"]
```

### Q: 与 pip 的兼容性？
```bash
# 导出供 pip 使用
uv pip compile pyproject.toml -o requirements.txt
uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
```

## 八、项目模板

为新项目快速初始化，可使用以下命令：

```bash
# 创建项目
uv init my-project && cd my-project

# 设置 Python 版本
echo "3.11" > .python-version

# 添加常用依赖（根据项目类型选择）
# Web API 项目
uv add fastapi uvicorn pydantic python-dotenv

# 添加测试依赖
uv add --dev pytest pytest-asyncio pytest-cov httpx

# 创建目录结构
mkdir -p src tests
touch src/__init__.py tests/__init__.py tests/conftest.py

# 同步
uv sync
```

---

**总结**：uv 相比 pip/poetry 的优势在于速度快、配置简洁、锁定文件可靠。建议所有新项目使用 uv 管理依赖。
