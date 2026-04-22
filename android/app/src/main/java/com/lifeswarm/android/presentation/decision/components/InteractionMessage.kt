package com.lifeswarm.android.presentation.decision.components

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.data.model.PersonaInteraction
import java.text.SimpleDateFormat
import java.util.*

/**
 * 交互消息组件
 * 显示人格之间的对话消息
 */
@Composable
fun InteractionMessage(
    interaction: PersonaInteraction,
    fromName: String,
    toName: String,
    modifier: Modifier = Modifier
) {
    // 入场动画
    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        visible = true
    }
    
    AnimatedVisibility(
        visible = visible,
        enter = fadeIn(animationSpec = tween(300)) + 
                slideInVertically(
                    initialOffsetY = { it / 2 },
                    animationSpec = tween(300)
                ),
        modifier = modifier
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(
                containerColor = getInteractionColor(interaction.type).copy(alpha = 0.1f)
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(
                modifier = Modifier.padding(12.dp)
            ) {
                // 头部：发送者 → 接收者
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.weight(1f)
                    ) {
                        // 交互类型图标
                        InteractionTypeIcon(
                            type = interaction.type,
                            action = interaction.action
                        )
                        
                        Spacer(modifier = Modifier.width(8.dp))
                        
                        // 发送者 → 接收者
                        Text(
                            text = fromName,
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                        
                        Icon(
                            imageVector = Icons.Default.ArrowForward,
                            contentDescription = null,
                            modifier = Modifier
                                .size(16.dp)
                                .padding(horizontal = 4.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        
                        Text(
                            text = toName,
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.secondary
                        )
                    }
                    
                    // 时间戳
                    Text(
                        text = formatTime(interaction.timestamp),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // 消息内容
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = MaterialTheme.colorScheme.surface.copy(alpha = 0.5f)
                ) {
                    Text(
                        text = interaction.message,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }
        }
    }
}

/**
 * 交互类型图标
 */
@Composable
fun InteractionTypeIcon(
    type: String,
    action: String?,
    modifier: Modifier = Modifier
) {
    val (icon, color) = when (action ?: type) {
        "question", "质疑" -> Icons.Default.Help to Color(0xFFFFC107)
        "support", "支持" -> Icons.Default.ThumbUp to Color(0xFF4CAF50)
        "challenge", "反对" -> Icons.Default.Warning to Color(0xFFF44336)
        "supplement", "补充" -> Icons.Default.Add to Color(0xFF2196F3)
        "讨论" -> Icons.Default.Chat to Color(0xFF9C27B0)
        else -> Icons.Default.Forum to MaterialTheme.colorScheme.primary
    }
    
    // 脉冲动画
    val scale by rememberInfiniteTransition(label = "scale").animateFloat(
        initialValue = 1f,
        targetValue = 1.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )
    
    Box(
        modifier = modifier
            .size(32.dp)
            .background(color.copy(alpha = 0.2f), RoundedCornerShape(8.dp)),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = icon,
            contentDescription = type,
            tint = color,
            modifier = Modifier.size(20.dp)
        )
    }
}

/**
 * 获取交互类型颜色
 */
private fun getInteractionColor(type: String): Color {
    return when (type) {
        "质疑" -> Color(0xFFFFC107)
        "支持" -> Color(0xFF4CAF50)
        "反对" -> Color(0xFFF44336)
        "补充" -> Color(0xFF2196F3)
        "讨论" -> Color(0xFF9C27B0)
        else -> Color(0xFF607D8B)
    }
}

/**
 * 格式化时间
 */
private fun formatTime(timestamp: Long): String {
    val sdf = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
    return sdf.format(Date(timestamp))
}

/**
 * 紧凑型交互消息（用于列表）
 */
@Composable
fun CompactInteractionMessage(
    interaction: PersonaInteraction,
    fromName: String,
    toName: String,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        InteractionTypeIcon(
            type = interaction.type,
            action = interaction.action,
            modifier = Modifier.size(24.dp)
        )
        
        Spacer(modifier = Modifier.width(8.dp))
        
        Column(modifier = Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = fromName,
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                Icon(
                    imageVector = Icons.Default.ArrowForward,
                    contentDescription = null,
                    modifier = Modifier
                        .size(12.dp)
                        .padding(horizontal = 2.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = toName,
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.secondary
                )
            }
            
            Text(
                text = interaction.message,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 2
            )
        }
        
        Text(
            text = formatTime(interaction.timestamp),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
