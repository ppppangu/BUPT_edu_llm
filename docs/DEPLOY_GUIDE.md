# BUPT EDU LLM Platform - 部署指南

本文档提供了 BUPT EDU LLM 平台的详细部署指南，涵盖开发环境和生产环境的配置。

## 目录

- [系统要求](#系统要求)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Nginx 配置](#nginx-配置)
- [服务管理](#服务管理)
- [故障排查](#故障排查)

## 系统要求

### 硬件要求

- CPU: 2核以上
- 内存: 4GB 以上
- 磁盘: 20GB 以上可用空间

### 软件要求

- 操作系统: Ubuntu 20.04+ / CentOS 8+ / Windows 10+ (with WSL2)
- Python: 3.12 或更高版本
- Nginx: 1.18 或更高版本
- Git: 2.25 或更高版本

## 开发环境部署

### 1. 克隆仓库

```bash
git clone <your-repository-url>
cd BUPT_edu_llm
```

### 2. 安装 Python 依赖

推荐使用 `uv` 进行依赖管理：

```bash
# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync
```

或使用传统的 pip：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用你喜欢的编辑器
```

关键配置项：

```env
PLATFORM_ENV=development
SOLAR_NEWS_PORT=5000
SOLAR_NEWS_ENABLED=true
DEBUG=true
```

### 4. 启动开发服务器

```bash
# 方式 1: 使用启动脚本
chmod +x scripts/*.sh
./scripts/start_all.sh

# 方式 2: 手动启动各服务
cd solar_news_crawler/solar_news_crawler
python app.py
```

### 5. 访问应用

- Landing Page: http://localhost/
- Solar News Crawler: http://localhost:5000/

## 生产环境部署

### 1. 服务器准备

更新系统并安装必要软件：

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.12 python3.12-venv nginx git build-essential python-is-python3

# CentOS/RHEL
sudo yum update
sudo yum install -y python3.12 python3.12-devel nginx git gcc
```

### 2. 创建部署用户

```bash
sudo useradd -m -s /bin/bash bupt_llm
sudo su - bupt_llm
```

### 3. 部署代码

```bash
cd ~
git clone <your-repository-url> BUPT_edu_llm
cd BUPT_edu_llm

# 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
nano .env
```

生产环境配置示例：

```env
PLATFORM_ENV=production
PLATFORM_VERSION=0.1.0

# Solar News Crawler
SOLAR_NEWS_ENABLED=true
SOLAR_NEWS_PORT=5000
SOLAR_NEWS_WORKERS=4

# Security
DEBUG=false
SECRET_KEY=<generate-a-random-secret-key>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_DIR=/home/bupt_llm/BUPT_edu_llm/logs
```

### 5. 创建 Systemd 服务

#### Solar News Crawler 服务

创建 `/etc/systemd/system/solar-news-crawler.service`:

```ini
[Unit]
Description=Solar News Crawler Service
After=network.target

[Service]
Type=simple
User=bupt_llm
Group=bupt_llm
WorkingDirectory=/home/bupt_llm/BUPT_edu_llm/solar_news_crawler/solar_news_crawler
Environment="PATH=/home/bupt_llm/BUPT_edu_llm/.venv/bin"
ExecStart=/home/bupt_llm/BUPT_edu_llm/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable solar-news-crawler
sudo systemctl start solar-news-crawler
sudo systemctl status solar-news-crawler
```

## Nginx 配置

### 1. 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS/RHEL
sudo yum install -y nginx
```

### 2. 配置反向代理

复制项目配置文件：

```bash
sudo cp /home/bupt_llm/BUPT_edu_llm/nginx/bupt_edu_llm.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/bupt_edu_llm.conf /etc/nginx/sites-enabled/
```

编辑配置文件，更新路径：

```bash
sudo nano /etc/nginx/sites-available/bupt_edu_llm.conf
```

需要修改的地方：

```nginx
# Landing Page 路径
location / {
    root /home/bupt_llm/BUPT_edu_llm/landingpage;
    # ...
}

# 域名（生产环境）
server_name your-domain.com www.your-domain.com;
```

### 3. 测试并重启 Nginx

```bash
# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 4. 配置 SSL (可选但推荐)

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

## 服务管理

### 查看服务状态

```bash
# 查看所有服务状态
python /home/bupt_llm/BUPT_edu_llm/scripts/health_check.py

# 查看 Systemd 服务状态
sudo systemctl status solar-news-crawler
sudo systemctl status nginx
```

### 查看日志

```bash
# 应用日志
tail -f /home/bupt_llm/BUPT_edu_llm/logs/solar_news_crawler.log

# Systemd 日志
sudo journalctl -u solar-news-crawler -f

# Nginx 日志
sudo tail -f /var/log/nginx/bupt_edu_llm_access.log
sudo tail -f /var/log/nginx/bupt_edu_llm_error.log
```

### 重启服务

```bash
# 重启 Solar News Crawler
sudo systemctl restart solar-news-crawler

# 重启 Nginx
sudo systemctl restart nginx

# 或使用脚本
/home/bupt_llm/BUPT_edu_llm/scripts/stop_all.sh
/home/bupt_llm/BUPT_edu_llm/scripts/start_all.sh
```

## 定时任务配置

为 Solar News Crawler 配置定时爬虫任务：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 2 点运行爬虫）
0 2 * * * cd /home/bupt_llm/BUPT_edu_llm/solar_news_crawler/solar_news_crawler && /home/bupt_llm/BUPT_edu_llm/.venv/bin/python master_crawler.py daily >> /home/bupt_llm/BUPT_edu_llm/logs/crawler_cron.log 2>&1

# 每天凌晨 3 点运行翻译
0 3 * * * cd /home/bupt_llm/BUPT_edu_llm/solar_news_crawler/solar_news_crawler && /home/bupt_llm/BUPT_edu_llm/.venv/bin/python translator.py >> /home/bupt_llm/BUPT_edu_llm/logs/translator_cron.log 2>&1
```

## 故障排查

### 1. 服务无法启动

**检查端口占用**：

```bash
sudo lsof -i :5000
sudo netstat -tulpn | grep 5000
```

**检查权限**：

```bash
ls -la /home/bupt_llm/BUPT_edu_llm
sudo chown -R bupt_llm:bupt_llm /home/bupt_llm/BUPT_edu_llm
```

### 2. Nginx 502 Bad Gateway

**检查后端服务是否运行**：

```bash
sudo systemctl status solar-news-crawler
curl http://127.0.0.1:5000
```

**检查 Nginx 配置**：

```bash
sudo nginx -t
cat /var/log/nginx/bupt_edu_llm_error.log
```

### 3. 权限问题

**SELinux 相关（CentOS/RHEL）**：

```bash
# 临时禁用
sudo setenforce 0

# 永久禁用（不推荐，建议配置 SELinux 策略）
sudo nano /etc/selinux/config
# 设置 SELINUX=disabled
```

**防火墙配置**：

```bash
# Ubuntu (UFW)
sudo ufw allow 80
sudo ufw allow 443

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 4. 数据库连接问题

检查数据库文件权限：

```bash
ls -la /home/bupt_llm/BUPT_edu_llm/solar_news_crawler/solar_news_crawler/*.db
```

### 5. 内存不足

**增加 swap 空间**：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 性能优化

### 1. Gunicorn 优化

调整 worker 数量（建议：CPU 核心数 × 2 + 1）：

```bash
# 在 systemd 服务文件中
ExecStart=/path/to/.venv/bin/gunicorn -w 8 -b 127.0.0.1:5000 app:app
```

### 2. Nginx 缓存优化

在 Nginx 配置中添加：

```nginx
# 启用缓存
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;

location /solar_news/ {
    proxy_cache my_cache;
    proxy_cache_valid 200 1h;
    # ...
}
```

### 3. 数据库优化

定期清理旧数据，优化数据库：

```bash
# 添加到 crontab
0 4 * * 0 cd /path/to/solar_news_crawler && python cleanup_old_data.py
```

## 监控与告警

### 1. 使用健康检查脚本

```bash
# 添加到 crontab，每 5 分钟检查一次
*/5 * * * * /home/bupt_llm/BUPT_edu_llm/scripts/health_check.py --json > /home/bupt_llm/BUPT_edu_llm/logs/health_check.json
```

### 2. 日志轮转

创建 `/etc/logrotate.d/bupt_edu_llm`:

```
/home/bupt_llm/BUPT_edu_llm/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 bupt_llm bupt_llm
}
```

## 备份策略

### 1. 数据库备份

```bash
#!/bin/bash
# 添加到 crontab: 0 5 * * * /home/bupt_llm/backup.sh

BACKUP_DIR="/home/bupt_llm/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp /home/bupt_llm/BUPT_edu_llm/solar_news_crawler/solar_news_crawler/*.db $BACKUP_DIR/db_backup_$DATE.db

# 删除 30 天前的备份
find $BACKUP_DIR -name "db_backup_*.db" -mtime +30 -delete
```

### 2. 配置文件备份

```bash
tar -czf ~/config_backup_$(date +%Y%m%d).tar.gz \
    /home/bupt_llm/BUPT_edu_llm/.env \
    /etc/nginx/sites-available/bupt_edu_llm.conf \
    /etc/systemd/system/solar-news-crawler.service
```

## 安全建议

1. **定期更新系统和依赖包**
2. **使用强密码和密钥**
3. **启用防火墙**
4. **配置 SSL/TLS**
5. **定期备份数据**
6. **监控系统日志**
7. **限制 SSH 访问**
8. **使用非 root 用户运行服务**

## 参考资源

- [Nginx 官方文档](https://nginx.org/en/docs/)
- [Gunicorn 文档](https://docs.gunicorn.org/)
- [Systemd 文档](https://www.freedesktop.org/software/systemd/man/)
- [Let's Encrypt](https://letsencrypt.org/)

## 联系支持

如遇问题，请通过以下方式获取支持：

- GitHub Issues: [Your Repository Issues URL]
- Email: your-email@example.com
