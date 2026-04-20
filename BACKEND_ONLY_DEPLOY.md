# 🚀 后端+数据库部署（不含前端）

## 📦 部署内容
- MySQL (关系型数据库)
- Redis (缓存)
- Neo4j (图数据库)
- Backend (FastAPI + FAISS)

## 🎯 快速部署

```bash
# 1. 上传代码到服务器
scp -r ./* root@152.136.13.236:/root/lifeswarm/

# 2. SSH登录
ssh root@152.136.13.236

# 3. 进入目录
cd /root/lifeswarm

# 4. 配置环境变量
cp .env.production .env
nano .env
# 修改: MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD, NEO4J_PASSWORD, QWEN_API_KEY

# 5. 启动服务（只启动后端+数据库）
docker-compose up -d mysql redis neo4j backend

# 6. 查看日志
docker-compose logs -f

# 7. 等待30秒后初始化数据库
sleep 30
docker-compose exec backend python backend/database/init_db.py
docker-compose exec backend python backend/database/init_neo4j.py

# 8. 测试后端
curl http://152.136.13.236:8000/health
```

## ✅ 访问地址

- 后端API: http://152.136.13.236:8000
- 健康检查: http://152.136.13.236:8000/health
- API文档: http://152.136.13.236:8000/docs

## 📱 HarmonyOS端配置

修改 `harmonyos/entry/src/main/ets/constants/ApiConstants.ets`:

```typescript
export class ApiConstants {
  static readonly BASE_URL = 'http://152.136.13.236:8000';
  static readonly WS_URL = 'ws://152.136.13.236:8000';
}
```

## 🔍 查看服务状态

```bash
# 查看运行的容器
docker-compose ps

# 应该看到4个容器:
# - lifeswarm-mysql
# - lifeswarm-redis
# - lifeswarm-neo4j
# - lifeswarm-backend

# 查看资源使用
docker stats
```

## 🛠️ 常用命令

```bash
# 重启后端
docker-compose restart backend

# 查看后端日志
docker-compose logs -f backend

# 停止所有服务
docker-compose stop

# 更新代码
git pull
docker-compose up -d --build backend
```

## 💾 内存使用（2核4G优化）

- MySQL: ~512MB
- Redis: ~256MB
- Neo4j: ~1GB
- Backend: ~1.5GB
- 系统预留: ~750MB

总计: ~4GB (刚好)
