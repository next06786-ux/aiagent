package com.lifeswarm.android.presentation.decision.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * 评分卡片组件
 * 显示选项的综合评分
 */
@Composable
fun ScoreCard(
    score: Double,
    optionTitle: String,
    isComplete: Boolean,
    modifier: Modifier = Modifier
) {
    // 评分动画
    val animatedScore by animateFloatAsState(
        targetValue = score.toFloat(),
        animationSpec = tween(
            durationMillis = 1000,
            easing = FastOutSlowInEasing
        ),
        label = "score"
    )
    
    val scoreColor = getScoreColor(animatedScore.toDouble())
    val scoreLevel = getScoreLevel(animatedScore.toDouble())
    
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = scoreColor.copy(alpha = 0.1f)
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // 标题
            Text(
                text = optionTitle,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 圆形进度条 + 评分
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier.size(160.dp)
            ) {
                // 圆形进度条
                CircularScoreIndicator(
                    score = animatedScore.toDouble(),
                    color = scoreColor
                )
                
                // 中心评分
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "${animatedScore.toInt()}",
                        style = MaterialTheme.typography.displayLarge,
                        fontWeight = FontWeight.Bold,
                        color = scoreColor,
                        fontSize = 48.sp
                    )
                    Text(
                        text = "/ 100",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 评分等级
            ScoreLevelBadge(
                level = scoreLevel,
                color = scoreColor
            )
            
            // 完成状态
            if (isComplete) {
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.CheckCircle,
                        contentDescription = null,
                        tint = Color(0xFF4CAF50),
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "推演完成",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color(0xFF4CAF50),
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

/**
 * 圆形评分指示器
 */
@Composable
fun CircularScoreIndicator(
    score: Double,
    color: Color,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier.fillMaxSize()) {
        val strokeWidth = 12.dp.toPx()
        val diameter = size.minDimension
        val radius = (diameter - strokeWidth) / 2
        val topLeft = Offset(
            x = (size.width - diameter) / 2 + strokeWidth / 2,
            y = (size.height - diameter) / 2 + strokeWidth / 2
        )
        val arcSize = Size(diameter - strokeWidth, diameter - strokeWidth)
        
        // 背景圆环
        drawArc(
            color = color.copy(alpha = 0.2f),
            startAngle = -90f,
            sweepAngle = 360f,
            useCenter = false,
            topLeft = topLeft,
            size = arcSize,
            style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
        )
        
        // 进度圆环
        val sweepAngle = (score / 100.0 * 360.0).toFloat()
        drawArc(
            color = color,
            startAngle = -90f,
            sweepAngle = sweepAngle,
            useCenter = false,
            topLeft = topLeft,
            size = arcSize,
            style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
        )
    }
}

/**
 * 评分等级徽章
 */
@Composable
fun ScoreLevelBadge(
    level: String,
    color: Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(20.dp),
        color = color.copy(alpha = 0.2f)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = when (level) {
                    "优秀" -> Icons.Default.Star
                    "良好" -> Icons.Default.ThumbUp
                    "一般" -> Icons.Default.Remove
                    else -> Icons.Default.ThumbDown
                },
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = level,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = color
            )
        }
    }
}

/**
 * 紧凑型评分卡片
 */
@Composable
fun CompactScoreCard(
    score: Double,
    optionTitle: String,
    modifier: Modifier = Modifier
) {
    val scoreColor = getScoreColor(score)
    
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = scoreColor.copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = optionTitle,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = getScoreLevel(score),
                    style = MaterialTheme.typography.bodySmall,
                    color = scoreColor
                )
            }
            
            // 评分
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = scoreColor.copy(alpha = 0.2f)
            ) {
                Text(
                    text = "${score.toInt()}",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                    color = scoreColor,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                )
            }
        }
    }
}

/**
 * 获取评分颜色
 */
fun getScoreColor(score: Double): Color {
    return when {
        score >= 80 -> Color(0xFF4CAF50)  // 绿色 - 优秀
        score >= 60 -> Color(0xFF8BC34A)  // 浅绿 - 良好
        score >= 40 -> Color(0xFFFFC107)  // 黄色 - 一般
        score >= 20 -> Color(0xFFFF9800)  // 橙色 - 较差
        else -> Color(0xFFF44336)          // 红色 - 差
    }
}

/**
 * 获取评分等级
 */
fun getScoreLevel(score: Double): String {
    return when {
        score >= 80 -> "优秀"
        score >= 60 -> "良好"
        score >= 40 -> "一般"
        score >= 20 -> "较差"
        else -> "差"
    }
}
