package com.lifeswarm.android.presentation.decision

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lifeswarm.android.data.model.PersonaAgent
import com.lifeswarm.android.data.repository.DecisionRepository
import kotlinx.coroutines.launch
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.PI

/**
 * 决策推演结果页面
 * 显示推演完成后的综合评估结果
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DecisionResultScreen(
    simulationId: String,
    onNavigateBack: () -> Unit,
    repository: DecisionRepository
) {
    var isLoading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }
    var result by remember { mutableStateOf<SimulationResult?>(null) }
    
    val scope = rememberCoroutineScope()
    
    // 加载推演结果
    LaunchedEffect(simulationId) {
        scope.launch {
            try {
                isLoading = true
                // TODO: 从 repository 加载结果
                // result = repository.getSimulationResult(simulationId)
                
                // 临时模拟数据
                result = SimulationResult(
                    simulationId = simulationId,
                    question = "示例决策问题",
                    selectedOption = "选项一",
                    overallScore = 75.5,
                    riskLevel = "中等",
                    executionConfidence = 0.82,
                    recommendation = "基于7位决策人格的综合分析，该方案具有较高的可行性。建议在执行前做好风险预案。",
                    agents = emptyList(),
                    keyInsights = listOf(
                        "该方案在长期收益方面表现突出",
                        "需要注意短期内的资源投入压力",
                        "建议分阶段实施以降低风险"
                    ),
                    dimensionScores = mapOf(
                        "可行性" to 80.0,
                        "收益性" to 75.0,
                        "风险度" to 65.0,
                        "创新性" to 70.0,
                        "稳定性" to 78.0
                    )
                )
                
                isLoading = false
            } catch (e: Exception) {
                error = e.message
                isLoading = false
            }
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("推演结果") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, "返回")
                    }
                },
                actions = {
                    IconButton(onClick = { /* TODO: 分享结果 */ }) {
                        Icon(Icons.Default.Share, "分享")
                    }
                }
            )
        }
    ) { padding ->
        when {
            isLoading -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            error != null -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        Icon(
                            Icons.Default.Error,
                            contentDescription = null,
                            modifier = Modifier.size(64.dp),
                            tint = MaterialTheme.colorScheme.error
                        )
                        Text(
                            error ?: "加载失败",
                            style = MaterialTheme.typography.bodyLarge
                        )
                        Button(onClick = onNavigateBack) {
                            Text("返回")
                        }
                    }
                }
            }
            result != null -> {
                ResultContent(
                    result = result!!,
                    modifier = Modifier.padding(padding)
                )
            }
        }
    }
}

@Composable
fun ResultContent(
    result: SimulationResult,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // 决策问题
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Column(
                    modifier = Modifier.padding(20.dp)
                ) {
                    Text(
                        "决策问题",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        result.question,
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "选择方案: ${result.selectedOption}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                    )
                }
            }
        }
        
        // 综合评分
        item {
            OverallScoreCard(
                score = result.overallScore,
                riskLevel = result.riskLevel,
                confidence = result.executionConfidence
            )
        }
        
        // 维度评分雷达图
        item {
            DimensionScoresCard(scores = result.dimensionScores)
        }
        
        // AI 推荐建议
        item {
            Card(
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(20.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            Icons.Default.Lightbulb,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary
                        )
                        Text(
                            "AI 推荐建议",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        result.recommendation,
                        style = MaterialTheme.typography.bodyMedium,
                        lineHeight = 24.sp
                    )
                }
            }
        }
        
        // 关键洞察
        item {
            Card(
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(20.dp)
                ) {
                    Text(
                        "关键洞察",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    result.keyInsights.forEach { insight ->
                        Row(
                            modifier = Modifier.padding(vertical = 6.dp),
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(CircleShape)
                                    .align(Alignment.CenterVertically),
                                contentAlignment = Alignment.Center
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(6.dp)
                                        .clip(CircleShape)
                                        .background(MaterialTheme.colorScheme.primary)
                                )
                            }
                            Text(
                                insight,
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }
            }
        }
        
        // 底部间距
        item {
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
fun OverallScoreCard(
    score: Double,
    riskLevel: String,
    confidence: Double
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Text(
                "综合评估",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSecondaryContainer
            )
            Spacer(modifier = Modifier.height(20.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                // 综合评分
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        "${score.toInt()}",
                        style = MaterialTheme.typography.displayLarge,
                        fontWeight = FontWeight.Bold,
                        color = when {
                            score >= 80 -> Color(0xFF4CAF50)
                            score >= 60 -> Color(0xFFFFA726)
                            else -> Color(0xFFEF5350)
                        }
                    )
                    Text(
                        "综合评分",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.7f)
                    )
                }
                
                // 风险等级
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = when (riskLevel) {
                            "低" -> Color(0xFF4CAF50).copy(alpha = 0.2f)
                            "中等" -> Color(0xFFFFA726).copy(alpha = 0.2f)
                            else -> Color(0xFFEF5350).copy(alpha = 0.2f)
                        }
                    ) {
                        Text(
                            riskLevel,
                            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = when (riskLevel) {
                                "低" -> Color(0xFF4CAF50)
                                "中等" -> Color(0xFFFFA726)
                                else -> Color(0xFFEF5350)
                            }
                        )
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "风险等级",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.7f)
                    )
                }
                
                // 执行信心
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        "${(confidence * 100).toInt()}%",
                        style = MaterialTheme.typography.displayMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        "执行信心",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.7f)
                    )
                }
            }
        }
    }
}

@Composable
fun DimensionScoresCard(scores: Map<String, Double>) {
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Text(
                "维度评分",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(20.dp))
            
            // 雷达图
            RadarChart(
                scores = scores,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(250.dp)
            )
            
            Spacer(modifier = Modifier.height(20.dp))
            
            // 详细分数列表
            scores.forEach { (dimension, score) ->
                DimensionScoreRow(
                    dimension = dimension,
                    score = score
                )
                Spacer(modifier = Modifier.height(12.dp))
            }
        }
    }
}

@Composable
fun DimensionScoreRow(
    dimension: String,
    score: Double
) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                dimension,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium
            )
            Text(
                "${score.toInt()}",
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )
        }
        Spacer(modifier = Modifier.height(6.dp))
        LinearProgressIndicator(
            progress = (score / 100).toFloat(),
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp)),
            color = when {
                score >= 80 -> Color(0xFF4CAF50)
                score >= 60 -> Color(0xFFFFA726)
                else -> Color(0xFFEF5350)
            }
        )
    }
}

@Composable
fun RadarChart(
    scores: Map<String, Double>,
    modifier: Modifier = Modifier
) {
    val dimensions = scores.keys.toList()
    val values = scores.values.toList()
    val maxScore = 100.0
    
    Canvas(modifier = modifier) {
        val center = Offset(size.width / 2, size.height / 2)
        val radius = size.minDimension / 2 * 0.8f
        val angleStep = (2 * PI / dimensions.size).toFloat()
        
        // 绘制背景网格（5层）
        for (level in 1..5) {
            val levelRadius = radius * level / 5
            val path = Path()
            
            dimensions.indices.forEach { i ->
                val angle = -PI.toFloat() / 2 + angleStep * i
                val x = center.x + levelRadius * cos(angle)
                val y = center.y + levelRadius * sin(angle)
                
                if (i == 0) {
                    path.moveTo(x, y)
                } else {
                    path.lineTo(x, y)
                }
            }
            path.close()
            
            drawPath(
                path = path,
                color = Color.Gray.copy(alpha = 0.2f),
                style = Stroke(width = 1.dp.toPx())
            )
        }
        
        // 绘制轴线
        dimensions.indices.forEach { i ->
            val angle = -PI.toFloat() / 2 + angleStep * i
            val endX = center.x + radius * cos(angle)
            val endY = center.y + radius * sin(angle)
            
            drawLine(
                color = Color.Gray.copy(alpha = 0.3f),
                start = center,
                end = Offset(endX, endY),
                strokeWidth = 1.dp.toPx()
            )
        }
        
        // 绘制数据区域
        val dataPath = Path()
        values.forEachIndexed { i, value ->
            val angle = -PI.toFloat() / 2 + angleStep * i
            val valueRadius = radius * (value / maxScore).toFloat()
            val x = center.x + valueRadius * cos(angle)
            val y = center.y + valueRadius * sin(angle)
            
            if (i == 0) {
                dataPath.moveTo(x, y)
            } else {
                dataPath.lineTo(x, y)
            }
        }
        dataPath.close()
        
        // 填充数据区域
        drawPath(
            path = dataPath,
            color = Color(0xFF2196F3).copy(alpha = 0.3f)
        )
        
        // 绘制数据边界
        drawPath(
            path = dataPath,
            color = Color(0xFF2196F3),
            style = Stroke(width = 2.dp.toPx())
        )
        
        // 绘制数据点
        values.forEachIndexed { i, value ->
            val angle = -PI.toFloat() / 2 + angleStep * i
            val valueRadius = radius * (value / maxScore).toFloat()
            val x = center.x + valueRadius * cos(angle)
            val y = center.y + valueRadius * sin(angle)
            
            drawCircle(
                color = Color(0xFF2196F3),
                radius = 4.dp.toPx(),
                center = Offset(x, y)
            )
        }
    }
}

// 数据模型
data class SimulationResult(
    val simulationId: String,
    val question: String,
    val selectedOption: String,
    val overallScore: Double,
    val riskLevel: String,
    val executionConfidence: Double,
    val recommendation: String,
    val agents: List<PersonaAgent>,
    val keyInsights: List<String>,
    val dimensionScores: Map<String, Double>
)
