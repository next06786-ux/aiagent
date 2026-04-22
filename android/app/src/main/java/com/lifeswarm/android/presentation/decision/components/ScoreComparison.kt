package com.lifeswarm.android.presentation.decision.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.data.model.OptionSimulationState

/**
 * 评分对比组件
 * 对比多个选项的评分
 */
@Composable
fun ScoreComparison(
    optionStates: Map<String, OptionSimulationState>,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            // 标题
            Text(
                text = "方案评分对比",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(20.dp))
            
            // 找出最高分
            val maxScore = optionStates.values.maxOfOrNull { it.totalScore } ?: 0.0
            
            // 评分条
            optionStates.values.sortedByDescending { it.totalScore }.forEach { state ->
                ScoreBar(
                    optionTitle = state.optionTitle,
                    score = state.totalScore,
                    maxScore = maxScore,
                    isComplete = state.isComplete
                )
                Spacer(modifier = Modifier.height(12.dp))
            }
        }
    }
}

/**
 * 评分条
 */
@Composable
fun ScoreBar(
    optionTitle: String,
    score: Double,
    maxScore: Double,
    isComplete: Boolean,
    modifier: Modifier = Modifier
) {
    // 进度动画
    val animatedProgress by animateFloatAsState(
        targetValue = if (maxScore > 0) (score / maxScore).toFloat() else 0f,
        animationSpec = tween(
            durationMillis = 1000,
            easing = FastOutSlowInEasing
        ),
        label = "progress"
    )
    
    val scoreColor = getScoreColor(score)
    
    Column(modifier = modifier.fillMaxWidth()) {
        // 标题和评分
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = optionTitle,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f)
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Text(
                text = "${score.toInt()}",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = scoreColor
            )
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // 进度条
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(12.dp)
        ) {
            // 背景
            Surface(
                modifier = Modifier.fillMaxSize(),
                shape = RoundedCornerShape(6.dp),
                color = MaterialTheme.colorScheme.surfaceVariant
            ) {}
            
            // 进度
            Surface(
                modifier = Modifier
                    .fillMaxWidth(animatedProgress)
                    .fillMaxHeight(),
                shape = RoundedCornerShape(6.dp),
                color = scoreColor
            ) {}
        }
        
        // 完成状态
        if (isComplete) {
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "✓ 已完成",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF4CAF50)
            )
        }
    }
}

/**
 * 雷达图评分对比（简化版）
 */
@Composable
fun RadarScoreComparison(
    optionStates: Map<String, OptionSimulationState>,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "综合评分雷达图",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(20.dp))
            
            // 简化的雷达图（使用 Canvas 绘制）
            Box(
                modifier = Modifier.size(200.dp),
                contentAlignment = Alignment.Center
            ) {
                Canvas(modifier = Modifier.fillMaxSize()) {
                    val center = Offset(size.width / 2, size.height / 2)
                    val radius = size.minDimension / 2 * 0.8f
                    
                    // 绘制背景网格
                    for (i in 1..5) {
                        val r = radius * i / 5
                        drawCircle(
                            color = Color.Gray.copy(alpha = 0.2f),
                            radius = r,
                            center = center,
                            style = androidx.compose.ui.graphics.drawscope.Stroke(width = 1.dp.toPx())
                        )
                    }
                    
                    // 绘制每个选项的评分点
                    optionStates.values.forEachIndexed { index, state ->
                        val angle = (index * 360.0 / optionStates.size - 90).toFloat()
                        val rad = Math.toRadians(angle.toDouble())
                        val scoreRadius = radius * (state.totalScore / 100.0).toFloat()
                        
                        val x = center.x + (scoreRadius * Math.cos(rad)).toFloat()
                        val y = center.y + (scoreRadius * Math.sin(rad)).toFloat()
                        
                        drawCircle(
                            color = getScoreColor(state.totalScore),
                            radius = 8.dp.toPx(),
                            center = Offset(x, y)
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 图例
            optionStates.values.forEach { state ->
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(vertical = 4.dp)
                ) {
                    Surface(
                        modifier = Modifier.size(12.dp),
                        shape = RoundedCornerShape(6.dp),
                        color = getScoreColor(state.totalScore)
                    ) {}
                    
                    Spacer(modifier = Modifier.width(8.dp))
                    
                    Text(
                        text = "${state.optionTitle}: ${state.totalScore.toInt()}",
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }
    }
}

/**
 * 排名列表
 */
@Composable
fun ScoreRankingList(
    optionStates: Map<String, OptionSimulationState>,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp)
        ) {
            Text(
                text = "方案排名",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            optionStates.values
                .sortedByDescending { it.totalScore }
                .forEachIndexed { index, state ->
                    RankingItem(
                        rank = index + 1,
                        optionTitle = state.optionTitle,
                        score = state.totalScore,
                        isComplete = state.isComplete
                    )
                    
                    if (index < optionStates.size - 1) {
                        Divider(modifier = Modifier.padding(vertical = 12.dp))
                    }
                }
        }
    }
}

/**
 * 排名项
 */
@Composable
fun RankingItem(
    rank: Int,
    optionTitle: String,
    score: Double,
    isComplete: Boolean
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // 排名徽章
        Surface(
            modifier = Modifier.size(40.dp),
            shape = RoundedCornerShape(20.dp),
            color = when (rank) {
                1 -> Color(0xFFFFD700)  // 金色
                2 -> Color(0xFFC0C0C0)  // 银色
                3 -> Color(0xFFCD7F32)  // 铜色
                else -> MaterialTheme.colorScheme.surfaceVariant
            }
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = "$rank",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = if (rank <= 3) Color.White else MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        
        Spacer(modifier = Modifier.width(16.dp))
        
        // 选项信息
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = optionTitle,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            if (isComplete) {
                Text(
                    text = "已完成",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFF4CAF50)
                )
            }
        }
        
        // 评分
        Text(
            text = "${score.toInt()}",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = getScoreColor(score)
        )
    }
}
