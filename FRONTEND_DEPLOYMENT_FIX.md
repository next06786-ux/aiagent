# 前端部署修复说明

## 问题描述

浏览器控制台显示错误：
```
POST http://localhost:6006/api/decision/enhanced/collect/continue-stream net::ERR_CONNECTION_REFUSED
```

## 根本原因

前端代码中存在硬编码的 `localhost:6006` URL，导致在 Docker 部署环境下无法正确访问后端 API。

## 已修复的文件

以下文件已将硬编码的 `localhost:6006` 改为相对路径（由 nginx 代理）：

1. ✅ `web/src/services/decision.ts` - 决策服务
2. ✅ `web/src/services/scheduleService.ts` - 智能日程服务
3. ✅ `web/src/services/parallelLifeService.ts` - 平行人生服务
4. ✅ `web/src/services/treeHoleService.ts` - 树洞服务
5. ✅ `web/src/services/llmService.ts` - LLM 服务

## 修复内容

### 修改前
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:6006';
```

### 修改后
```typescript
// 使用相对路径，由nginx代理到后端
const API_BASE_URL = '';
```

## 部署步骤

### 方法一：完整重新构建（推荐）

```bash
# 1. 停止并删除旧的前端容器
docker compose stop frontend
docker compose rm -f frontend

# 2. 清除构建缓存并重新构建
docker compose build --no-cache frontend

# 3. 启动新的前端容器
docker compose up -d frontend

# 4. 查看日志确认启动成功
docker compose logs -f frontend
```

### 方法二：快速重启（如果方法一失败）

```bash
# 1. 完全停止所有服务
docker compose down

# 2. 重新构建前端（无缓存）
docker compose build --no-cache frontend

# 3. 启动所有服务
docker compose up -d

# 4. 查看所有服务状态
docker compose ps
```

## 验证步骤

### 1. 清除浏览器缓存

- **Chrome/Edge**: 按 `Ctrl + Shift + Delete`，选择"缓存的图片和文件"，点击"清除数据"
- **或者**: 按 `Ctrl + F5` 强制刷新页面

### 2. 检查网络请求

打开浏览器开发者工具（F12）→ Network 标签页：

- ✅ 正确：请求应该是 `/api/decision/enhanced/collect/continue-stream`（相对路径）
- ❌ 错误：如果还是 `http://localhost:6006/...`，说明浏览器使用了缓存的旧 JS 文件

### 3. 检查 JS 文件

在 Network 标签页中：
- 找到 `index-*.js` 文件
- 查看 Response 标签页
- 搜索 `localhost:6006`
- ✅ 应该找不到任何结果

### 4. 测试功能

1. 登录系统
2. 进入决策推演页面
3. 开始信息收集
4. 查看控制台是否还有 `ERR_CONNECTION_REFUSED` 错误

## 常见问题

### Q1: 重新构建后还是报错？

**A**: 可能是浏览器缓存问题
- 尝试使用无痕模式/隐私模式打开
- 或者清除浏览器所有缓存数据

### Q2: nginx 缓存问题？

**A**: nginx.conf 中设置了 `expires 1y` 的静态资源缓存，可能导致旧文件被缓存

解决方法：
```bash
# 进入前端容器
docker exec -it lifeswarm-frontend sh

# 清除 nginx 缓存（如果有）
rm -rf /var/cache/nginx/*

# 重启 nginx
nginx -s reload
```

### Q3: 如何确认前端容器使用了新代码？

**A**: 检查容器构建时间
```bash
# 查看镜像构建时间
docker images | grep lifeswarm

# 查看容器创建时间
docker ps -a | grep frontend
```

如果时间不是最新的，说明没有重新构建，需要执行：
```bash
docker compose build --no-cache --pull frontend
```

## 技术说明

### 为什么使用相对路径？

在 Docker Compose 部署中：
- 前端运行在 nginx 容器（端口 80）
- 后端运行在 backend 容器（端口 8000）
- 用户访问 `http://your-server/`

nginx 配置了反向代理：
```nginx
location /api/ {
    proxy_pass http://backend:8000/api/;
}
```

因此前端使用相对路径 `/api/...` 时：
1. 浏览器发送请求到 `http://your-server/api/...`
2. nginx 接收请求并转发到 `http://backend:8000/api/...`
3. 后端处理请求并返回响应

### 为什么不能用 localhost:6006？

- `localhost:6006` 是开发环境的配置
- 在生产环境中，前端和后端在不同的容器中
- 浏览器无法直接访问 `localhost:6006`（端口未暴露或不在同一网络）

## 完成确认

部署完成后，请确认：

- [ ] 前端容器已重新构建并启动
- [ ] 浏览器缓存已清除
- [ ] Network 标签页显示请求使用相对路径
- [ ] 决策推演功能正常工作
- [ ] 控制台无 `ERR_CONNECTION_REFUSED` 错误

## 后续建议

1. **环境变量配置**: 考虑在 `docker-compose.yml` 中为前端添加构建参数
2. **版本控制**: 在 JS 文件名中添加哈希值，避免缓存问题
3. **健康检查**: 添加前端容器健康检查，确保服务正常运行

---

**修复完成时间**: 2026-04-21
**修复人员**: Kiro AI Assistant
