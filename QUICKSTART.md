# 快速启动指南

## 系统要求

- Python 3.8+
- FastAPI
- 基本的系统依赖

## 安装步骤

### 1. 安装依赖
```bash
cd /e:/ai/backend
pip install fastapi uvicorn
```

### 2. 启动服务器
```bash
python start_server.py
```

服务器将在 `http://localhost:8000` 启动

### 3. 运行演示
在另一个终端中：
```bash
cd /e:/ai
python demo.py
```

## API 快速测试

### 完整系统测试
```bash
curl -X POST http://localhost:8000/api/v3/system/full-test \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "user_message": "I have been sleeping poorly and feeling stressed",
    "user_data": {
      "sleep_hours": 5,
      "exercise_minutes": 20,
      "stress_level": 8,
      "mood": 4,
      "health_score": 60
    }
  }'
```

### 知识图谱构建
```bash
curl -X POST http://localhost:8000/api/v3/kg/build-from-data \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "user_data": {
      "sleep_hours": 5,
      "exercise_minutes": 20,
      "stress_level": 8,
      "mood": 4,
      "health_score": 60
    },
    "user_message": "I am stressed"
  }'
```

### 数字孪生预测
```bash
curl -X POST http://localhost:8000/api/v3/digital-twin/predict \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "current_state": {
      "sleep_hours": 5,
      "stress_level": 8,
      "mood": 4,
      "health_score": 60,
      "exercise_minutes": 20
    },
    "prediction_days": 7
  }'
```

### 反事实分析
```bash
curl -X POST http://localhost:8000/api/v3/counterfactual/what-if \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "original_decision": "work",
    "alternative_decision": "exercise",
    "current_state": {
      "sleep_hours": 5,
      "stress_level": 8,
      "mood": 4,
      "health_score": 60
    },
    "decision_impact": {}
  }'
```

## 系统架构概览

```
┌─────────────────────────────────────────┐
│         用户输入 (文本、数据)             │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼────────┐
        │  知识图谱构建    │ (529行)
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  强化学习训练    │ (394行)
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │   决策引擎       │ (470行)
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  涌现检测        │ (538行)
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──┐  ┌─────▼────┐  ┌────▼────┐
│混合  │  │数字孪生  │  │反事实   │
│智能  │  │预测      │  │分析     │
└──────┘  └──────────┘  └─────────┘
    │            │            │
    └────────────┼────────────┘
                 │
        ┌────────▼────────┐
        │  个性化建议      │
        └─────────────────┘
```

## 核心模块说明

### 1. 知识图谱自动化构建
- 自动从用户数据提取实体
- 推理实体间的关系
- 支持6大领域
- 因果链分析

**关键类**: `AutomatedKnowledgeGraphBuilder`

### 2. 强化学习真实训练
- Q-Learning算法
- 真实用户反馈训练
- 策略性能评估
- 推荐成功率预测

**关键类**: `ReinforcementLearningTrainer`

### 3. 决策引擎
- 基于真实数据的决策
- 多维度决策规则库
- 知识图谱与RL融合
- 决策反馈记录

**关键类**: `DecisionEngine`

### 4. 涌现检测系统
- 6种涌现类型检测
- 相关性模式识别
- 非线性效应分析
- 反馈循环识别

**关键类**: `EmergenceDetector`

### 5. 混合智能系统
- 整合所有组件
- 自适应模式选择
- 实时决策融合
- 系统健康度评估

**关键类**: `HybridIntelligenceSystem`

### 6. 数字孪生系统
- 用户状态实时模拟
- 未来趋势预测
- 干预效果评估
- 三场景模拟

**关键类**: `DigitalTwin`

### 7. 反事实分析
- 5种反事实场景
- 后悔程度评估
- 机会成本计算
- 最好/最坏情况预测

**关键类**: `CounterfactualAnalyzer`

## 常见问题

### Q: 如何添加新的决策规则？
A: 编辑 `backend/decision/decision_engine.py` 中的 `_initialize_decision_rules()` 方法

### Q: 如何自定义涌现检测？
A: 在 `backend/emergence/emergence_detector.py` 中添加新的检测方法

### Q: 如何扩展知识图谱？
A: 在 `backend/knowledge/automated_kg_builder.py` 中的 `_initialize_predefined_entities()` 中添加新实体

### Q: 如何调整强化学习参数？
A: 修改 `backend/learning/rl_trainer.py` 中的学习率、折扣因子等参数

## 性能优化建议

1. **缓存**: 使用Redis缓存频繁查询的结果
2. **异步处理**: 使用async/await处理长时间运行的任务
3. **数据库**: 集成PostgreSQL存储历史数据
4. **并发**: 使用线程池处理并发请求
5. **监控**: 添加日志和性能监控

## 部署建议

### 开发环境
```bash
python start_server.py
```

### 生产环境
```bash
gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app
```

### Docker部署
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 文档链接

- [系统架构详解](SYSTEM_ARCHITECTURE.md)
- [改进总结](IMPROVEMENT_SUMMARY.md)
- [API文档](API_DOCUMENTATION.md)

## 支持

如有问题，请查看：
1. 演示脚本: `demo.py`
2. 测试API: `/api/v3/system/full-test`
3. 系统日志: 服务器输出

## 许可证

MIT License

---

**最后更新**: 2026年3月15日
**系统版本**: 1.0
**总代码行数**: 34,558行

