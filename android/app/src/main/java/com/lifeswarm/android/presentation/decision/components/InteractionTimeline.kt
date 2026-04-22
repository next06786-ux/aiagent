package com.lifeswarm.android.presentation.decision.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.data.model.PersonaAgent
import com.lifeswarm.android.data.model.PersonaInteraction

/**
 * 交互时间线组件
 * 按时间顺序显示人格之间的交互
 */
@Composable
fun InteractionTimeline(
    interactions: List<PersonaInteraction>,
    agents: List<PersonaAgent>,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()
    
    // 自动滚动到最新消息
    LaunchedEffect(interactions.size) {
        if (interactions.isNotEmpty()) {
            listState.animateScrollToItem(interactions.size - 1)
        }
    }
    
    Column(modifier = modifier) {
        // 标题
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "人格交互",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            
            if (interactions.isNotEmpty()) {
                Text(
                    text = "${interactions.size} 条交互",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        
        if (interactions.isEmpty()) {
            // 空状态
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "等待人格交互...",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            // 交互列表
            LazyColumn(
                state = listState,
                modifier = Modifier.fillMaxWidth(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(interactions) { interaction ->
                    val fromAgent = agents.find { it.id == interaction.from }
                    val toAgent = agents.find { it.id == interaction.to }
                    
                    InteractionMessage(
                        interaction = interaction,
                        fromName = fromAgent?.name ?: "未知",
                        toName = toAgent?.name ?: "未知"
                    )
                }
            }
        }
    }
}

/**
 * 紧凑型交互时间线（用于小屏幕）
 */
@Composable
fun CompactInteractionTimeline(
    interactions: List<PersonaInteraction>,
    agents: List<PersonaAgent>,
    maxItems: Int = 5,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        Text(
            text = "最近交互",
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
        )
        
        if (interactions.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "暂无交互",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                interactions.takeLast(maxItems).forEach { interaction ->
                    val fromAgent = agents.find { it.id == interaction.from }
                    val toAgent = agents.find { it.id == interaction.to }
                    
                    CompactInteractionMessage(
                        interaction = interaction,
                        fromName = fromAgent?.name ?: "未知",
                        toName = toAgent?.name ?: "未知"
                    )
                    
                    Divider()
                }
            }
        }
    }
}

/**
 * 交互统计卡片
 */
@Composable
fun InteractionStatsCard(
    interactions: List<PersonaInteraction>,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = "交互统计",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // 按类型统计
            val typeStats = interactions.groupBy { it.type }
            
            typeStats.forEach { (type, list) ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = type,
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        text = "${list.size} 次",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }
        }
    }
}
