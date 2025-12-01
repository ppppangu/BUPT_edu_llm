# GCP + Cloudflare 服务器配置指南

本文档介绍如何从零开始在 Google Cloud Platform (GCP) 上部署服务器，并配置 Cloudflare CDN 和 SSL。

## 目录

- [前置准备](#前置准备)
- [GCP 虚拟机创建](#gcp-虚拟机创建)
- [GCP 防火墙配置](#gcp-防火墙配置)
- [服务器环境配置](#服务器环境配置)
- [Cloudflare 配置](#cloudflare-配置)
- [SSL 证书配置](#ssl-证书配置)
- [Nginx 配置](#nginx-配置)
- [常见问题排查](#常见问题排查)

## 前置准备

### 所需账号

- Google Cloud Platform 账号（需绑定付款方式）
- Cloudflare 账号（免费版即可）
- 已注册的域名

### 安装 gcloud CLI

**Windows:**
```powershell
# 下载安装包
https://cloud.google.com/sdk/docs/install

# 或使用 winget
winget install Google.CloudSDK
```

**macOS:**
```bash
brew install --cask google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**初始化 gcloud:**
```bash
gcloud init
gcloud auth login
```

## GCP 虚拟机创建

### 1. 创建 VM 实例

```bash
gcloud compute instances create webserver \
    --zone=us-central1-c \
    --machine-type=e2-medium \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-balanced \
    --tags=http-server,https-server
```

参数说明：
- `--zone`: 选择离用户较近的区域
- `--machine-type`: e2-medium (2 vCPU, 4GB 内存) 适合中小型应用
- `--tags`: 网络标签，用于防火墙规则匹配

### 2. 查看实例信息

```bash
# 列出所有实例
gcloud compute instances list

# 输出示例：
# NAME       ZONE           MACHINE_TYPE  EXTERNAL_IP     STATUS
# webserver  us-central1-c  e2-medium     34.135.224.149  RUNNING
```

### 3. SSH 连接到实例

```bash
gcloud compute ssh webserver --zone=us-central1-c
```

## GCP 防火墙配置

### 1. 查看现有防火墙规则

```bash
gcloud compute firewall-rules list
```

### 2. 创建 HTTP/HTTPS 防火墙规则

GCP 默认有 `default-allow-http` 和 `default-allow-https` 规则，但需要 VM 实例带有对应标签才能生效。

**方法 A: 给实例添加标签（推荐）**

```bash
gcloud compute instances add-tags webserver \
    --zone=us-central1-c \
    --tags=http-server,https-server
```

**方法 B: 创建新的防火墙规则**

```bash
# 允许 HTTP
gcloud compute firewall-rules create allow-http \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:80 \
    --source-ranges=0.0.0.0/0

# 允许 HTTPS
gcloud compute firewall-rules create allow-https \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:443 \
    --source-ranges=0.0.0.0/0
```

### 3. 验证防火墙规则

```bash
# 查看规则详情
gcloud compute firewall-rules describe default-allow-http

# 查看规则的目标标签
gcloud compute firewall-rules describe default-allow-http --format="get(targetTags)"
```

## 服务器环境配置

SSH 连接到服务器后执行以下命令：

### 1. 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 安装必要软件

```bash
sudo apt install -y nginx git curl wget vim
```

### 3. 启动 Nginx

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

### 4. 验证 Nginx 运行

```bash
# 本地测试
curl -I http://127.0.0.1/

# 检查端口监听
sudo netstat -tlnp | grep -E ':80|:443'
```

## Cloudflare 配置

### 1. 添加域名到 Cloudflare

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 点击 "Add a Site"
3. 输入域名（如 `edubeam.cn`）
4. 选择计划（Free 即可）
5. Cloudflare 会扫描现有 DNS 记录

### 2. 修改域名 NS 服务器

在域名注册商处，将 NS 服务器修改为 Cloudflare 提供的地址，例如：
- `anna.ns.cloudflare.com`
- `bob.ns.cloudflare.com`

### 3. 配置 DNS 记录

在 Cloudflare DNS 设置中添加 A 记录：

| Type | Name | Content | Proxy status |
|------|------|---------|--------------|
| A | @ | 34.135.224.149 | Proxied (橙色云朵) |
| A | www | 34.135.224.149 | Proxied (橙色云朵) |

**重要**: 确保云朵图标是**橙色**（Proxied），这样流量才会经过 Cloudflare。

### 4. 配置 SSL/TLS 模式

1. 进入 **SSL/TLS** → **Overview**
2. 选择 **Full (Strict)** 模式

SSL 模式说明：
- **Off**: 不加密（不推荐）
- **Flexible**: Cloudflare 到源站使用 HTTP（会导致重定向循环）
- **Full**: Cloudflare 到源站使用 HTTPS，但不验证证书
- **Full (Strict)**: Cloudflare 到源站使用 HTTPS，并验证证书（推荐）

## SSL 证书配置

### 方式一：使用 Cloudflare Origin 证书（推荐）

Origin 证书由 Cloudflare 签发，仅在 Cloudflare 代理模式下有效，有效期最长 15 年。

**1. 生成 Origin 证书**

1. 在 Cloudflare 进入 **SSL/TLS** → **Origin Server**
2. 点击 **Create Certificate**
3. 选择：
   - Private key type: RSA (2048)
   - Hostnames: `edubeam.cn`, `*.edubeam.cn`
   - Certificate Validity: 15 years
4. 点击 **Create**
5. 复制 Origin Certificate 和 Private Key

**2. 在服务器上配置证书**

```bash
# 创建 SSL 目录
sudo mkdir -p /etc/nginx/ssl

# 创建证书文件
sudo vim /etc/nginx/ssl/edubeam.cn.pem
# 粘贴 Origin Certificate 内容

sudo vim /etc/nginx/ssl/edubeam.cn.key
# 粘贴 Private Key 内容

# 设置权限
sudo chmod 644 /etc/nginx/ssl/edubeam.cn.pem
sudo chmod 600 /etc/nginx/ssl/edubeam.cn.key
```

### 方式二：使用 Let's Encrypt 证书

如果不使用 Cloudflare 代理（灰色云朵），需要使用公共 CA 证书：

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书（确保域名已解析到服务器且 80 端口开放）
sudo certbot --nginx -d edubeam.cn -d www.edubeam.cn

# 测试自动续期
sudo certbot renew --dry-run
```

## Nginx 配置

### 完整配置示例

创建 `/etc/nginx/conf.d/edubeam.conf`:

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name edubeam.cn www.edubeam.cn;
    return 301 https://edubeam.cn$request_uri;
}

# HTTPS 主配置
server {
    listen 443 ssl http2;
    server_name edubeam.cn www.edubeam.cn;

    # 日志
    access_log /var/log/nginx/edubeam_access.log;
    error_log /var/log/nginx/edubeam_error.log;

    # SSL 证书
    ssl_certificate /etc/nginx/ssl/edubeam.cn.pem;
    ssl_certificate_key /etc/nginx/ssl/edubeam.cn.key;

    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # 网站根目录
    location / {
        root /data/BUPT_edu_llm;
        index index.html;
        try_files $uri $uri/ /index.html;

        # 静态资源缓存
        location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 反向代理示例
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 错误页面
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
}
```

### 测试并重载配置

```bash
# 测试配置语法
sudo nginx -t

# 重载配置
sudo systemctl reload nginx
```

## 常见问题排查

### 522 Connection Timed Out

**原因**: Cloudflare 无法连接到源服务器

**排查步骤**:

1. **检查 GCP 防火墙**
   ```bash
   gcloud compute firewall-rules list --filter="allowed[].ports:80 OR allowed[].ports:443"
   ```

2. **检查实例网络标签**
   ```bash
   gcloud compute instances describe webserver --zone=us-central1-c --format="get(tags.items)"
   ```
   确保有 `http-server` 和 `https-server` 标签

3. **添加缺失的标签**
   ```bash
   gcloud compute instances add-tags webserver --zone=us-central1-c --tags=http-server,https-server
   ```

4. **从外部测试连接**
   ```bash
   curl -I http://<服务器公网IP>/ --connect-timeout 5
   ```

### 重定向循环 (ERR_TOO_MANY_REDIRECTS)

**原因**: Cloudflare SSL 模式设置为 Flexible，而 Nginx 配置了 HTTP 到 HTTPS 重定向

**解决方案**:
1. 登录 Cloudflare Dashboard
2. 进入 **SSL/TLS** → **Overview**
3. 将模式改为 **Full** 或 **Full (Strict)**

### 525 SSL Handshake Failed

**原因**: Cloudflare 无法与源服务器建立 SSL 连接

**排查步骤**:

1. **检查证书文件是否存在**
   ```bash
   ls -la /etc/nginx/ssl/
   ```

2. **验证证书有效性**
   ```bash
   openssl x509 -in /etc/nginx/ssl/edubeam.cn.pem -noout -dates
   ```

3. **检查 Nginx SSL 配置**
   ```bash
   nginx -t
   ```

### 526 Invalid SSL Certificate

**原因**: 使用了无效的 SSL 证书（如自签名证书）且 SSL 模式为 Full (Strict)

**解决方案**:
- 使用 Cloudflare Origin 证书
- 或将 SSL 模式改为 Full（不验证证书）

## 快速检查清单

部署完成后，按以下顺序验证：

```bash
# 1. 检查 Nginx 运行状态
sudo systemctl status nginx

# 2. 检查端口监听
sudo netstat -tlnp | grep -E ':80|:443'

# 3. 本地 HTTP 测试
curl -I http://127.0.0.1/ -H "Host: edubeam.cn"

# 4. 本地 HTTPS 测试
curl -I -k https://127.0.0.1/ -H "Host: edubeam.cn"

# 5. DNS 解析检查
host edubeam.cn

# 6. 外部访问测试
curl -I https://edubeam.cn/
```

## 参考链接

- [GCP Compute Engine 文档](https://cloud.google.com/compute/docs)
- [gcloud CLI 参考](https://cloud.google.com/sdk/gcloud/reference)
- [Cloudflare SSL/TLS 文档](https://developers.cloudflare.com/ssl/)
- [Nginx 官方文档](https://nginx.org/en/docs/)
