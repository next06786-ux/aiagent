# 日志配置说明

## 环境变量

在 `.env` 文件中添加以下配置来控制日志输出：

### 1. 详细启动日志
```bash
# 显示详细的启动日志（默认：false）
VERBOSE_STARTUP=false
```

设置为 `true` 可以看到：
- ✅ 系统初始化成功信息
- ⏱️ 各模块加载耗时
- ⚠️ 警告信息

### 2. 调试模式
```bash
# 开启调试模式，显示详细的运行时日志（默认：false）
DEBUG_MODE=false
```

设置为 `true` 可以看到：
- Neo4j 查询结果统计
- 知识图谱构建详情
- RAG 系统检索信息
- 数据处理过程

### 3. 本地模型
```bash
# 启用本地 GPU 模型（默认：false）
ENABLE_LOCAL_MODEL=false
```

## 推荐配置

### 生产环境（最小日志）
```bash
VERBOSE_STARTUP=false
DEBUG_MODE=false
ENABLE_LOCAL_MODEL=false
```

### 开发环境（适度日志）
```bash
VERBOSE_STARTUP=true
DEBUG_MODE=false
ENABLE_LOCAL_MODEL=false
```

### 调试环境（完整日志）
```bash
VERBOSE_STARTUP=true
DEBUG_MODE=true
ENABLE_LOCAL_MODEL=false
```

## 修改后的日志行为

### 启动时
- 默认只显示关键错误和警告
- 不再显示每个模块的初始化信息
- 不再显示耗时统计

### 运行时
- Neo4j 查询结果不再打印到控制台
- 知识图谱构建过程静默执行
- 只在出错时显示错误信息

## 如何启用详细日志

1. 编辑项目根目录的 `.env` 文件
2. 添加或修改：
   ```bash
   VERBOSE_STARTUP=true
   DEBUG_MODE=true
   ```
3. 重启后端服务

## 日志级别

系统使用 Python logging 模块，默认级别为 `WARNING`：
- `ERROR`: 错误信息（始终显示）
- `WARNING`: 警告信息（始终显示）
- `INFO`: 一般信息（需要 VERBOSE_STARTUP=true）
- `DEBUG`: 调试信息（需要 DEBUG_MODE=true）
