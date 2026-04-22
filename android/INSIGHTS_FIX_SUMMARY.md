# 智慧洞察崩溃修复总结

## 问题
Android客户端智慧洞察功能点击任意Agent生成报告后崩溃。

## 根本原因
1. **类型不匹配**：`layer_timing` 定义为Int，后端返回Double
2. **空值处理**：必需字段没有默认值，JSON缺少字段时解析失败
3. **类型转换**：`dataSources` Map访问时没有类型检查

## 修复内容

### 1. InsightModels.kt - 数据模型容错
```kotlin
// 所有字段添加默认值
data class AgentInsightReport(
    @SerializedName("insight_id") val insightId: String = "",
    @SerializedName("agent_type") val agentType: String = "",
    @SerializedName("title") val title: String = "",
    @SerializedName("summary") val summary: String = "",
    @SerializedName("confidence_score") val confidenceScore: Double = 0.0,
    @SerializedName("generated_at") val generatedAt: String = "",
    @SerializedName("decision_logic") val decisionLogic: DecisionLogic? = null,
    @SerializedName("layer_timing") val layerTiming: Map<String, Double>? = null
)

data class KeyFinding(
    @SerializedName("type") val type: String = "",
    @SerializedName("title") val title: String = "",
    @SerializedName("description") val description: String = "",
    @SerializedName("importance") val importance: String = "low"
)

// Recommendation、MLEvaluation、ReasoningStep 同样添加默认值
```

### 2. InsightRepository.kt - JSON解析增强
```kotlin
// 使用宽松的Gson配置
private val gson = com.google.gson.GsonBuilder()
    .setLenient()
    .serializeNulls()
    .create()

// 添加详细日志
Log.d(TAG, "生成XXX洞察响应码: ${response.code}")
Log.d(TAG, "生成XXX洞察响应体前500字符: ${responseBody.take(500)}")
Log.d(TAG, "API响应解析成功，包含键: ${apiResponse.keys}")
Log.d(TAG, "报告对象解析成功: ${report.insightId}")
```

### 3. AgentReportScreen.kt - 安全的类型转换
```kotlin
// 安全转换dataSources中的值
val ragNodes = when (val value = report.dataSources["rag_nodes"]) {
    is Number -> value.toInt()
    is String -> value.toIntOrNull() ?: 0
    else -> 0
}
```

### 4. InsightsViewModel.kt - 增强日志
```kotlin
Log.d(TAG, "开始生成${agentType.displayName}报告")
Log.d(TAG, "报告ID: ${report.insightId}")
Log.d(TAG, "关键发现数量: ${report.keyFindings.size}")
```

## 修改的文件
1. `android/app/src/main/java/com/lifeswarm/android/data/model/InsightModels.kt`
2. `android/app/src/main/java/com/lifeswarm/android/data/repository/InsightRepository.kt`
3. `android/app/src/main/java/com/lifeswarm/android/presentation/insight/AgentReportScreen.kt`
4. `android/app/src/main/java/com/lifeswarm/android/presentation/insight/InsightsViewModel.kt`

## 调试方法
```bash
# 查看Insight相关日志
adb logcat | grep -E "InsightRepository|InsightsViewModel"

# 查看所有错误
adb logcat *:E

# 保存完整日志
adb logcat -d > crash_log.txt
```

## 关键日志标签
- `InsightRepository` - API调用和JSON解析
- `InsightsViewModel` - 业务逻辑

## 预期结果
✅ 正确解析后端返回的浮点数
✅ 安全处理空值和缺失字段
✅ 正确转换不同类型的值
✅ 不再崩溃，正常展示Agent报告

## 如果仍然崩溃
请提供完整的Logcat日志：
```bash
adb logcat -d > crash_log.txt
```

查看日志中的错误信息，特别关注：
- `InsightRepository` 标签的JSON解析错误
- `InsightsViewModel` 标签的业务逻辑错误
- 任何包含 `Exception` 或 `Error` 的行
