package com.lifeswarm.android.presentation.decision.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.data.model.PersonaAgent

/**
 * 人格网格布局
 * 以网格形式显示所有 AI 人格
 */
@Composable
fun PersonaGrid(
    agents: List<PersonaAgent>,
    onAgentClick: (PersonaAgent) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        // 标题
        Text(
            text = "AI 人格分析团队",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
        )
        
        if (agents.isEmpty()) {
            // 空状态
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp)
            ) {
                Text(
                    text = "等待人格团队初始化...",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            // 网格布局
            LazyVerticalGrid(
                columns = GridCells.Fixed(2),  // 2列网格
                contentPadding = PaddingValues(16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                items(agents) { agent ->
                    PersonaCard(
                        agent = agent,
                        onClick = { onAgentClick(agent) }
                    )
                }
            }
        }
    }
}

/**
 * 紧凑型人格网格（用于小屏幕或预览）
 */
@Composable
fun CompactPersonaGrid(
    agents: List<PersonaAgent>,
    onAgentClick: (PersonaAgent) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        LazyVerticalGrid(
            columns = GridCells.Adaptive(minSize = 140.dp),  // 自适应列数
            contentPadding = PaddingValues(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            items(agents) { agent ->
                PersonaCard(
                    agent = agent,
                    onClick = { onAgentClick(agent) }
                )
            }
        }
    }
}
