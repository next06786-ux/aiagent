# 🚀 快速部署命令

## 方式1: 一键部署脚本

```bash
# 上传代码到服务器
scp -r ./* root@152.136.13.236:/root/lifeswarm/

# SSH登录服务器
ssh root@152.136.13.236

# 进入项目目录
cd /root/lifeswarm

# 赋予执行权限
chmod +x DEPLOY.sh

# 运行部署脚本
./DEPLOY.sh
```

---

## 方式2: 手动逐步部署

### 1️⃣ 安装Docker
```bash
curl -fsSL https://get.docker.com | bash
systemctl start docker
systemctl enable docker
```

### 2️⃣ 安装Docker Compose
```bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### 3️⃣ 配置环境变量
```bash
# 编辑环境变量（必须修改密码和API密钥）
nano .env
```

**必改项**:
- `MYSQL_PASSWORD=你的MySQL密码`
- `MYSQL_ROOT_PASSWORD=你的Root密码`
- `NEO4J_PASSWORD=你的Neo4j密码`
- `QWEN_API_KEY=你的通义千问API密钥`

### 4️⃣ 启动服务
```bash
# 构建并启动所有容器
docker-compose up -d --build

# 查看启动日志
docker-compose logs -f
```

### 5️⃣ 初始化数据库
```bash
# 等待30秒让数据库完全启动
sleep 30

# 初始化MySQL
docker-compose exec backend python backend/database/init_db.py

# 初始化Neo4j
docker-compose exec backend python backend/database/init_neo4j.py
```

### 6️⃣ 验证部署
```bash
# 查看容器状态
docker-compose ps

# 测试后端健康检查
curl http://localhost:8000/health

# 浏览器访问
# 前端: http://152.136.13.236
# 后端: http://152.136.13.236:8000
```

---

## 常用管理命令

```bash
# 查看日志
docker-compose logs -f                    # 所有服务
docker-compose logs -f backend            # 只看后端
docker-compose logs -f mysql              # 只看MySQL

# 重启服务
docker-compose restart                    # 重启所有
docker-compose restart backend            # 重启后端

# 停止服务
docker-compose stop                       # 停止所有
docker-compose down                       # 停止并删除容器

# 更新代码
git pull                                  # 拉取最新代码
docker-compose up -d --build              # 重新构建

# 查看资源使用
docker stats                              # 实时监控

# 进入容器
docker-compose exec backend bash          # 进入后端容器
docker-compose exec mysql bash            # 进入MySQL容器
```

---

## 故障排查

### 后端启动失败
```bash
docker-compose logs backend
# 常见原因: 数据库连接失败、环境变量未配置
```

### 数据库连接失败
```bash
# 测试MySQL
docker-compose exec mysql mysql -u root -p

# 测试Neo4j
docker-compose exec neo4j cypher-shell -u neo4j -p your_password

# 测试Redis
docker-compose exec redis redis-cli ping
```

### 内存不足
```bash
# 查看内存使用
free -h
docker stats

# 减少worker数量（编辑 Dockerfile.backend）
# 将 --workers 2 改为 --workers 1
```

---

## 数据备份

```bash
# 备份MySQL
docker-compose exec mysql mysqldump -u root -p lifeswarm > backup.sql

# 备份Neo4j
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/data/backup.dump

# 备份FAISS索引
docker cp lifeswarm-backend:/app/faiss_indexes ./backup_faiss
```

---

## 防火墙配置

```bash
# 安装UFW
apt install ufw

# 允许SSH
ufw allow 22

# 允许HTTP
ufw allow 80

# 允许后端API（可选）
ufw allow 8000

# 启用防火墙
ufw enable
```

---

## 完成！

✅ 前端访问: **http://152.136.13.236**  
✅ 后端API: **http://152.136.13.236:8000**  
✅ 健康检查: **http://152.136.13.236:8000/health**
