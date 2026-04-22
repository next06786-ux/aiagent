# 智慧洞察崩溃调试指南

## 已实施的修复

### 1. 数据模型修复
- ✅ `layer_timing` 类型改为 `Map<String, Double>`（浮点数）
- ✅ `decisionLogic` 改为可空类型
- ✅ 所有嵌套对象字段添加默认值
- ✅ `AgentInsightReport` 所有必需字段添加默认值

### 2. JSON解析增强
- ✅ 使用 `GsonBuilder().setLenient().serializeNulls()`
- ✅ 添加详细的解析日志
- ✅ 添加异常捕获和堆栈跟踪

### 3. 异常处理策略
- ✅ Repository层：捕获所有JSON解析异常
- ✅ ViewModel层：使用Result类型安全处理
- ✅ UI层：依赖数据模型的默认值保证安全渲染
- ⚠️ 注意：Compose不支持在Composable函数周围使用try-catch

### 4. 日志增强
- ✅ Repository层详细日志
- ✅ ViewModel层详细日志
- ✅ 所有异常打印堆栈跟踪

## 如何查看崩溃日志

### 方法1：使用Android Studio Logcat

1. 打开Android Studio
2. 点击底部的 "Logcat" 标签
3. 在过滤器中输入：`InsightRepository` 或 `InsightsViewModel` 或 `AgentReportScreen`
4. 重现崩溃
5. 查看红色的错误日志

### 方法2：使用ADB命令行

```bash
# 清除旧日志
adb logcat -c

# 实时查看日志（过滤Insight相关）
adb logcat | grep -E "InsightRepository|InsightsViewModel|AgentReportScreen"

# 或者查看所有错误
adb logcat *:E

# 保存日志到文件
adb logcat > insight_crash.log
```

### 方法3：捕获完整崩溃报告

```bash
# 捕获崩溃堆栈
adb logcat -d > full_crash_log.txt
```

## 关键日志标签

查找以下标签的日志：

1. **InsightRepository** - API调用和JSON解析
   - `生成人际关系洞察请求`
   - `生成人际关系洞察响应码`
   - `报告JSON前500字符`
   - `JSON解析失败`

2. **InsightsViewModel** - 业务逻辑
   - `开始生成XXX报告`
   - `生成XXX报告成功`
   - `报告ID`
   - `关键发现数量`

3. **AgentReportScreen** - UI渲染
   - `渲染报告标题失败`
   - `渲染摘要失败`
   - `渲染关键发现失败`

## 常见崩溃原因和解决方案

### 1. NumberFormatException
**症状：** `Expected an int but was 0.088`
**原因：** 字段类型不匹配
**解决：** ✅ 已修复 - 改为Double类型

### 2. NullPointerException
**症状：** `Attempt to invoke ... on a null object reference`
**原因：** 访问了空对象
**解决：** ✅ 已修复 - 添加空值检查和默认值

### 3. JsonSyntaxException
**症状：** `Expected BEGIN_OBJECT but was STRING`
**原因：** JSON结构不匹配
**解决：** ✅ 已修复 - 使用宽松的Gson配置

### 4. ClassCastException
**症状：** `Cannot cast Double to Integer`
**原因：** 类型转换错误
**解决：** ✅ 已修复 - 安全的类型转换

## 调试步骤

### 第1步：确认API响应
查看日志中的：
```
生成人际关系洞察响应码: 200
生成人际关系洞察响应体前500字符: {"report":{"insight_id":"...
```

如果响应码不是200，检查：
- Token是否有效
- 网络连接是否正常
- 后端服务是否运行

### 第2步：确认JSON解析
查看日志中的：
```
API响应解析成功，包含键: [report, success]
报告JSON长度: 1234
```

如果解析失败，查看：
- `JSON解析失败` 错误信息
- `失败的JSON` 内容

### 第3步：确认对象创建
查看日志中的：
```
报告对象解析成功: insight_123
报告标题: XXX分析报告
```

如果对象创建失败，检查：
- 哪个字段导致失败
- 该字段的实际值和期望类型

### 第4步：确认UI渲染
查看日志中的：
```
生成XXX报告成功
关键发现数量: 3
推荐建议数量: 5
```

如果UI渲染失败，查看：
- `渲染XXX失败` 错误信息
- 具体是哪个组件失败

## 测试清单

- [ ] 人际关系Agent - 点击生成
- [ ] 人际关系Agent - 查看完整报告
- [ ] 教育升学Agent - 点击生成
- [ ] 教育升学Agent - 查看完整报告
- [ ] 职业规划Agent - 点击生成
- [ ] 职业规划Agent - 查看完整报告
- [ ] 返回Agent选择
- [ ] 切换到跨领域分析
- [ ] 切换回单Agent分析

## 如果仍然崩溃

请提供以下信息：

1. **完整的Logcat日志**
   ```bash
   adb logcat -d > crash_log.txt
   ```

2. **崩溃时的具体操作**
   - 点击了哪个Agent
   - 是否显示了加载界面
   - 崩溃发生在哪个阶段

3. **后端响应示例**
   - 从日志中复制 `响应体前500字符`
   - 或者完整的响应JSON

4. **设备信息**
   - Android版本
   - 设备型号
   - 应用版本

## 临时解决方案

如果问题持续，可以尝试：

### 方案1：使用模拟数据
在 `InsightRepository` 中添加：
```kotlin
// 临时：返回模拟数据用于测试UI
return Result.success(AgentInsightReport(
    insightId = "test_123",
    agentType = "relationship",
    title = "测试报告",
    summary = "这是一个测试摘要",
    // ... 其他字段
))
```

### 方案2：跳过问题字段
在 `AgentReportScreen` 中注释掉崩溃的部分：
```kotlin
// 暂时注释掉导致崩溃的部分
// if (report.decisionLogic != null) {
//     item { DecisionLogicSection(report) }
// }
```

## 下一步

1. 运行应用并重现崩溃
2. 收集Logcat日志
3. 查找上述关键日志标签
4. 根据错误信息定位问题
5. 如需帮助，提供完整日志
