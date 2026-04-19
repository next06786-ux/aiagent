# 🚀 Docker快速部署指南

## 为什么选择Docker？

✅ **零配置烦恼** - 不用再担心前后端端口、代理配置  
✅ **一键启动** - 所有服务（前端、后端、数据库）一起启动  
✅ **环境隔离** - 不会影响你的本地开发环境  
✅ **易于迁移** - 可以轻松部署到任何服务器  

## 前置要求

### Windows用户
1. 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. 启动Docker Desktop
3. 确保WSL2已启用

### Linux/Mac用户
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 三步部署

### 步骤1: 配置环境变量

```bash
# 复制环境变量模板
cp .env.docker .env

# 编辑.env文件，填写你的API Key
# 最重要的是 DASHSCOPE_API_KEY
```

### 步骤2: 一键部署

**Windows (PowerShell):**
```powershell
.\deploy.ps1
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### 步骤3: 访问系统

打开浏览器访问: **http://localhost**

默认管理员账号:
- 用户名: `admin`
- 密码: `admin123`

## 就这么简单！

部署完成后，你会看到：

```
==========================================
  部署完成！
==========================================

访问地址：
  前端: http://localhost
  后端API: http://localhost:6006
  Neo4j浏览器: http://localhost:7474

默认管理员账号：
  用户名: admin
  密码: admin123
```

## 常用命令

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 只看后端日志
docker-compose logs -f backend

# 只看前端日志
docker-compose logs -f frontend
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 只重启后端
docker-compose restart backend
```

### 停止服务
```bash
docker-compose stop
```

### 完全清理（删除所有数据）
```bash
docker-compose down -v
```

## Docker vs 本地开发

| 特性 | 本地开发 | Docker部署 |
|------|---------|-----------|
| 配置复杂度 | 需要配置Vite代理、端口等 | 零配置 |
| 启动方式 | 分别启动前后端 | 一键启动 |
| 数据库 | 需要手动安装MySQL、Neo4j | 自动启动 |
| 端口冲突 | 可能冲突 | 容器隔离 |
| 环境污染 | 影响本地环境 | 完全隔离 |
| 部署到服务器 | 需要重新配置 | 直接复制 |

## 故障排查

### 问题1: 容器启动失败

```bash
# 查看详细日志
docker-compose logs backend

# 检查容器状态
docker-compose ps
```

### 问题2: 无法访问前端

检查Docker Desktop是否正在运行，然后：
```bash
docker-compose restart frontend
```

### 问题3: 数据库连接失败

等待MySQL完全启动（大约30秒）：
```bash
# 检查MySQL状态
docker-compose exec mysql mysqladmin ping -h localhost
```

### 问题4: WebSocket连接失败

这在Docker部署中**不会发生**，因为nginx已经配置好了WebSocket代理！

## 与本地开发对比

### 本地开发遇到的问题
```
❌ Vite代理配置复杂
❌ WebSocket连接失败
❌ 端口冲突
❌ 需要手动启动多个服务
❌ 环境变量配置繁琐
```

### Docker部署的优势
```
✅ 零配置
✅ WebSocket自动工作
✅ 容器隔离，无端口冲突
✅ 一键启动所有服务
✅ 统一的环境变量管理
```

## 部署到服务器

### 1. 复制代码到服务器
```bash
# 打包代码
tar -czf lifeswarm.tar.gz .

# 上传到服务器
scp lifeswarm.tar.gz user@server:/path/to/deploy/

# 在服务器上解压
ssh user@server
cd /path/to/deploy/
tar -xzf lifeswarm.tar.gz
```

### 2. 配置环境变量
```bash
cp .env.docker .env
nano .env  # 填写API Key
```

### 3. 部署
```bash
./deploy.sh
```

### 4. 配置域名（可选）

编辑 `nginx.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 改为你的域名
    # ...
}
```

重启前端服务：
```bash
docker-compose restart frontend
```

## 性能优化

### 调整资源限制

编辑 `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### 启用Redis缓存

添加Redis服务到 `docker-compose.yml`:
```yaml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
```

## 数据备份

### 备份数据库
```bash
# MySQL备份
docker-compose exec mysql mysqldump -u root -p123456 lifeswarm > backup.sql

# Neo4j备份
docker-compose exec neo4j neo4j-admin dump --to=/tmp/backup.dump
docker cp lifeswarm-neo4j:/tmp/backup.dump ./neo4j_backup.dump
```

### 恢复数据库
```bash
# MySQL恢复
docker-compose exec -T mysql mysql -u root -p123456 lifeswarm < backup.sql

# Neo4j恢复
docker cp neo4j_backup.dump lifeswarm-neo4j:/tmp/backup.dump
docker-compose exec neo4j neo4j-admin load --from=/tmp/backup.dump
```

## 总结

Docker部署让你：
- 🚀 **5分钟内完成部署**
- 🎯 **零配置烦恼**
- 🔒 **环境隔离安全**
- 📦 **一键迁移到任何服务器**

不再需要：
- ❌ 手动配置Vite代理
- ❌ 担心WebSocket连接问题
- ❌ 处理端口冲突
- ❌ 分别启动多个服务

**立即开始Docker部署，告别配置烦恼！**
