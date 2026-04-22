package com.lifeswarm.android.presentation.decision.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.data.model.PersonaAgent
import com.lifeswarm.android.data.model.PersonaStatus

/**
 * 人格卡片组件
 * 显示单个 AI 人格的状态、评分和思考内容
 */
@Composable
fun PersonaCard(
    agent: PersonaAgent,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val statusColor = when (agent.status) {
        PersonaStatus.WAITING -> MaterialTheme.colorScheme.surfaceVariant
        PersonaStatus.THINKING -> MaterialTheme.colorScheme.primaryContainer
        PersonaStatus.COMPLETE -> MaterialTheme.colorScheme.tertiaryContainer
        PersonaStatus.ERROR -> MaterialTheme.colorScheme.errorContainer
    }
    
    val statusTextColor = when (agent.status) {
        PersonaStatus.WAITING -> MaterialTheme.colorScheme.onSurfaceVariant
        PersonaStatus.THINKING -> MaterialTheme.colorScheme.onPrimaryContainer
        PersonaStatus.COMPLETE -> MaterialTheme.colorScheme.onTertiaryContainer
        PersonaStatus.ERROR -> MaterialTheme.colorScheme.onErrorContainer
    }
    
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = statusColor
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = if (agent.status == PersonaStatus.THINKING) 4.dp else 2.dp
        )
    ) {
        Column(
            modifier = Modifier.padding(12.dp)
        ) {
            // 头部：头像 + 名称 + 状态
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth()
            ) {
                // 头像
                PersonaAvatar(
                    agent = agent,
                    size = 40.dp
                )
                
                Spacer(modifier = Modifier.width(12.dp))
                
                // 名称和状态
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = agent.name,
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold,
                        color = statusTextColor,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    
                    Text(
                        text = getStatusText(agent.status),
                        style = MaterialTheme.typography.bodySmall,
                        color = statusTextColor.copy(alpha = 0.7f)
                    )
                }
                
                // 评分（如果有）
                if (agent.score != null) {
                    ScoreBadge(score = agent.score)
                }
            }
            
            // 立场（如果有）
            if (agent.stance != null) {
                Spacer(modifier = Modifier.height(8.dp))
                StanceBadge(stance = agent.stance)
            }
            
            // 当前消息（思考气泡）
            if (agent.currentMessage != null && agent.status == PersonaStatus.THINKING) {
                Spacer(modifier = Modifier.height(8.dp))
                ThinkingBubble(
                    message = agent.currentMessage,
                    action = agent.messageAction
                )
            }
        }
    }
}

/**
 * 人格头像
 */
@Composable
fun PersonaAvatar(
    agent: PersonaAgent,
    size: androidx.compose.ui.unit.Dp,
    modifier: Modifier = Modifier
) {
    val icon = when (agent.status) {
        PersonaStatus.WAITING -> Icons.Default.Person
        PersonaStatus.THINKING -> Icons.Default.Psychology
        PersonaStatus.COMPLETE -> Icons.Default.CheckCircle
        PersonaStatus.ERROR -> Icons.Default.Error
    }
    
    val backgroundColor = when (agent.status) {
        PersonaStatus.WAITING -> MaterialTheme.colorScheme.surface
        PersonaStatus.THINKING -> MaterialTheme.colorScheme.primary
        PersonaStatus.COMPLETE -> MaterialTheme.colorScheme.tertiary
        PersonaStatus.ERROR -> MaterialTheme.colorScheme.error
    }
    
    val iconColor = when (agent.status) {
        PersonaStatus.WAITING -> MaterialTheme.colorScheme.onSurface
        PersonaStatus.THINKING -> MaterialTheme.colorScheme.onPrimary
        PersonaStatus.COMPLETE -> MaterialTheme.colorScheme.onTertiary
        PersonaStatus.ERROR -> MaterialTheme.colorScheme.onError
    }
    
    // 思考中的脉冲动画
    val scale by rememberInfiniteTransition(label = "scale").animateFloat(
        initialValue = 1f,
        targetValue = 1.1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )
    
    Box(
        modifier = modifier
            .size(size)
            .scale(if (agent.status == PersonaStatus.THINKING) scale else 1f)
            .background(backgroundColor, CircleShape)
            .border(2.dp, backgroundColor.copy(alpha = 0.3f), CircleShape),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = icon,
            contentDescription = agent.name,
            tint = iconColor,
            modifier = Modifier.size(size * 0.6f)
        )
    }
}

/**
 * 评分徽章
 */
@Composable
fun ScoreBadge(score: Double) {
    val scoreColor = when {
        score >= 70 -> Color(0xFF4CAF50)  // 绿色
        score >= 40 -> Color(0xFFFFC107)  // 黄色
        else -> Color(0xFFF44336)          // 红色
    }
    
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = scoreColor.copy(alpha = 0.2f),
        modifier = Modifier.padding(4.dp)
    ) {
        Text(
            text = "${score.toInt()}",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = scoreColor,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)
        )
    }
}

/**
 * 立场徽章
 */
@Composable
fun StanceBadge(stance: String) {
    val (icon, color) = when {
        stance.contains("支持") || stance.contains("赞同") -> 
            Icons.Default.ThumbUp to Color(0xFF4CAF50)
        stance.contains("反对") || stance.contains("质疑") -> 
            Icons.Default.ThumbDown to Color(0xFFF44336)
        stance.contains("中立") || stance.contains("谨慎") -> 
            Icons.Default.RemoveCircle to Color(0xFFFFC107)
        else -> 
            Icons.Default.Info to MaterialTheme.colorScheme.primary
    }
    
    Surface(
        shape = RoundedCornerShape(8.dp),
        color = color.copy(alpha = 0.1f),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(8.dp)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(16.dp)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Text(
                text = stance,
                style = MaterialTheme.typography.bodySmall,
                color = color,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

/**
 * 思考气泡
 */
@Composable
fun ThinkingBubble(
    message: String,
    action: String?
) {
    val alpha by rememberInfiniteTransition(label = "alpha").animateFloat(
        initialValue = 0.6f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )
    
    val actionIcon = when (action) {
        "question" -> Icons.Default.Help
        "support" -> Icons.Default.ThumbUp
        "challenge" -> Icons.Default.Warning
        "supplement" -> Icons.Default.Add
        else -> null
    }
    
    Surface(
        shape = RoundedCornerShape(8.dp),
        color = MaterialTheme.colorScheme.surface.copy(alpha = 0.5f),
        modifier = Modifier
            .fillMaxWidth()
            .alpha(alpha)
    ) {
        Row(
            modifier = Modifier.padding(8.dp),
            verticalAlignment = Alignment.Top
        ) {
            if (actionIcon != null) {
                Icon(
                    imageVector = actionIcon,
                    contentDescription = action,
                    modifier = Modifier.size(16.dp),
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(6.dp))
            }
            
            Text(
                text = message,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f),
                maxLines = 3,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

/**
 * 获取状态文本
 */
private fun getStatusText(status: PersonaStatus): String {
    return when (status) {
        PersonaStatus.WAITING -> "等待中..."
        PersonaStatus.THINKING -> "思考中..."
        PersonaStatus.COMPLETE -> "已完成"
        PersonaStatus.ERROR -> "出错"
    }
}
