package com.lifeswarm.android.presentation.insight

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lifeswarm.android.data.model.CrossDomainAnalysisResult

/**
 * 跨领域综合分析界面
 */
@Composable
fun CrossDomainAnalysisScreen(
    query: String,
    result: CrossDomainAnalysisResult?,
    isLoading: Boolean,
    onQueryChange: (String) -> Unit,
    onAnalyze: () -> Unit
) {
    var selectedTab by remember { mutableStateOf(0) }
    val tabs = listOf("综合摘要", "跨领域模式", "战略建议", "行动计划")
    
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // 标题
        item {
            Column {
                Text(
                    "🔗 跨领域综合分析",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "多Agent协作 · 发现跨领域关联 · 生成综合战略",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        
        // 查询输入
        item {
            QueryInputSection(
                query = query,
                onQueryChange = onQueryChange,
                onAnalyze = onAnalyze,
                isLoading = isLoading
            )
        }
        
        // 快捷查询
        item {
            QuickQueriesSection(onQuerySelected = onQueryChange)
        }
        
        // 加载状态
        if (isLoading) {
            item {
                LoadingSection()
            }
        }
        
        // 分析结果
        if (result != null && !isLoading) {
            // 执行摘要
            item {
                ExecutionSummaryCard(result)
            }
            
            // 标签页
            item {
                TabRow(
                    selectedTabIndex = selectedTab,
                    containerColor = MaterialTheme.colorScheme.surface
                ) {
                    tabs.forEachIndexed { index, title ->
                        Tab(
                            selected = selectedTab == index,
                            onClick = { selectedTab = index },
                            text = { Text(title, fontSize = 13.sp) }
                        )
                    }
                }
            }
            
            // 标签页内容
            when (selectedTab) {
                0 -> item { SummaryTabContent(result) }
                1 -> item { PatternsTabContent(result) }
                2 -> item { RecommendationsTabContent(result) }
                3 -> item { ActionPlanTabContent(result) }
            }
        }
    }
}

/**
 * 查询输入部分
 */
@Composable
fun QueryInputSection(
    query: String,
    onQueryChange: (String) -> Unit,
    onAnalyze: () -> Unit,
    isLoading: Boolean
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            OutlinedTextField(
                value = query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("输入你的综合分析需求...") },
                minLines = 3,
                maxLines = 5,
                shape = RoundedCornerShape(12.dp)
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Button(
                onClick = onAnalyze,
                modifier = Modifier.fillMaxWidth(),
                enabled = !isLoading && query.isNotBlank(),
                shape = RoundedCornerShape(12.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("分析中...")
                } else {
                    Text("开始分析")
                }
            }
        }
    }
}

/**
 * 快捷查询部分
 */
@Composable
fun QuickQueriesSection(onQuerySelected: (String) -> Unit) {
    val quickQueries = listOf(
        "综合分析我的人际关系、教育背景和职业发展",
        "我的人际关系如何影响职业发展？",
        "教育背景和人脉资源如何协同提升职业竞争力？",
        "如何平衡学业、人际关系和职业规划？"
    )
    
    Column {
        Text(
            "快捷查询",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(8.dp))
        
        quickQueries.forEach { query ->
            OutlinedButton(
                onClick = { onQuerySelected(query) },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    query,
                    style = MaterialTheme.typography.bodySmall,
                    textAlign = TextAlign.Start,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
    }
}

/**
 * 加载部分
 */
@Composable
fun LoadingSection() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            CircularProgressIndicator(
                modifier = Modifier.size(48.dp),
                strokeWidth = 4.dp
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            val steps = listOf(
                "📦 初始化共享记忆空间...",
                "🤖 执行多Agent协作...",
                "🔗 识别跨领域关联...",
                "🎯 生成综合战略..."
            )
            
            steps.forEach { step ->
                Text(
                    step,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(vertical = 4.dp)
                )
            }
        }
    }
}

/**
 * 执行摘要卡片
 */
@Composable
fun ExecutionSummaryCard(result: CrossDomainAnalysisResult) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            SummaryItem(
                label = "执行Agent",
                value = "${result.executionSummary.totalAgents} 个"
            )
            SummaryItem(
                label = "执行时间",
                value = "${result.executionSummary.executionTime.toInt()}秒"
            )
            SummaryItem(
                label = "分析类型",
                value = result.analysisType
            )
        }
    }
}

@Composable
fun SummaryItem(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            value,
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold
        )
    }
}

/**
 * 综合摘要标签页
 */
@Composable
fun SummaryTabContent(result: CrossDomainAnalysisResult) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text(
                    result.crossDomainAnalysis.summary,
                    style = MaterialTheme.typography.bodyLarge,
                    lineHeight = 24.sp
                )
            }
        }
        
        // 整合洞察
        if (result.crossDomainAnalysis.integratedInsights.isNotEmpty()) {
            Text(
                "🔍 整合洞察",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            
            result.crossDomainAnalysis.integratedInsights.forEach { insight ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                insight.title,
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.weight(1f)
                            )
                            
                            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                insight.domains.forEach { domain ->
                                    Surface(
                                        shape = RoundedCornerShape(6.dp),
                                        color = MaterialTheme.colorScheme.primaryContainer
                                    ) {
                                        Text(
                                            domain,
                                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                            style = MaterialTheme.typography.labelSmall
                                        )
                                    }
                                }
                            }
                        }
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Text(
                            insight.description,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

/**
 * 跨领域模式标签页
 */
@Composable
fun PatternsTabContent(result: CrossDomainAnalysisResult) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        // 跨领域模式
        Text(
            "🔗 跨领域模式 (${result.crossDomainAnalysis.crossDomainPatterns.size})",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        
        result.crossDomainAnalysis.crossDomainPatterns.forEach { pattern ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            pattern.title,
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.weight(1f)
                        )
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = MaterialTheme.colorScheme.secondaryContainer
                        ) {
                            Text(
                                pattern.strength,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                style = MaterialTheme.typography.labelSmall
                            )
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(pattern.description, style = MaterialTheme.typography.bodyMedium)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "涉及领域: ${pattern.domains.joinToString(" × ")}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
        
        // 协同效应
        if (result.crossDomainAnalysis.synergies.isNotEmpty()) {
            Text(
                "⚡ 协同效应 (${result.crossDomainAnalysis.synergies.size})",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            
            result.crossDomainAnalysis.synergies.forEach { synergy ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFF10b981).copy(alpha = 0.1f)
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            synergy.title,
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(synergy.description, style = MaterialTheme.typography.bodyMedium)
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "💡 潜在收益: ${synergy.potentialBenefit}",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF10b981),
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
        
        // 潜在冲突
        if (result.crossDomainAnalysis.conflicts.isNotEmpty()) {
            Text(
                "⚠️ 潜在冲突 (${result.crossDomainAnalysis.conflicts.size})",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            
            result.crossDomainAnalysis.conflicts.forEach { conflict ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFFFF9500).copy(alpha = 0.1f)
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                conflict.title,
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.weight(1f)
                            )
                            Surface(
                                shape = RoundedCornerShape(6.dp),
                                color = Color(0xFFFF9500).copy(alpha = 0.2f)
                            ) {
                                Text(
                                    conflict.severity,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                    style = MaterialTheme.typography.labelSmall,
                                    color = Color(0xFFFF9500)
                                )
                            }
                        }
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(conflict.description, style = MaterialTheme.typography.bodyMedium)
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "🔧 解决建议: ${conflict.resolutionSuggestion}",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFFFF9500),
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

/**
 * 战略建议标签页
 */
@Composable
fun RecommendationsTabContent(result: CrossDomainAnalysisResult) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(
            "🎯 战略建议 (${result.crossDomainAnalysis.strategicRecommendations.size})",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        
        result.crossDomainAnalysis.strategicRecommendations.forEachIndexed { index, rec ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = MaterialTheme.colorScheme.primary
                        ) {
                            Text(
                                "${index + 1}",
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                                style = MaterialTheme.typography.labelMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                        }
                        
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = MaterialTheme.colorScheme.secondaryContainer
                        ) {
                            Text(
                                rec.priority,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                style = MaterialTheme.typography.labelSmall
                            )
                        }
                        
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = MaterialTheme.colorScheme.tertiaryContainer
                        ) {
                            Text(
                                rec.category,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                style = MaterialTheme.typography.labelSmall
                            )
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    Text(
                        rec.action,
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    Text(
                        "预期影响: ${rec.expectedImpact}",
                        style = MaterialTheme.typography.bodySmall
                    )
                    
                    Spacer(modifier = Modifier.height(4.dp))
                    
                    Text(
                        "时间线: ${rec.timeline}",
                        style = MaterialTheme.typography.bodySmall
                    )
                    
                    rec.involvedDomains?.let { domains ->
                        if (domains.isNotEmpty()) {
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                "涉及领域: ${domains.joinToString(", ")}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * 行动计划标签页
 */
@Composable
fun ActionPlanTabContent(result: CrossDomainAnalysisResult) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(
            "📅 分阶段行动计划",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        
        // 短期行动
        ActionPlanSection(
            icon = "🚀",
            title = "短期行动 (1-3个月)",
            actions = result.crossDomainAnalysis.actionPlan.shortTerm,
            color = Color(0xFF10b981)
        )
        
        // 中期行动
        ActionPlanSection(
            icon = "📈",
            title = "中期行动 (3-6个月)",
            actions = result.crossDomainAnalysis.actionPlan.mediumTerm,
            color = Color(0xFF3b82f6)
        )
        
        // 长期行动
        ActionPlanSection(
            icon = "🎯",
            title = "长期行动 (6-12个月)",
            actions = result.crossDomainAnalysis.actionPlan.longTerm,
            color = Color(0xFFf59e0b)
        )
    }
}

@Composable
fun ActionPlanSection(
    icon: String,
    title: String,
    actions: List<String>,
    color: Color
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = color.copy(alpha = 0.1f)
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(icon, fontSize = 24.sp)
                Text(
                    title,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold
                )
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            actions.forEach { action ->
                Row(
                    modifier = Modifier.padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        "•",
                        style = MaterialTheme.typography.bodyMedium,
                        color = color,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        action,
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }
    }
}
