# 贡献指南

本指南帮助你快速上手，为 BUPT EDU LLM 平台贡献新的子项目。

## 目录

- [项目结构](#项目结构)
- [设计说明](#设计说明)
- [添加新项目（4步）](#添加新项目4步)
- [环境变量说明](#环境变量说明)
- [常见问题](#常见问题)
- [附录：部署脚本模板](#附录部署脚本模板)

---

## 项目结构

```
BUPT_edu_llm/
├── projects/                        # 所有子项目放这里
│   └── your_project/
│       ├── .env.example             # 环境变量模板
│       ├── scripts/
│       │   └── deploy.sh            # 部署脚本（自包含）
│       ├── backend/                 # 后端代码
│       ├── frontend/                # 前端代码
│       ├── data/                    # 数据文件
│       ├── docs/                    # 子项目文档
│       ├── tests/                   # 子项目测试（如果需要的话）
│       ├── pyproject.toml           # Python 项目配置
│       └── README.md                # 项目说明
│
├── scripts/
│   ├── start_all.sh                 # 统一启动脚本
│   └── stop_all.sh                  # 统一停止脚本
│
├── index.html                       # 聚合首页（nginx 托管）
└── .env                             # 平台级配置
```

---

## 设计说明

### 自包含原则

每个子项目是**完全自包含**的单元：
- 部署脚本 `scripts/deploy.sh` 放在项目内部，不依赖外部公共库
- 环境变量、依赖、文档都在项目目录内管理
- 项目可以独立 clone、独立部署、独立测试

### 为什么这样设计？

| 优点 | 说明 |
|------|------|
| **独立性** | 单个项目可以独立运行，不依赖平台其他部分 |
| **可移植** | 项目可以直接复制到其他地方使用 |
| **易维护** | 修改一个项目不影响其他项目 |
| **易贡献** | 新贡献者只需关注自己的项目目录 |

### 平台编排

根目录的 `scripts/start_all.sh` 负责：
1. 扫描 `projects/` 目录下的子项目
2. 检查各项目环境变量是否配置
3. 调用各项目的 `scripts/deploy.sh`

### 后端架构规范

对于提供公共服务的项目（如新闻爬虫、数据分析等），推荐采用以下架构：

#### API 路由规范

所有后端接口以 `/api/` 开头：

```
GET  /api/health              # 健康检查（必须）
GET  /api/xxx                 # 数据查询接口
GET  /api/xxx/stats           # 统计接口
```

nginx 配置后，完整路径为 `/<project_id>/api/xxx`，例如：
- `/alpha_sentiment/api/health`
- `/solar_news_crawler/api/news`

#### 数据刷新模式

**重要原则：前端只读，后端定时刷新**

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   定时任务       │ ───→ │   数据服务       │ ───→ │   JSON 文件     │
│ (APScheduler)   │      │ (爬虫/计算)      │      │   (data/)       │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                          │
                                                          ↓
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   前端页面       │ ←─── │   API 层        │ ←─── │   读取 JSON     │
│ (frontend/)     │      │ (/api/xxx)      │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

- **后端**：APScheduler 定时执行数据更新任务（每日凌晨）
- **前端**：只调用 `/api/xxx` 获取数据，**不提供刷新按钮**
- **数据**：存储为 JSON 文件，API 层读取后返回

#### 服务层设计

推荐的后端目录结构：

```
backend/
├── main.py              # 入口 + 路由定义
├── config.py            # 配置管理
├── scheduler.py         # APScheduler 定时任务
└── services/
    ├── data_service.py  # 数据读取服务
    └── xxx_service.py   # 其他业务服务
```

### README 规范

由于每个子项目的后端/前端实现各不相同，**每个子项目必须在 README.md 中清晰说明以下内容**：

#### 必须包含的内容

1. **项目简介** - 一句话说明项目功能
2. **项目结构** - 目录树 + 每个目录/文件的用途说明
3. **数据流图** - 数据从哪来、怎么处理、存到哪、怎么展示

#### README 模板

```markdown
# 项目名称

一句话项目简介。

## 项目结构

\`\`\`
your_project/
├── backend/                 # 后端服务
│   ├── main.py             # Flask 入口，定义 API 路由
│   ├── config.py           # 配置管理，读取环境变量
│   ├── scheduler.py        # 定时任务（APScheduler）
│   └── services/           # 业务逻辑层
│       ├── data_service.py # 数据读取服务
│       └── xxx_service.py  # 其他服务
├── frontend/               # 前端页面
│   └── index.html          # 主页面
├── data/                   # 数据存储目录
│   └── *.json              # 生成的数据文件
├── scripts/
│   └── deploy.sh           # 部署脚本
├── .env.example            # 环境变量模板
├── pyproject.toml          # 依赖配置
└── README.md               # 本文件
\`\`\`

## 数据流

\`\`\`
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  数据源      │ ──→ │  处理服务    │ ──→ │  JSON 文件   │
│ (API/爬虫)   │     │ (计算/转换)  │     │  (data/)    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  前端页面    │ ←── │  API 接口    │ ←── │  读取 JSON   │
│ (frontend/) │     │ (/api/xxx)  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
\`\`\`

**数据流说明：**
1. **数据采集**：描述数据从哪里来
2. **数据处理**：描述如何处理/计算
3. **数据存储**：描述存储格式和位置
4. **数据展示**：描述 API 如何返回、前端如何展示

## 环境变量

| 变量名 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| XXX_PORT | 服务端口 | 否 | 5001 |
| XXX_API_KEY | API 密钥 | 是 | - |

## 本地开发

\`\`\`bash
cd projects/your_project
cp .env.example .env
# 编辑 .env 填入配置
uv sync
uv run python -m backend.main
\`\`\`

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| GET | /api/xxx | 获取数据 |
\`\`\`

---

## 添加新项目（4步）

### 步骤 1：创建项目目录

```bash
mkdir -p projects/your_project/{backend,frontend,scripts,docs}
# 把你的代码放进去
```

### 步骤 2：创建部署脚本

创建 `projects/your_project/scripts/deploy.sh`：

```bash
#!/bin/bash
set -e

# 日志函数（自包含，不依赖外部库）
log_info()  { echo -e "\033[0;34m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[0;32m[SUCCESS]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; }

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log_info "=========================================="
log_info "Your Project 部署脚本"
log_info "=========================================="

cd "$PROJECT_DIR"

# 加载环境变量
if [ -f .env ]; then
    set -a && source .env && set +a
fi

# 安装依赖
uv sync

# 启动服务
uv run gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:5001 backend.main:app

log_success "部署完成"
```

```bash
chmod +x projects/your_project/scripts/deploy.sh
```

### 步骤 3：创建环境变量模板

创建 `projects/your_project/.env.example`：

```bash
# 服务配置
YOUR_PROJECT_PORT=5001

# API 密钥（必填）
YOUR_API_KEY=
```

### 步骤 4：提交 PR

完成以上步骤后，提交 Pull Request 即可。

> **注意**：如果需要在首页展示你的项目，请同时编辑 `index.html`，在项目卡片区域添加你的项目卡片。

---

## 环境变量说明

### 两类环境变量

| 文件位置 | 用途 | 谁维护 |
|----------|------|--------|
| `/.env` | **平台级配置**：Nginx 路径、端口扫描等 | 运维人员 |
| `/projects/<project>/.env` | **项目运行时配置**：API 密钥、数据库等 | 项目开发者 |

> **注意**：根目录的 `.env` 与子项目运行时无关。每个项目在自己目录维护 `.env`。

---

## 常见问题

### Q: 如何单独启动某个项目？
```bash
cd projects/your_project
./scripts/deploy.sh
```

### Q: 端口冲突怎么办？
查看其他项目的 `.env` 文件或 `deploy.sh` 中已分配的端口，选择未使用的端口。

### Q: 健康检查接口怎么写？
提供 `/api/health` 接口返回 `{"status": "ok"}`。

---

## 附录：部署脚本模板

完整的部署脚本模板，包含环境检查、依赖安装、服务启动：

```bash
#!/bin/bash
# 部署脚本模板 - 自包含版本
set -e

# ============================================
# 日志函数（自包含，不依赖外部库）
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================
# 环境变量检查函数
# ============================================
require_env() {
    local var_name="$1"
    local description="$2"
    local default_value="$3"

    if [ -n "${!var_name}" ]; then
        log_info "$var_name = ${!var_name}"
        return 0
    fi

    if [ -n "$default_value" ]; then
        export "$var_name"="$default_value"
        log_info "$var_name = $default_value (默认值)"
    else
        log_error "$var_name ($description) 未设置"
        exit 1
    fi
}

# ============================================
# 主逻辑
# ============================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="your_project"  # 修改为你的项目名

log_info "=========================================="
log_info "$PROJECT_NAME 部署脚本"
log_info "=========================================="

cd "$PROJECT_DIR"

# 1. 加载环境变量
if [ -f .env ]; then
    log_info "加载 .env 文件"
    set -a && source .env && set +a
else
    log_warn "未找到 .env 文件"
fi

# 2. 检查必要的环境变量
require_env "YOUR_PROJECT_PORT" "服务端口" "5001"
require_env "YOUR_API_KEY" "API密钥"  # 无默认值=必填

# 3. 检查依赖
if ! command -v uv &> /dev/null; then
    log_error "未找到 uv，请先安装: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 4. 安装依赖
log_info "安装依赖..."
uv sync

# 5. 启动服务
log_info "启动服务..."
uv run gunicorn -w 2 -k uvicorn.workers.UvicornWorker \
    -b 127.0.0.1:${YOUR_PROJECT_PORT} \
    backend.main:app

log_success "=========================================="
log_success "$PROJECT_NAME 部署完成"
log_success "=========================================="
```

---

## 联系方式

有问题可以在 GitHub 提 Issue。
