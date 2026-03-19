# 决策层系统快速集成指南

## 🎯 5分钟快速开始

### 第1步：配置环境 (1分钟)

```bash
# 复制环境配置文件
cp /e:/ai/.env.example /e:/ai/.env

# 编辑 .env 文件，配置以下内容
# MYSQL_HOST=localhost
# REDIS_HOST=localhost
# NEO4J_HOST=localhost
```

### 第2步：初始化数据库 (1分钟)

```bash
# 运行数据库初始化脚本
cd /e:/ai/backend/database
python init_db.py localhost lifeswarm lifeswarm123 lifeswarm
```

### 第3步：启动服务 (1分钟)

```bash
# 启动MySQL
mysql -u lifeswarm -p lifeswarm123

# 启动Redis (新终端)
redis-server

# 启动Neo4j (新终端)
neo4j start

# 启动后端 (新终端)
cd /e:/ai/backend
python main.py
```

### 第4步：测试集成 (1分钟)

```bash
# 发送测试数据
curl -X POST http://localhost:8000/api/v1/frontend-data/sensor-data \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "sensor_type": "heart_rate",
    "value": 72.5,
    "unit": "bpm",
    "accuracy": 0.95,
    "device_id": "device_001",
    "timestamp": "2026-03-15T10:30:00"
  }'

# 获取决策
curl -X POST http://localhost:8000/api/v1/decisions/analyze-health \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "heart_rate": 72.5,
    "blood_oxygen": 97,
    "temperature": 37.0,
    "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 80,
    "sleep_hours": 8,
    "exercise_minutes": 30,
    "stress_level": 30
  }'
```

### 第5步：验证系统 (1分钟)

```bash
# 检查系统状态
curl http://localhost:8000/api/v1/decision-layer/status

# 应该返回:
# {
#   "status": "success",
#   "initialized": true,
#   "components": {
#     "decision_engine": true,
#     "decision_executor": true,
#     "sensor_collector": true,
#     "frontend_bridge": true
#   }
# }
```

---

## 🔧 详细集成步骤

### 步骤1：环境配置

**创建 .env 文件**:

```bash
# 数据库配置
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=lifeswarm
MYSQL_PASSWORD=lifeswarm123
MYSQL_DATABASE=lifeswarm

# 缓存配置
CACHE_TYPE=redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Neo4j配置
NEO4J_HOST=localhost
NEO4J_PORT=7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123

# 应用配置
LIFESWARM_ENV=development
DEBUG=True
LOG_LEVEL=INFO

# API配置
API_HOST=0.0.0.0
API_PORT=8000
```

### 步骤2：数据库初始化

**运行初始化脚本**:

```python
from backend.database.init_db import DatabaseInitializer

initializer = DatabaseInitializer(
    host='localhost',
    user='lifeswarm',
    password='lifeswarm123',
    database='lifeswarm'
)

if initializer.initialize():
    print("✓ Database initialized successfully")
else:
    print("✗ Failed to initialize database")
```

**验证表创建**:

```sql
-- 连接到MySQL
mysql -u lifeswarm -p lifeswarm123 lifeswarm

-- 查看表
SHOW TABLES;

-- 应该看到以下表:
-- users
-- sensor_data
-- health_data
-- app_usage
-- daily_statistics
-- decisions
-- rl_training
-- emergence_events
-- user_feedback
```

### 步骤3：系统初始化

**在应用启动时初始化决策层**:

```python
from backend.decision_layer import initialize_decision_layer, get_decision_layer_system
from backend.services.data_service import DataService
from backend.services.knowledge_graph import KnowledgeGraph
from backend.services.rl_agent import RLAgent
from backend.services.notification_service import NotificationService

# 创建服务实例
data_service = DataService()
kg = KnowledgeGraph()
rl_agent = RLAgent()
notification_service = NotificationService()

# 初始化决策层
success = initialize_decision_layer(
    data_service=data_service,
    knowledge_graph=kg,
    rl_agent=rl_agent,
    notification_service=notification_service
)

if success:
    print("✓ Decision layer initialized successfully")
    system = get_decision_layer_system()
else:
    print("✗ Failed to initialize decision layer")
```

### 步骤4：集成到FastAPI

**在FastAPI应用中注册决策层API**:

```python
from fastapi import FastAPI
from backend.decision_layer.api import router as decision_router
from backend.decision_layer.frontend_api import router as frontend_router
from backend.decision_layer.integrated_api import router as integrated_router

app = FastAPI()

# 注册决策层API
app.include_router(decision_router)
app.include_router(frontend_router)
app.include_router(integrated_router)

# 启动时初始化
@app.on_event("startup")
async def startup_event():
    from backend.decision_layer import initialize_decision_layer
    initialize_decision_layer(...)

# 关闭时清理
@app.on_event("shutdown")
async def shutdown_event():
    from backend.decision_layer import shutdown_decision_layer
    shutdown_decision_layer()
```

### 步骤5：前端集成

**HarmonyOS前端发送数据**:

```typescript
// HarmonyOS前端代码
import http from '@ohos.net.http';

class SensorDataSender {
  private apiUrl = 'http://backend:8000/api/v1/frontend-data';
  
  // 发送传感器数据
  async sendSensorData(userId: string, sensorData: any) {
    const httpRequest = http.createHttpRequest();
    
    const requestBody = {
      user_id: userId,
      sensor_type: sensorData.type,
      value: sensorData.value,
      unit: sensorData.unit,
      accuracy: sensorData.accuracy,
      device_id: sensorData.deviceId,
      timestamp: new Date().toISOString()
    };
    
    try {
      const response = await httpRequest.request(
        `${this.apiUrl}/sensor-data`,
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'application/json' },
          extraData: JSON.stringify(requestBody)
        }
      );
      
      console.log('Sensor data sent:', response.result);
    } catch (error) {
      console.error('Error sending sensor data:', error);
    }
  }
  
  // 批量发送传感器数据
  async sendBatchSensorData(userId: string, sensorDataList: any[]) {
    const httpRequest = http.createHttpRequest();
    
    const requestBody = {
      user_id: userId,
      sensor_data_list: sensorDataList.map(data => ({
        sensor_type: data.type,
        value: data.value,
        unit: data.unit,
        accuracy: data.accuracy,
        device_id: data.deviceId,
        timestamp: new Date().toISOString()
      }))
    };
    
    try {
      const response = await httpRequest.request(
        `${this.apiUrl}/sensor-data/batch`,
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'application/json' },
          extraData: JSON.stringify(requestBody)
        }
      );
      
      console.log('Batch sensor data sent:', response.result);
    } catch (error) {
      console.error('Error sending batch sensor data:', error);
    }
  }
}

// 使用示例
const sender = new SensorDataSender();

// 发送单个数据
sender.sendSensorData('user_001', {
  type: 'heart_rate',
  value: 72.5,
  unit: 'bpm',
  accuracy: 0.95,
  deviceId: 'device_001'
});

// 发送批量数据
sender.sendBatchSensorData('user_001', [
  { type: 'heart_rate', value: 72.5, unit: 'bpm', accuracy: 0.95, deviceId: 'device_001' },
  { type: 'temperature', value: 37.0, unit: '°C', accuracy: 0.9, deviceId: 'device_001' },
  { type: 'blood_oxygen', value: 97, unit: '%', accuracy: 0.95, deviceId: 'device_001' }
]);
```

---

## 📊 验证清单

### 数据库验证

```bash
# 连接到MySQL
mysql -u lifeswarm -p lifeswarm123 lifeswarm

# 查看表
SHOW TABLES;

# 查看传感器数据表结构
DESCRIBE sensor_data;

# 查看数据
SELECT * FROM sensor_data LIMIT 5;
```

### Redis验证

```bash
# 连接到Redis
redis-cli

# 查看所有键
KEYS *

# 查看特定用户的缓存
GET user:user_001:latest_sensor_data

# 查看缓存统计
INFO stats
```

### Neo4j验证

```bash
# 连接到Neo4j (http://localhost:7474)
# 运行Cypher查询

# 查看所有用户节点
MATCH (u:User) RETURN u;

# 查看用户的传感器读数
MATCH (u:User)-[:HAS_SENSOR_READING]->(r:SensorReading) 
WHERE u.user_id = 'user_001' 
RETURN r;

# 查看关系
MATCH (u:User)-[r]->(n) 
WHERE u.user_id = 'user_001' 
RETURN r, n;
```

### API验证

```bash
# 检查系统状态
curl http://localhost:8000/api/v1/decision-layer/status

# 发送测试数据
curl -X POST http://localhost:8000/api/v1/frontend-data/sensor-data \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user_001","sensor_type":"heart_rate","value":72.5,"unit":"bpm","accuracy":0.95,"device_id":"device_001"}'

# 获取缓存数据
curl http://localhost:8000/api/v1/decision-layer/cached-data/user_001

# 获取健康摘要
curl http://localhost:8000/api/v1/decision-layer/health-summary/user_001?days=7
```

---

## 🐛 常见问题

### Q1: MySQL连接失败

**解决方案**:
```bash
# 检查MySQL是否运行
mysql -u lifeswarm -p lifeswarm123

# 如果失败，启动MySQL
# Windows: net start MySQL80
# Linux: sudo systemctl start mysql
# macOS: brew services start mysql
```

### Q2: Redis连接失败

**解决方案**:
```bash
# 检查Redis是否运行
redis-cli ping

# 如果失败，启动Redis
# Windows: redis-server.exe
# Linux: redis-server
# macOS: brew services start redis
```

### Q3: Neo4j连接失败

**解决方案**:
```bash
# 检查Neo4j是否运行
curl http://localhost:7474

# 如果失败，启动Neo4j
# Windows: neo4j.bat console
# Linux: neo4j start
# macOS: brew services start neo4j
```

### Q4: API返回503错误

**解决方案**:
```python
# 检查决策层是否初始化
from backend.decision_layer import get_decision_layer_system

system = get_decision_layer_system()
if system and system.is_initialized():
    print("✓ Decision layer is initialized")
else:
    print("✗ Decision layer is not initialized")
    # 重新初始化
    from backend.decision_layer import initialize_decision_layer
    initialize_decision_layer(...)
```

---

## 📈 性能优化

### 1. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_user_timestamp ON sensor_data(user_id, timestamp);
CREATE INDEX idx_sensor_type ON sensor_data(sensor_type);

-- 查看索引
SHOW INDEX FROM sensor_data;
```

### 2. Redis优化

```bash
# 增加Redis内存
# 编辑 redis.conf
# maxmemory 2gb
# maxmemory-policy allkeys-lru

# 重启Redis
redis-cli shutdown
redis-server
```

### 3. Neo4j优化

```bash
# 编辑 neo4j.conf
# dbms.memory.heap.initial_size=2G
# dbms.memory.heap.max_size=4G

# 重启Neo4j
neo4j restart
```

---

## 🚀 部署到生产

### 1. 环境配置

```bash
# 生产环境 .env
LIFESWARM_ENV=production
DEBUG=False
LOG_LEVEL=WARNING

# 数据库配置 (使用生产数据库)
MYSQL_HOST=prod-db.example.com
MYSQL_USER=prod_user
MYSQL_PASSWORD=secure_password

# Redis配置 (使用生产Redis)
REDIS_HOST=prod-redis.example.com
REDIS_PASSWORD=secure_password

# Neo4j配置 (使用生产Neo4j)
NEO4J_HOST=prod-neo4j.example.com
NEO4J_PASSWORD=secure_password
```

### 2. 启动脚本

```bash
#!/bin/bash
# start_production.sh

# 启动后端服务
cd /e:/ai/backend
python main.py --env production --workers 4

# 或使用Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### 3. 监控和告警

```python
# 添加监控
from prometheus_client import Counter, Histogram

decision_counter = Counter('decisions_generated', 'Total decisions generated')
decision_latency = Histogram('decision_latency_seconds', 'Decision generation latency')

@decision_latency.time()
def generate_decision():
    # 生成决策
    decision_counter.inc()
```

---

## 📞 获取帮助

- 查看 [README.md](backend/decision_layer/README.md)
- 查看 [使用示例](backend/decision_layer/examples.py)
- 查看 [测试用例](backend/decision_layer/test_integration.py)
- 查看 [API文档](backend/decision_layer/api.py)

---

**最后更新**: 2026-03-15
**版本**: 1.0.0
**状态**: 生产就绪 ✅

