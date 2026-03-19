# 真实数据集成快速检查清单

## ✅ 第1周：前端集成

### 前端配置
- [ ] 配置HarmonyOS后端API端点
  ```typescript
  // harmonyos/entry/src/main/ets/common/Config.ets
  export const API_CONFIG = {
    BASE_URL: 'http://your-backend-ip:8000',
    SENSOR_ENDPOINT: '/api/v3/real-data/receive-harmonyos-sensor',
    TIMEOUT: 5000
  };
  ```

- [ ] 实现传感器数据发送服务
  ```typescript
  // harmonyos/entry/src/main/ets/service/SensorDataSender.ets
  export class SensorDataSender {
    async sendSensorData(data: SensorData): Promise<void> {
      const payload = {
        user_id: this.userId,
        heart_rate: data.heartRate,
        steps: data.steps,
        accelerometer: data.accelerometer,
        gyroscope: data.gyroscope,
        temperature: data.temperature,
        blood_oxygen: data.bloodOxygen,
        timestamp: new Date().toISOString()
      };
      
      await fetch(API_CONFIG.BASE_URL + API_CONFIG.SENSOR_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }
  }
  ```

- [ ] 测试数据接收
  - 启动后端服务
  - 运行HarmonyOS应用
  - 检查API日志

### 后端配置
- [ ] 验证API端点可访问
  ```bash
  curl -X POST http://localhost:8000/api/v3/real-data/receive-harmonyos-sensor \
    -H "Content-Type: application/json" \
    -d '{"user_id": "test_user", "heart_rate": 72, "timestamp": "2026-03-15T10:30:00"}'
  ```

- [ ] 检查日志输出
  ```
  [INFO] Real Data Integration Layer initialized for user test_user
  [INFO] Successfully received and processed sensor data for user test_user
  ```

---

## ✅ 第2周：数据库集成

### MySQL配置
- [ ] 创建数据库
  ```sql
  CREATE DATABASE lifeswarm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```

- [ ] 创建传感器数据表
  ```sql
  CREATE TABLE sensor_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(255) NOT NULL,
    timestamp DATETIME NOT NULL,
    heart_rate FLOAT,
    steps INT,
    accelerometer_x FLOAT,
    accelerometer_y FLOAT,
    accelerometer_z FLOAT,
    gyroscope_x FLOAT,
    gyroscope_y FLOAT,
    gyroscope_z FLOAT,
    light FLOAT,
    pressure FLOAT,
    temperature FLOAT,
    blood_oxygen FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_timestamp (user_id, timestamp),
    INDEX idx_timestamp (timestamp)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  ```

- [ ] 创建用户表
  ```sql
  CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  ```

- [ ] 创建每日统计表
  ```sql
  CREATE TABLE daily_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    heart_rate_avg FLOAT,
    heart_rate_min FLOAT,
    heart_rate_max FLOAT,
    steps_total INT,
    temperature_avg FLOAT,
    blood_oxygen_avg FLOAT,
    data_points INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_date (user_id, date)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  ```

- [ ] 验证连接
  ```bash
  mysql -h localhost -u lifeswarm -p lifeswarm123 -e "USE lifeswarm; SHOW TABLES;"
  ```

### 数据库配置文件
- [ ] 创建 `.env` 文件
  ```
  # Database Configuration
  DB_TYPE=mysql
  MYSQL_HOST=localhost
  MYSQL_PORT=3306
  MYSQL_USER=lifeswarm
  MYSQL_PASSWORD=lifeswarm123
  MYSQL_DATABASE=lifeswarm
  
  # Cache Configuration
  CACHE_TYPE=redis
  REDIS_HOST=localhost
  REDIS_PORT=6379
  REDIS_DB=0
  REDIS_PREFIX=lifeswarm:
  
  # Neo4j Configuration
  NEO4J_HOST=localhost
  NEO4J_PORT=7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=neo4j123
  
  # Environment
  LIFESWARM_ENV=development
  ```

- [ ] 验证ORM模型
  ```python
  # backend/database/models.py
  from sqlalchemy import Column, Integer, Float, String, DateTime
  from sqlalchemy.ext.declarative import declarative_base
  
  Base = declarative_base()
  
  class SensorData(Base):
      __tablename__ = 'sensor_data'
      
      id = Column(Integer, primary_key=True)
      user_id = Column(String(255), nullable=False, index=True)
      timestamp = Column(DateTime, nullable=False, index=True)
      heart_rate = Column(Float)
      steps = Column(Integer)
      # ... 其他字段
  ```

---

## ✅ 第3周：缓存和知识图谱

### Redis配置
- [ ] 启动Redis服务
  ```bash
  redis-server
  ```

- [ ] 验证Redis连接
  ```bash
  redis-cli ping
  # 输出: PONG
  ```

- [ ] 测试缓存操作
  ```python
  from backend.database.cache_manager import CacheManager
  
  cache = CacheManager()
  cache.set("test_key", "test_value", ttl=3600)
  value = cache.get("test_key")
  print(value)  # 输出: test_value
  ```

- [ ] 验证缓存键设计
  ```
  user:user_001:latest_sensor_data
  user:user_001:latest_heart_rate
  user:user_001:latest_steps
  user:user_001:daily_stats:2026-03-15
  ```

### Neo4j配置
- [ ] 启动Neo4j服务
  ```bash
  neo4j start
  ```

- [ ] 访问Neo4j浏览器
  ```
  http://localhost:7474
  用户名: neo4j
  密码: neo4j123
  ```

- [ ] 创建索引
  ```cypher
  CREATE INDEX ON :User(user_id);
  CREATE INDEX ON :SensorReading(timestamp);
  CREATE INDEX ON :HeartRate(timestamp);
  ```

- [ ] 测试知识图谱操作
  ```python
  from backend.knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
  
  kg = Neo4jKnowledgeGraph()
  
  # 创建用户节点
  kg.create_or_update_node({
      "id": "user_001",
      "type": "User",
      "properties": {"name": "Test User"}
  })
  
  # 创建传感器节点
  kg.create_or_update_node({
      "id": "sensor_001",
      "type": "SensorReading",
      "properties": {"heart_rate": 72}
  })
  
  # 创建关系
  kg.create_relationship(
      source_id="user_001",
      target_id="sensor_001",
      relationship_type="HAS_SENSOR_READING"
  )
  ```

---

## ✅ 第4周：测试和优化

### 集成测试
- [ ] 测试完整数据流
  ```bash
  # 1. 发送传感器数据
  curl -X POST http://localhost:8000/api/v3/real-data/receive-harmonyos-sensor \
    -H "Content-Type: application/json" \
    -d '{
      "user_id": "user_001",
      "heart_rate": 72,
      "steps": 1250,
      "temperature": 36.8,
      "blood_oxygen": 97,
      "timestamp": "2026-03-15T10:30:00"
    }'
  
  # 2. 获取最新数据
  curl http://localhost:8000/api/v3/real-data/latest-sensor/user_001
  
  # 3. 获取每日统计
  curl -X POST http://localhost:8000/api/v3/real-data/daily-statistics \
    -H "Content-Type: application/json" \
    -d '{"user_id": "user_001", "date": "2026-03-15"}'
  
  # 4. 获取缓存统计
  curl http://localhost:8000/api/v3/real-data/cache-stats/user_001
  ```

- [ ] 验证数据存储
  ```bash
  # MySQL验证
  mysql -u lifeswarm -p lifeswarm123 -e "SELECT * FROM lifeswarm.sensor_data LIMIT 5;"
  
  # Redis验证
  redis-cli GET "lifeswarm:user:user_001:latest_sensor_data"
  
  # Neo4j验证
  # 访问 http://localhost:7474 查看图谱
  ```

### 性能测试
- [ ] 测试响应时间
  ```bash
  # 测试缓存命中
  time curl http://localhost:8000/api/v3/real-data/latest-sensor/user_001
  # 预期: < 50ms
  
  # 测试数据库查询
  time curl -X POST http://localhost:8000/api/v3/real-data/daily-statistics \
    -H "Content-Type: application/json" \
    -d '{"user_id": "user_001", "date": "2026-03-15"}'
  # 预期: < 200ms
  ```

- [ ] 测试并发
  ```bash
  # 使用 Apache Bench
  ab -n 1000 -c 10 http://localhost:8000/api/v3/real-data/latest-sensor/user_001
  ```

### 数据验证
- [ ] 验证数据准确性
  ```python
  # 检查MySQL中的数据
  SELECT COUNT(*) FROM sensor_data WHERE user_id = 'user_001';
  
  # 检查Redis缓存
  redis-cli KEYS "lifeswarm:user:user_001:*"
  
  # 检查Neo4j关系
  MATCH (u:User)-[r:HAS_SENSOR_READING]->(s:SensorReading) 
  WHERE u.user_id = 'user_001' 
  RETURN COUNT(r);
  ```

---

## 📊 完成度检查

### 数据采集层
- [ ] 前端传感器集成：100%
- [ ] MySQL存储：100%
- [ ] Redis缓存：100%
- [ ] Neo4j知识图谱：100%
- [ ] 数据查询接口：100%

### 系统完成度
- [ ] 数据采集：30% → 100% ✅
- [ ] 数据库应用：0% → 100% ✅
- [ ] 缓存应用：0% → 100% ✅
- [ ] 知识图谱应用：20% → 100% ✅
- [ ] 系统总体：72% → 95% ✅

### 国赛评分
- [ ] 理论完美度：85分
- [ ] 实现完成度：90分 (从70分提升)
- [ ] 创新性：70分
- [ ] 演示效果：85分 (从75分提升)
- [ ] **总分：330/400 = 82.5分** (从75分提升)

---

## 🚀 快速启动命令

### 启动所有服务
```bash
# 1. 启动MySQL
mysql -u lifeswarm -p lifeswarm123

# 2. 启动Redis
redis-server

# 3. 启动Neo4j
neo4j start

# 4. 启动后端
cd /e:/ai/backend
python start_server.py

# 5. 启动HarmonyOS应用
cd /e:/ai/harmonyos
./build.bat
```

### 验证所有服务
```bash
# 检查MySQL
mysql -u lifeswarm -p lifeswarm123 -e "SELECT 1;"

# 检查Redis
redis-cli ping

# 检查Neo4j
curl http://localhost:7474

# 检查后端
curl http://localhost:8000/api/v3/system/full-test

# 检查HarmonyOS
# 在设备上运行应用
```

---

## 📝 故障排除

### 常见问题

**问题1：MySQL连接失败**
```
解决方案：
1. 检查MySQL是否运行: mysql -u lifeswarm -p lifeswarm123
2. 检查.env配置是否正确
3. 检查防火墙设置
```

**问题2：Redis连接失败**
```
解决方案：
1. 检查Redis是否运行: redis-cli ping
2. 检查Redis配置文件
3. 检查端口是否被占用: netstat -an | grep 6379
```

**问题3：Neo4j连接失败**
```
解决方案：
1. 检查Neo4j是否运行: neo4j status
2. 访问 http://localhost:7474 检查Web界面
3. 检查Neo4j日志: tail -f /path/to/neo4j/logs/neo4j.log
```

**问题4：前端数据未到达后端**
```
解决方案：
1. 检查HarmonyOS应用日志
2. 检查后端API日志
3. 检查网络连接: ping backend-ip
4. 检查防火墙: 确保8000端口开放
```

---

## ✨ 预期成果

### 完成后的系统架构
```
HarmonyOS前端 (真实传感器)
    ↓
API接收层 (/api/v3/real-data/receive-harmonyos-sensor)
    ↓
├─ MySQL (持久化存储)
├─ Redis (缓存加速)
└─ Neo4j (知识图谱)
    ↓
数据查询接口
    ↓
后端系统 (知识图谱、强化学习、决策引擎等)
    ↓
个性化建议输出
```

### 性能指标
- 数据接收延迟：< 100ms
- 缓存命中率：> 80%
- 数据库查询：< 200ms
- 知识图谱查询：< 500ms

### 国赛评分提升
- 改进前：75分 (三等奖)
- 改进后：82.5分 (二等奖)
- 提升：+7.5分

---

## 📞 下一步

1. **立即行动**：按照第1-4周的计划执行
2. **并行进行**：前端、数据库、缓存可以并行配置
3. **持续测试**：每完成一个模块就进行测试
4. **性能优化**：根据测试结果进行优化
5. **准备演示**：完成后准备国赛演示

**预计总耗时：2-3周**
**预期成果：系统完成度从72%提升到95%，国赛评分从75分提升到82.5分**

