# 知识图谱调试指南

## 当前状态

✅ HTTP请求成功（200状态码）
✅ HttpInterceptor已兼容`success`字段
❌ 数据提取失败（`backendResponse.data`为空）

## 调试步骤

### 1. 查看完整的响应日志

重新运行应用，查看以下日志：

```
[KnowledgeGraphService] 职业图谱响应: {...}
[KnowledgeGraphService] 教育图谱响应: {...}
[KnowledgeGraphService] 人际关系图谱响应: {...}
```

### 2. 检查响应结构

后端应该返回：
```json
{
  "success": true,
  "data": {
    "nodes": [...],
    "edges": [...],
    "metadata": {...}
  },
  "message": "已生成xxx知识图谱，包含xx个节点"
}
```

### 3. 常见问题

#### 问题1：data字段为null
**症状**：`[KnowledgeGraphService] 后端返回数据为空`

**可能原因**：
- HttpClient的泛型类型不匹配
- HttpInterceptor返回的对象结构不对
- 后端返回的数据被过滤了

**解决方案**：
检查HttpClient.post的返回值类型，确保返回完整的响应对象

#### 问题2：nodes/edges为空数组
**症状**：`nodesCount: 0, edgesCount: 0`

**可能原因**：
- 用户没有知识图谱数据
- 后端查询失败
- 数据格式不匹配

**解决方案**：
- 检查后端日志
- 使用真实用户ID而不是test_user_001
- 验证Neo4j数据库中是否有数据

#### 问题3：类型转换失败
**症状**：编译错误或运行时类型错误

**解决方案**：
使用`Record<string, Object>`动态类型，避免强类型约束

## 预期日志输出

成功的日志应该是：

```
[KnowledgeGraphService] 发起职业图谱请求: {"user_id":"xxx",...}
[KnowledgeGraphService] 职业图谱响应: {"success":true,"data":{...},"message":"..."}
[KnowledgeGraphService] 开始转换数据，响应类型: object
[KnowledgeGraphService] 响应keys: success, data, message
[KnowledgeGraphService] data字段keys: nodes, edges, metadata
[KnowledgeGraphService] 转换职业图谱数据: {hasNodes:true, nodesCount:10, hasEdges:true, edgesCount:15}
[KnowledgeGraphService] 转换完成: {nodes:10, edges:15}
[KnowledgeGraphPage] 星图数据加载完成: {relationship:5, career:10, education:8}
```

## 下一步

1. 重新编译运行
2. 查看完整的响应日志
3. 根据日志输出定位问题
4. 如果data字段确实为空，检查HttpInterceptor的handleResponse方法
