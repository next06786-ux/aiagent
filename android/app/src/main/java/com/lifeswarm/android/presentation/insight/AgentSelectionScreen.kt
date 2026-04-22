package com.lifeswarm.android.presentation.insight

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Agent 选择界面
 */
@Composable
fun AgentSelectionScreen(
    onAgentSelected: (AgentType) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            "选择专业Agent",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            "点击Agent查看专业洞察报告",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Agent 卡片列表
        Column(
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            AgentType.values().forEach { agentType ->
                AgentCard(
                    agentType = agentType,
                    onClick = { onAgentSelected(agentType) }
                )
            }
        }
    }
}

/**
 * Agent 卡片
 */
@Composable
fun AgentCard(
    agentType: AgentType,
    onClick: () -> Unit
) {
    val color = when (agentType) {
        AgentType.RELATIONSHIP -> Color(0xFF10b981)
        AgentType.EDUCATION -> Color(0xFF3b82f6)
        AgentType.CAREER -> Color(0xFFf59e0b)
    }
    
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Agent 图标
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(color.copy(alpha = 0.2f)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    agentType.icon,
                    fontSize = 32.sp
                )
            }
            
            // Agent 信息
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    agentType.displayName,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    agentType.description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            // 查看按钮
            Button(
                onClick = onClick,
                colors = ButtonDefaults.buttonColors(
                    containerColor = color
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("查看报告")
            }
        }
    }
}

/**
 * Agent 加载界面
 */
@Composable
fun AgentLoadingScreen(agentType: AgentType) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(64.dp),
            strokeWidth = 6.dp
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            "${agentType.displayName}正在分析...",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            "正在通过RAG和Neo4j混合检索生成专业洞察报告",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
    }
}
