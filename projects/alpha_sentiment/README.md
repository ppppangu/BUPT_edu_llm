# AlphaSenti - 股票情绪分析终端

基于 AkShare + DeepSeek API 的 A 股情绪分析工具。

## 架构说明

采用 **FastAPI 后端服务** 架构：

```
FastAPI 服务 (内置定时任务) → 生成静态数据 → API 提供数据 → 前端展示
```

**特点**：
- 统一的 API 接口（`/api/`）
- 内置 APScheduler 定时任务（每日 15:30 自动刷新）
- Docker 健康检查支持
- 支持多项目 Nginx 反向代理聚合

## 功能特性

- 热门股票排行榜（东方财经热度数据）
- K 线数据（AkShare 实时获取）
- AI 情绪分析（DeepSeek API）
- 每日收盘后自动更新（15:30）
- 原子性数据写入（确保数据一致性）

## 快速开始

### 1. 安装依赖

```bash
cd projects/alpha_sentiment
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
DEEPSEEK_API_KEY=your_api_key_here
```

### 3. 启动服务

```bash
python -m backend.main
```

服务启动后：
- 前端页面：http://127.0.0.1:5001
- API 文档：http://127.0.0.1:5001/api/docs
- 健康检查：http://127.0.0.1:5001/api/health

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查（含数据状态） |
| `/api/hot_stocks` | GET | 获取热门股票列表 |
| `/api/stock/{code}` | GET | 获取股票详情 |
| `/api/refresh` | POST | 手动触发数据刷新 |
| `/api/docs` | GET | Swagger API 文档 |

## 数据来源

| 数据 | 来源 | 接口 |
|------|------|------|
| 热门排名 | AkShare | `stock_hot_rank_em` |
| 实时价格 | AkShare | `stock_zh_a_spot` |
| K 线数据 | AkShare | `stock_zh_a_daily` |
| 新闻数据 | AkShare | `stock_news_main_cx` |
| 千股千评 | AkShare | `stock_comment_em` |
| 情绪分析 | DeepSeek | AI 新闻情感分析 |

## 定时任务

服务内置 APScheduler 定时任务，**每日 15:30（收盘后）自动刷新数据**。

无需配置操作系统级别的 crontab，启动服务即可自动运行。

## 目录结构

```
alpha_sentiment/
├── backend/                # 后端模块
│   ├── services/
│   │   ├── data_fetcher.py     # 数据获取（AkShare）
│   │   ├── data_generator.py   # 数据生成（聚合服务）
│   │   └── sentiment.py        # AI情绪分析（DeepSeek）
│   ├── models/
│   │   └── schemas.py          # Pydantic 数据模型
│   ├── scheduler.py        # 定时任务（APScheduler）
│   ├── main.py             # FastAPI 入口
│   └── config.py           # 配置管理
├── frontend/               # 前端静态文件
│   └── index.html
├── data/                   # 静态数据目录
│   ├── hot_stocks.json         # 热门股票列表
│   └── stock_*.json            # 股票详情
├── tests/                  # 测试目录
├── pyproject.toml          # 项目配置
└── .env                    # 环境配置
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | - |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | https://api.deepseek.com |
| `ALPHA_SENTIMENT_MAX_HOT_STOCKS` | 热门股票数量 | 20 |
| `ALPHA_SENTIMENT_HOST` | 服务监听地址 | 127.0.0.1 |
| `ALPHA_SENTIMENT_PORT` | 服务监听端口 | 5001 |
| `ALPHA_SENTIMENT_LOG_LEVEL` | 日志级别 | INFO |
| `ALPHA_SENTIMENT_MAX_RETRIES` | 最大重试次数 | 5 |
| `ALPHA_SENTIMENT_RETRY_DELAY` | 重试延迟(秒) | 2.0 |
| `ALPHA_SENTIMENT_ALERT_WEBHOOK` | 告警 Webhook URL | - |

## 告警配置

支持通过 Webhook 发送告警通知（钉钉/飞书/企业微信等）。

```env
ALPHA_SENTIMENT_ALERT_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
```

## Docker 部署

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 5001
HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:5001/api/health || exit 1
CMD ["python", "-m", "backend.main"]
```

## Nginx 反向代理

多项目聚合时的路由格式：

```
域名/alpha_sentiment/          → 前端页面
域名/alpha_sentiment/api/xxx   → API 接口
```

详见根目录 `nginx.conf` 配置。

## 命令行工具

```bash
# 启动服务（含定时任务）
python -m backend.main

# 手动生成数据
python -m backend.services.data_generator --run

# 删除所有数据
python -m backend.services.data_generator --delete
```
