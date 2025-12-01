# 部署文档

## 环境要求

- Python 3.8+
- uv (推荐) 或 pip
- Chrome/Chromium 浏览器（用于 selenium 爬虫）
- ChromeDriver（会自动下载）

## 部署步骤

### 1. 安装系统依赖（Linux）

**Ubuntu/Debian:**
```bash
# 安装 Python 和 Chrome
sudo apt update
sudo apt install -y python3 python3-pip

# 安装 Chrome 浏览器（用于 selenium）
sudo apt install -y chromium-browser chromium-chromedriver
```

**安装 uv (推荐):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 克隆项目

```bash
git clone <repository_url>
cd BUPT_edu_llm/projects/solar_news_crawler
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入配置
```

### 4. 安装依赖

```bash
uv sync
```

### 5. 运行服务

#### 开发模式

```bash
uv run python -m backend.main
```

#### 生产模式

使用部署脚本：
```bash
./scripts/deploy.sh
```

或手动启动：
```bash
uv run uvicorn backend.main:app \
    --host 127.0.0.1 \
    --port 5000 \
    --workers 2 \
    --log-level info
```

### 6. 访问应用

- 前端页面：`http://127.0.0.1:5000/`
- 健康检查：`http://127.0.0.1:5000/api/health`
- API 文档：`http://127.0.0.1:5000/api/docs`

## 使用 Nginx 反向代理（可选）

如果需要通过域名访问，创建配置文件 `/etc/nginx/sites-available/solar-news`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location /solar_news_crawler/ {
        alias /path/to/BUPT_edu_llm/projects/solar_news_crawler/frontend/;
        try_files $uri $uri/ @backend;
    }

    # API 请求
    location /solar_news_crawler/api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location @backend {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/solar-news /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                      部署架构 (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Uvicorn (ASGI)                      │   │
│  │                    (N workers)                        │   │
│  └──────────────────────────┬───────────────────────────┘   │
│                             │                                │
│                             ▼                                │
│     ┌─────────────────────────────────────────────────┐     │
│     │                 FastAPI 应用                     │     │
│     │                                                  │     │
│     │  ┌────────────┐  ┌────────────┐  ┌────────────┐ │     │
│     │  │ API 路由   │  │ 静态文件   │  │ 页面路由   │ │     │
│     │  │ /api/*     │  │ /static/*  │  │ /, /news.. │ │     │
│     │  └────────────┘  └────────────┘  └────────────┘ │     │
│     │                                                  │     │
│     │  ┌────────────────────────────────────────────┐ │     │
│     │  │          APScheduler (进程内)              │ │     │
│     │  │      每日凌晨执行：爬虫 → 翻译 → AI总结    │ │     │
│     │  └────────────────────────────────────────────┘ │     │
│     └─────────────────────────────────────────────────┘     │
│                             │                                │
│                             ▼                                │
│     ┌─────────────────────────────────────────────────┐     │
│     │               data/ 目录 (JSON 文件)            │     │
│     └─────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**架构特点：**

- **单进程部署**：uvicorn 直接启动，内置 APScheduler，无需额外进程
- **简洁高效**：不依赖 gunicorn，配置更少
- **自动调度**：定时任务随应用启动/停止，无需 systemd 或 cron

## 环境变量

| 变量名 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| SOLAR_NEWS_HOST | 服务绑定地址 | 否 | 127.0.0.1 |
| SOLAR_NEWS_PORT | 服务端口 | 否 | 5000 |
| SOLAR_NEWS_WORKERS | 工作进程数 | 否 | 2 |
| SCHEDULER_HOUR | 定时任务执行小时 | 否 | 2 |
| SCHEDULER_MINUTE | 定时任务执行分钟 | 否 | 0 |
| LLM_BASE_URL | LLM API 地址 | 否 | - |
| LLM_API_KEY | LLM API 密钥 | 否 | - |
| LLM_MODEL | LLM 模型名称 | 否 | gpt-3.5-turbo |

## 注意事项

1. **文件权限**：确保 `data/` 目录有写入权限
2. **Worker 数量**：建议设置为 `(2 × CPU核心数) + 1`
3. **AI 功能**：如需 AI 总结功能，需配置 `LLM_API_KEY` 和 `LLM_BASE_URL`
4. **定时任务**：默认每天凌晨 2:00 执行数据更新

## 故障排除

### 服务无法启动

```bash
# 检查端口是否被占用
lsof -i :5000

# 查看详细日志
uv run python -m backend.main
```

### 爬虫执行失败

```bash
# 检查 Chrome 是否安装
which chromium-browser || which google-chrome

# 检查 data 目录权限
ls -la data/
```

### API 返回 500 错误

```bash
# 直接运行查看错误信息
uv run python -m backend.main
```
