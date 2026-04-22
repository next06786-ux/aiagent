# HarmonyOS 知识图谱后端对接修复方案

## 问题分析

当前HarmonyOS端的知识图谱页面存在以下问题：

1. **显示测试数据**：页面显示的是硬编码的星空图测试数据，而不是从后端获取的真实数据
2. **API对接不完整**：虽然定义了API端点，但实际调用逻辑与Web端不一致
3. **数据格式不匹配**：后端返回的数据格式与前端期望的格式存在差异

## Web端实现参考

### Web端API调用流程

```typescript
// 1. 职业图谱 - POST请求
getCareerGraphView({
  user_id: user.user_id,
  mastered_skills: [],  // 空数组，让后端从知识图谱查询
  partial_skills: [],
  missing_skills: [],
  target_direction: 'Python工程师'
})

// 2. 教育图谱 - POST请求
getEducationGraphView({
  user_id: user.user_id,
  gpa: 3.5,
  gpa_max: 4.0,
  ranking_percent: 0.2,
  sat_act: 1450,
  research_experience: 0.6,
  publications: 2,
  target_major: '计算机科学',
  target_level: 'master',
  search_keyword: question || '',
  location: ''
})

// 3. 人物关系图谱 - POST请求
getPeopleGraphView({
  user_id: user.user_id,
  question: question || '',
  session_id: sessionId
})
```

### 后端返回数据格式

```json
{
  "success": true,
  "data": {
    "view_mode": "career",
    "title": "职业发展图谱",
    "nodes": [
      {
        "id": "node_1",
        "name": "Python",
        "type": "skill",
        "category": "skill",
        "metadata": {
          "status": "mastered",
          "level": "高级"
        },
        "position": { "x": 10, "y": 0, "z": 0 },
        "is_self": false
      }
    ],
    "edges": [  // 注意：后端返回的是edges，不是links
      {
        "source": "node_1",
        "target": "node_2",
        "type": "mastery",
        "weight": 0.8
      }
    ],
    "metadata": {
      "total_nodes": 10,
      "total_edges": 15
    }
  }
}
```

## 修复方案

### 1. 修改KnowledgeGraphService.ets

需要将GET请求改为POST请求，并传递正确的参数：

```typescript
/**
 * 获取职业星图 - 修复版
 */
async getCareerStarMap(userId: string): Promise<StarMapData> {
  // 改为POST请求，传递用户技能数据
  const requestData = {
    user_id: userId,
    mastered_skills: [],  // 空数组，让后端从知识图谱查询
    partial_skills: [],
    missing_skills: [],
    target_direction: 'Python工程师'
  };
  
  const result = await this.httpClient.post<Object>(
    ApiConstants.VERTICAL.CAREER_STAR_MAP,
    requestData
  );
  
  // 转换后端数据格式
  return this.convertBackendDataToStarMap(result.data, 'career');
}

/**
 * 获取教育星图 - 修复版
 */
async getEducationStarMap(userId: string): Promise<StarMapData> {
  const requestData = {
    user_id: userId,
    gpa: 3.5,
    gpa_max: 4.0,
    ranking_percent: 0.2,
    sat_act: 1450,
    research_experience: 0.6,
    publications: 2,
    target_major: '计算机科学',
    target_level: 'master',
    search_keyword: '',
    location: ''
  };
  
  const result = await this.httpClient.post<Object>(
    ApiConstants.VERTICAL.EDUCATION_STAR_MAP,
    requestData
  );
  
  return this.convertBackendDataToStarMap(result.data, 'education');
}

/**
 * 获取人际关系星图 - 修复版
 */
async getRelationshipStarMap(userId: string): Promise<StarMapData> {
  const requestData = {
    user_id: userId,
    question: '',
    session_id: null
  };
  
  const result = await this.httpClient.post<Object>(
    ApiConstants.VERTICAL.RELATIONSHIP_STAR_MAP,
    requestData
  );
  
  return this.convertBackendDataToStarMap(result.data, 'relationship');
}

/**
 * 转换后端数据格式为StarMapData
 */
private convertBackendDataToStarMap(backendData: any, type: string): StarMapData {
  const data = backendData.data || backendData;
  
  // 提取节点
  const nodes: KnowledgeNode[] = (data.nodes || []).map((node: any) => {
    return KnowledgeNode.create(
      node.id,
      node.name || node.label,
      node.type || 'default',
      node.category || node.type,
      node.position?.x || 0,
      node.position?.y || 0,
      node.position?.z || 0,
      10,  // size
      this.getNodeColor(node, type)
    );
  });
  
  // 提取连线 - 注意：后端返回的是edges，不是links
  const edges: KnowledgeEdge[] = (data.edges || data.links || []).map((edge: any) => {
    return KnowledgeEdge.create(
      edge.source,
      edge.target,
      edge.type || 'RELATED',
      edge.weight || edge.strength || 1.0
    );
  });
  
  // 提取层级信息
  const layers: string[] = this.extractLayers(nodes, type);
  
  return {
    nodes: nodes,
    edges: edges,
    layers: layers
  };
}

/**
 * 获取节点颜色
 */
private getNodeColor(node: any, type: string): string {
  if (type === 'career') {
    if (node.type === 'center') return '#FFD700';
    if (node.type === 'skill') {
      const status = node.metadata?.status;
      if (status === 'mastered') return '#4CAF50';
      if (status === 'partial') return '#FFC107';
      if (status === 'missing') return '#F44336';
      return '#4CAF50';
    }
    if (node.type === 'job') return '#2196F3';
    if (node.type === 'company') return '#9C27B0';
    return '#A0C4FF';
  } else if (type === 'education') {
    if (node.type === 'center') return '#FFD700';
    if (node.type === 'school') return '#4ECDC4';
    if (node.type === 'major') return '#95E1D3';
    if (node.type === 'action') return '#FA709A';
    return '#A0C4FF';
  } else {
    // relationship
    if (node.type === 'person' && node.is_self) return '#FFD700';
    if (node.type === 'person') return '#4D9EFF';
    if (node.type === 'relationship') return '#9575FF';
    return '#A0C4FF';
  }
}

/**
 * 提取层级信息
 */
private extractLayers(nodes: KnowledgeNode[], type: string): string[] {
  if (type === 'career') {
    return ['我', '技能', '岗位', '公司'];
  } else if (type === 'education') {
    return ['我', '学业', '目标院校', '行动计划'];
  } else {
    return ['我', '家人', '朋友', '同事'];
  }
}
```

### 2. 修改KnowledgeGraphPage.ets

移除测试数据生成逻辑，直接使用后端数据：

```typescript
async loadStarMaps() {
  console.info('[KnowledgeGraphPage] loadStarMaps - 开始加载, userId:', this.userId);
  this.isLoading = true;
  
  try {
    // 直接从后端加载，不使用测试数据
    const results = await Promise.all([
      this.kgService.getRelationshipStarMap(this.userId),
      this.kgService.getCareerStarMap(this.userId),
      this.kgService.getEducationStarMap(this.userId)
    ]);
    
    this.relationshipStarMap = results[0];
    this.careerStarMap = results[1];
    this.educationStarMap = results[2];
    
    console.info('[KnowledgeGraphPage] 星图数据加载完成:', {
      relationship: this.relationshipStarMap?.nodes.length || 0,
      career: this.careerStarMap?.nodes.length || 0,
      education: this.educationStarMap?.nodes.length || 0
    });
    
    // 加载当前标签页的星图到Native渲染器
    this.loadCurrentStarMapToNative();
  } catch (error) {
    console.error('[KnowledgeGraphPage] 加载星图失败:', error);
    promptAction.showToast({ 
      message: '加载星图失败: ' + error.message 
    });
  } finally {
    this.isLoading = false;
  }
}

// 删除 createMockStarMap 方法
```

### 3. 数据格式对比

#### 后端返回格式（edges）
```json
{
  "edges": [
    {
      "source": "node_1",
      "target": "node_2",
      "type": "mastery",
      "weight": 0.8
    }
  ]
}
```

#### 前端期望格式（edges）
```typescript
interface KnowledgeEdge {
  from: string;    // 对应后端的source
  to: string;      // 对应后端的target
  type: string;
  weight: number;
}
```

需要在转换函数中处理字段名差异：

```typescript
const edges: KnowledgeEdge[] = (data.edges || []).map((edge: any) => {
  return {
    from: edge.source,      // 映射source -> from
    to: edge.target,        // 映射target -> to
    type: edge.type || 'RELATED',
    weight: edge.weight || edge.strength || 1.0
  };
});
```

## 实施步骤

1. **备份现有代码**
   ```bash
   cp harmonyos/entry/src/main/ets/services/KnowledgeGraphService.ets \
      harmonyos/entry/src/main/ets/services/KnowledgeGraphService.ets.backup
   ```

2. **修改KnowledgeGraphService.ets**
   - 将GET请求改为POST请求
   - 添加数据转换函数
   - 处理后端返回的edges字段

3. **修改KnowledgeGraphPage.ets**
   - 移除测试数据生成逻辑
   - 添加错误处理
   - 优化加载状态显示

4. **测试验证**
   - 测试职业图谱加载
   - 测试教育图谱加载
   - 测试人物关系图谱加载
   - 验证节点和连线数据正确性

## 注意事项

1. **API端点已正确配置**：ApiConstants中的端点定义是正确的，无需修改
2. **后端返回edges不是links**：Web端在normalizeGraphView中做了兼容处理
3. **职业图谱使用同心圆布局**：后端返回的position字段包含预计算的3D坐标
4. **空技能列表**：传递空数组让后端从用户知识图谱中查询技能数据

## 预期效果

修复后，HarmonyOS端将：
- 显示真实的用户知识图谱数据
- 与Web端保持一致的数据展示
- 正确处理后端返回的节点和连线数据
- 支持职业、教育、人物关系三种图谱视图
