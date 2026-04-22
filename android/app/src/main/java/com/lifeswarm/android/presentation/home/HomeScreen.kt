package com.lifeswarm.android.presentation.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.presentation.auth.AuthViewModel

/**
 * 主页 - 对应 web/src/pages/HomePage.tsx
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    authViewModel: AuthViewModel,
    onNavigateToAuth: () -> Unit,
    onNavigateToChat: () -> Unit,
    onNavigateToDecision: () -> Unit,
    onNavigateToKnowledgeGraph: () -> Unit,
    onNavigateToInsights: () -> Unit,
    onNavigateToParallelLife: () -> Unit,
    onNavigateToSocial: () -> Unit,
    onNavigateToProfile: () -> Unit
) {
    val user by authViewModel.user.collectAsState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Column {
                        Text("择境", style = MaterialTheme.typography.headlineSmall)
                        Text("ChoiceRealm", style = MaterialTheme.typography.labelSmall)
                    }
                },
                actions = {
                    IconButton(onClick = onNavigateToProfile) {
                        Icon(Icons.Default.Person, "个人中心")
                    }
                    IconButton(onClick = {
                        authViewModel.logout()
                        onNavigateToAuth()
                    }) {
                        Icon(Icons.Default.ExitToApp, "退出登录")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // 欢迎卡片
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp)
                ) {
                    Text(
                        text = "欢迎回来，${user?.nickname ?: user?.username ?: "用户"}！",
                        style = MaterialTheme.typography.headlineMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "探索你的人生可能性",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                    )
                }
            }
            
            Text(
                text = "核心功能",
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
            )
            
            // 功能卡片网格
            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(getFeatureCards()) { card ->
                    FeatureCard(
                        title = card.title,
                        description = card.description,
                        icon = card.icon,
                        onClick = when (card.id) {
                            "chat" -> onNavigateToChat
                            "decision" -> onNavigateToDecision
                            "knowledge" -> onNavigateToKnowledgeGraph
                            "insights" -> onNavigateToInsights
                            "parallel-life" -> onNavigateToParallelLife
                            "social" -> onNavigateToSocial
                            else -> {{}}
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun FeatureCard(
    title: String,
    description: String,
    icon: ImageVector,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .height(160.dp),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(32.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            
            Column {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                
                Spacer(modifier = Modifier.height(4.dp))
                
                Text(
                    text = description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2
                )
            }
        }
    }
}

data class FeatureCardData(
    val id: String,
    val title: String,
    val description: String,
    val icon: ImageVector
)

fun getFeatureCards() = listOf(
    FeatureCardData(
        id = "chat",
        title = "AI 对话",
        description = "与 AI 核心实时协作",
        icon = Icons.Default.Chat
    ),
    FeatureCardData(
        id = "decision",
        title = "决策副本",
        description = "多维度智能评估",
        icon = Icons.Default.AccountTree
    ),
    FeatureCardData(
        id = "knowledge",
        title = "知识星图",
        description = "记忆网络构建",
        icon = Icons.Default.Hub
    ),
    FeatureCardData(
        id = "insights",
        title = "智慧洞察",
        description = "涌现发现与行为分析",
        icon = Icons.Default.Lightbulb
    ),
    FeatureCardData(
        id = "parallel-life",
        title = "平行人生",
        description = "探索人生可能性",
        icon = Icons.Default.Psychology
    ),
    FeatureCardData(
        id = "social",
        title = "好友",
        description = "管理你的好友关系",
        icon = Icons.Default.People
    )
)
