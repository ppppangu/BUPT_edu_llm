# Solar News Crawler

多来源光伏行业新闻爬虫与资讯聚合平台，自动采集国内外权威信息源，提供翻译和 AI 总结功能。

## 项目结构

```
solar_news_crawler/
├── backend/                     # 后端服务
│   ├── main.py                 # Flask 入口，定义 API 路由
│   ├── config.py               # 配置管理，读取环境变量
│   ├── scheduler.py            # APScheduler 定时任务
│   └── services/               # 业务逻辑层
│       ├── news_service.py     # 新闻数据读取服务
│       ├── crawler_service.py  # 爬虫调度服务
│       ├── translator_service.py # 翻译服务
│       └── ai_service.py       # AI 总结服务
├── crawlers/                    # 爬虫脚本
│   ├── combined_crawler.py     # 国内新闻爬虫（政府网+能源局）
│   ├── iea_crawler.py          # IEA 新闻爬虫
│   ├── irena_crawler.py        # IRENA 新闻爬虫
│   └── pv_magazine_crawler.py  # PV Magazine 爬虫
├── frontend/                    # 前端页面
│   ├── index.html              # 主页
│   ├── news_search.html        # 国内新闻页
│   └── translated_news.html    # 国际新闻页
├── data/                        # 数据存储目录
│   ├── combined_*.json         # 国内新闻数据
│   ├── translator_*.json       # 翻译后的国际新闻
│   ├── summary_domestic.json   # 国内新闻 AI 总结
│   └── summary_international.json # 国际新闻 AI 总结
├── scripts/
│   └── deploy.sh               # 部署脚本
├── .env.example                 # 环境变量模板
├── pyproject.toml               # 依赖配置
└── README.md                    # 本文件
```

## 数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                        定时任务 (每日凌晨)                        │
│                      backend/scheduler.py                       │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 国内爬虫      │  │ IEA 爬虫     │  │ IRENA 爬虫   │  │ PV Magazine  │
│ combined     │  │              │  │              │  │ 爬虫         │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       ↓                 ↓                 ↓                 ↓
┌──────────────┐  ┌─────────────────────────────────────────────────┐
│ combined_    │  │              翻译服务                            │
│ *.json       │  │         translator_service.py                   │
└──────────────┘  └──────────────────────┬──────────────────────────┘
       │                                 │
       │                                 ↓
       │                          ┌──────────────┐
       │                          │ translator_  │
       │                          │ *.json       │
       │                          └──────────────┘
       │                                 │
       ↓                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                     AI 总结服务 (ai_service.py)                  │
└─────────────────────────────────────────────────────────────────┘
       │                                 │
       ↓                                 ↓
┌──────────────┐                  ┌──────────────┐
│ summary_     │                  │ summary_     │
│ domestic.json│                  │ international│
└──────────────┘                  └──────────────┘
       │                                 │
       └─────────────┬───────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                  news_service.py (读取 JSON)                     │
└─────────────────────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API 层 (main.py)                           │
│  /api/news  /api/international  /api/summary/<type>             │
└─────────────────────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                    前端页面 (frontend/)                          │
└─────────────────────────────────────────────────────────────────┘
```

**数据流说明：**

1. **数据采集**：定时任务每日凌晨触发，运行 4 个爬虫脚本
2. **数据处理**：国际新闻经过翻译服务转换为中文
3. **AI 总结**：调用 LLM API 生成每日新闻简报
4. **数据存储**：所有数据以 JSON 格式存储在 `data/` 目录
5. **数据展示**：API 层读取 JSON 文件返回给前端

## 环境变量

| 变量名 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| SOLAR_NEWS_HOST | 服务绑定地址 | 否 | 127.0.0.1 |
| SOLAR_NEWS_PORT | 服务端口 | 否 | 5000 |
| SOLAR_NEWS_WORKERS | 工作进程数 | 否 | 4 |
| SCHEDULER_HOUR | 定时任务执行小时 | 否 | 2 |
| SCHEDULER_MINUTE | 定时任务执行分钟 | 否 | 0 |
| LLM_BASE_URL | LLM API 地址 | 否 | - |
| LLM_API_KEY | LLM API 密钥 | 否 | - |
| LLM_MODEL | LLM 模型名称 | 否 | gpt-3.5-turbo |

## 本地开发

```bash
cd projects/solar_news_crawler
cp .env.example .env
# 编辑 .env 填入配置（AI 功能需要配置 API Key）
uv sync
uv run python -m backend.main
```

访问 http://127.0.0.1:5000

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| GET | /api/news | 获取国内新闻（支持筛选） |
| GET | /api/news/stats | 国内新闻统计 |
| GET | /api/international | 获取国际新闻（支持筛选） |
| GET | /api/international/stats | 国际新闻统计 |
| GET | /api/summary/domestic | 国内新闻 AI 总结 |
| GET | /api/summary/international | 国际新闻 AI 总结 |

**筛选参数：**
- `start_date` - 开始日期 (YYYY-MM-DD)
- `end_date` - 结束日期 (YYYY-MM-DD)
- `keyword` - 关键词
- `source` - 数据来源

## 部署

```bash
./scripts/deploy.sh
```
