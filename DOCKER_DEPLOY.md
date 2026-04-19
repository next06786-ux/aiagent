# 泽境决策管理系统 - Docker部署指南

## 为什么使用Docker？

✅ **一键部署** - 无需手动配置前后端端口和代理  
✅ **环境隔离** - 避免本地环境冲突  
✅ **统一配置** - 所有服务使用统一的网络和配置  
✅ **易于迁移** - 可以轻松部署到任何服务器  
✅ **自动重启** - 服务异常自动恢复  

## 系统架构

```
┌─────────────────────────────────────────────┐
│  用户浏览器 (http://localhost)              │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│  Nginx (前端 + 反向代理)                    │
│  - 静态文件服务                             │
│  - API代理: /api/* -> backend:6006         │
│  - WebSocket代理: /ws/* -> backend:6006    │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│  Backend (Python FastAPI)                   │
│  - REST API                                 │
│  - WebSocket服务                            │
│  - LLM集成                                  │
└─────┬───────────────────────┬───────────────┘
      │                       │
┌─────▼─────┐         ┌───────▼──────┐
│  MySQL    │         │   Neo4j      │
│  (数据库) │         │  (知识图谱)  │
└───────────┘         └──────────────┘
```

## 前置要求

### Windows
- Docker Desktop for Windows
- 至少4GB可用内存
- 至少10GB可用磁盘空间

### Linux/Mac
- Docker Engine
- Docker Compose
- 至少4GB可用内存
- 至少10GB可用磁盘空间

## 快速开始

### 1. 安装Docker

**Windows:**
1. 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. 安装并启动Docker Desktop
3. 确保WSL2已启用

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.docker .env

# 编辑.env文件，填写必要配置
# 最重要的是 DASHSCOPE_API_KEY
```

### 3. 一键部署

**Windows (PowerShell):**
```powershell
.\deploy.ps1
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### 4. 访问系统

- 前端: http://localhost
- 后端API: http://localhost:6006
- Neo4j浏览器: http://localhost:7474

默认管理员账号:
- 用户名: `admin`
- 密码: `admin123`

## 手动部署步骤

如果自动部署脚本失败，可以手动执行：

```bash
# 1. 停止旧容器
docker-compose down

# 2. 构建镜像
docker-compose build

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 初始化数据库（等待MySQL启动后）
docker-compose exec backend python -c "
from backend.database.models import Database
from backend.database.config import DatabaseConfig
db = Database(DatabaseConfig.get_database_url())
db.init_db()
"

# 6. 创建管理员用户
docker-compose exec backend python init_admin_user.py
```

## 常用命令

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
docker-compose logs -f neo4j
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 停止服务
```bash
docker-compose stop
```

### 完全清理
```bash
# 停止并删除容器、网络
docker-compose down

# 同时删除数据卷（⚠️ 会删除所有数据）
docker-compose down -v
```

### 进入容器
```bash
# 进入后端容器
docker-compose exec backend bash

# 进入MySQL
docker-compose exec mysql mysql -u root -p

# 进入Neo4j
docker-compose exec neo4j cypher-shell -u neo4j -p lifeswarm123
```

## 配置说明

### 端口映射

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|---------|---------|------|
| Frontend | 80 | 80 | 前端Web界面 |
| Backend | 6006 | 6006 | 后端API |
| MySQL | 3306 | 3306 | 数据库 |
| Neo4j HTTP | 7474 | 7474 | Neo4j浏览器 |
| Neo4j Bolt | 7687 | 7687 | Neo4j连接 |

### 数据持久化

数据存储在Docker volumes中：
- `mysql_data`: MySQL数据
- `neo4j_data`: Neo4j数据
- `neo4j_logs`: Neo4j日志
- `./backend/data`: 应用数据（挂载到主机）

### 环境变量

关键环境变量（在`.env`文件中配置）：

```bash
# LLM配置（必填）
DASHSCOPE_API_KEY=your_api_key_here

# 数据库配置（自动配置）
MYSQL_HOST=mysql
MYSQL_PORT=3306
NEO4J_URI=bolt://neo4j:7687

# 应用配置
LIFESWARM_ENV=production
```

## 故障排查

### 1. 容器启动失败

```bash
# 查看详细日志
docker-compose logs backend

# 检查容器状态
docker-compose ps
```

### 2. 数据库连接失败

```bash
# 检查MySQL是否就绪
docker-compose exec mysql mysqladmin ping -h localhost

# 检查Neo4j是否就绪
docker-compose exec neo4j cypher-shell -u neo4j -p lifeswarm123 "RETURN 1"
```

### 3. 前端无法访问后端

检查nginx配置和网络：
```bash
# 查看nginx日志
docker-compose logs frontend

# 测试后端连接
docker-compose exec frontend curl http://backend:6006/health
```

### 4. WebSocket连接失败

检查nginx的WebSocket代理配置：
```bash
# 查看nginx配置
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# 重启nginx
docker-compose restart frontend
```

### 5. 内存不足

如果系统内存不足，可以调整docker-compose.yml中的资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

## 生产环境部署

### 1. 使用域名

修改`nginx.conf`中的`server_name`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    # ...
}
```

### 2. 启用HTTPS

```bash
# 安装certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com
```

### 3. 配置防火墙

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. 设置自动备份

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec mysql mysqldump -u root -p123456 lifeswarm > backup_mysql_$DATE.sql
docker-compose exec neo4j neo4j-admin dump --to=/tmp/neo4j_$DATE.dump
docker cp lifeswarm-neo4j:/tmp/neo4j_$DATE.dump ./backup_neo4j_$DATE.dump
EOF

chmod +x backup.sh

# 添加到crontab（每天凌晨2点备份）
crontab -e
# 添加: 0 2 * * * /path/to/backup.sh
```

## 性能优化

### 1. 调整MySQL配置

编辑`docker-compose.yml`:
```yaml
mysql:
  command:
    - --max_connections=500
    - --innodb_buffer_pool_size=2G
```

### 2. 调整Neo4j内存

```yaml
neo4j:
  environment:
    NEO4J_dbms_memory_heap_max__size: 4G
    NEO4J_dbms_memory_pagecache_size: 2G
```

### 3. 启用Redis缓存

添加Redis服务到`docker-compose.yml`:
```yaml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
```

## 监控和日志

### 1. 查看资源使用

```bash
docker stats
```

### 2. 集中日志管理

使用ELK Stack或Loki进行日志聚合。

### 3. 健康检查

所有服务都配置了健康检查：
```bash
docker-compose ps
# 查看HEALTH列的状态
```

## 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 查看日志确认
docker-compose logs -f
```

## 总结

Docker部署的优势：
- ✅ 无需手动配置Vite代理
- ✅ 无需担心端口冲突
- ✅ 统一的网络环境
- ✅ 一键启动所有服务
- ✅ 易于迁移和扩展

如有问题，请查看日志或提交Issue。
