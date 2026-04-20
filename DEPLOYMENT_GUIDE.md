# 🚀 LifeSwarm 服务器部署指南

## 📋 服务器信息
- **IP地址**: 152.136.13.236
- **配置**: 2核4G
- **操作系统**: Linux (推荐 Ubuntu 20.04+)

## ✅ 部署前准备

### 1. 安装Docker和Docker Compose

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com | bash

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.production .env

# 编辑环境变量（填写实际的密码和API密钥）
nano .env
```

**必须修改的配置项**:
- `MYSQL_PASSWORD`: MySQL用户密码
- `MYSQL_ROOT_PASSWORD`: MySQL root密码
- `NEO4J_PASSWORD`: Neo4j密码
- `QWEN_API_KEY`: 通义千问API密钥（或使用DeepSeek）

### 3. 上传代码到服务器

```bash
# 方式1: 使用Git
git clone <your-repo-url>
cd lifeswarm

# 方式2: 使用SCP上传
scp -r ./lifeswarm root@152.136.13.236:/root/
```

## 🐳 Docker部署步骤

### 1. 构建并启动所有服务

```bash
# 构建镜像并启动（首次部署）
docker-compose up -d --build

# 查看启动日志
docker-compose logs -f
```

### 2. 初始化数据库

```bash
# 等待MySQL启动完成（约30秒）
sleep 30

# 初始化MySQL数据库
docker-compose exec backend python backend/database/init_db.py

# 初始化Neo4j数据库
docker-compose exec backend python backend/database/init_neo4j.py
```

### 3. 验证服务状态

```bash
# 查看所有容器状态
docker-compose ps

# 应该看到5个容器都在运行:
# - lifeswarm-mysql
# - lifeswarm-redis
# - lifeswarm-neo4j
# - lifeswarm-backend
# - lifeswarm-frontend
```

### 4. 测试访问

```bash
# 测试后端健康检查
curl http://152.136.13.236:8000/health

# 浏览器访问前端
http://152.136.13.236
```

## 📊 内存优化配置

针对2核4G服务器，已做以下优化：

### 内存分配
- MySQL: 512MB (限制) / 256MB (预留)
- Redis: 256MB (限制) / 128MB (预留)
- Neo4j: 1GB (限制) / 512MB (预留)
- Backend: 1.5GB (限制) / 768MB (预留)
- Frontend: 256MB (限制) / 128MB (预留)
- **总计**: ~3.5GB (预留1.5GB给系统)

### 性能优化
- MySQL: 最大连接数100
- Redis: 最大内存256MB，LRU淘汰策略
- Neo4j: 堆内存512MB，页缓存256MB
- Backend: 2个Worker进程
- Frontend: Nginx静态资源缓存

## 🔧 常用管理命令

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
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
# 停止所有服务
docker-compose stop

# 停止并删除容器（保留数据）
docker-compose down

# 停止并删除容器和数据卷（危险！）
docker-compose down -v
```

### 更新代码
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 或者只重启后端
docker-compose up -d --build backend
```

### 数据备份
```bash
# 备份MySQL
docker-compose exec mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} lifeswarm > backup_mysql_$(date +%Y%m%d).sql

# 备份Neo4j
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/data/backup_$(date +%Y%m%d).dump

# 备份FAISS索引
docker cp lifeswarm-backend:/app/faiss_indexes ./backup_faiss_$(date +%Y%m%d)
```

## 🔒 安全配置

### 1. 配置防火墙
```bash
# 安装UFW
sudo apt install ufw

# 允许SSH
sudo ufw allow 22

# 允许HTTP
sudo ufw allow 80

# 允许后端API（可选，如果需要直接访问）
sudo ufw allow 8000

# 启用防火墙
sudo ufw enable
```

### 2. 修改默认密码
- 修改`.env`中的所有密码
- 使用强密码（至少16位，包含大小写字母、数字、特殊字符）

### 3. 限制数据库访问
- MySQL、Redis、Neo4j只在Docker内网访问
- 不要暴露3306、6379、7474、7687端口到公网

## 📈 监控和维护

### 查看资源使用
```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看Docker磁盘使用
docker system df
```

### 清理Docker资源
```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的卷
docker volume prune

# 清理所有未使用的资源
docker system prune -a
```

## ⚠️ 故障排查

### 后端启动失败
```bash
# 查看后端日志
docker-compose logs backend

# 常见问题:
# 1. 数据库连接失败 -> 检查MySQL是否启动
# 2. Neo4j连接失败 -> 检查Neo4j密码配置
# 3. 内存不足 -> 减少worker数量或调整内存限制
```

### 前端无法访问
```bash
# 检查Nginx配置
docker-compose exec frontend nginx -t

# 查看前端日志
docker-compose logs frontend

# 检查后端API是否可访问
curl http://backend:8000/health
```

### 数据库连接问题
```bash
# 测试MySQL连接
docker-compose exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD}

# 测试Neo4j连接
docker-compose exec neo4j cypher-shell -u neo4j -p ${NEO4J_PASSWORD}

# 测试Redis连接
docker-compose exec redis redis-cli ping
```

## 🎯 性能调优建议

### 如果内存不足
1. 减少Backend worker数量（改为1）
2. 降低Neo4j堆内存（改为256MB）
3. 禁用不必要的功能模块

### 如果响应慢
1. 增加Redis缓存时间
2. 优化数据库查询
3. 启用Nginx缓存
4. 考虑升级服务器配置

## 📞 技术支持

如遇到问题，请检查：
1. Docker日志: `docker-compose logs`
2. 系统资源: `docker stats`
3. 网络连接: `curl http://localhost:8000/health`

---

**部署完成后，访问**: http://152.136.13.236
