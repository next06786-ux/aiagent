package com.lifeswarm.android.presentation.knowledge

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lifeswarm.android.data.model.KnowledgeGraphNode
import com.lifeswarm.android.data.model.KnowledgeGraphLink
import com.lifeswarm.android.data.model.KnowledgeGraphView

/**
 * 节点详情侧边栏 - 对应 Web 端的节点详情面板
 * 参考: web/src/pages/KnowledgeGraphPage.tsx 的侧边栏实现
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NodeDetailPanel(
    selectedNode: KnowledgeGraphNode?,
    graph: KnowledgeGraphView?,
    viewMode: String,
    onClose: () -> Unit,
    onDelete: ((KnowledgeGraphNode) -> Unit)? = null,
    onNavigateToNode: ((KnowledgeGraphNode) -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    AnimatedVisibility(
        visible = selectedNode != null,
        enter = slideInHorizontally(initialOffsetX = { it }) + fadeIn(),
        exit = slideOutHorizontally(targetOffsetX = { it }) + fadeOut(),
        modifier = modifier
    ) {
        selectedNode?.let { node ->
            Card(
                modifier = Modifier
                    .fillMaxHeight()
                    .width(360.dp)
                    .padding(16.dp),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.95f)
                ),
                elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(20.dp)
                ) {
                    // 顶部操作栏
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.End,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // 删除按钮
                        if (onDelete != null) {
                            IconButton(
                                onClick = { onDelete(node) },
                                colors = IconButtonDefaults.iconButtonColors(
                                    containerColor = MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.3f),
                                    contentColor = MaterialTheme.colorScheme.error
                                )
                            ) {
                                Icon(Icons.Default.Delete, "删除节点")
                            }
                            Spacer(modifier = Modifier.width(8.dp))
                        }
                        
                        // 关闭按钮
                        IconButton(
                            onClick = onClose,
                            colors = IconButtonDefaults.iconButtonColors(
                                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                            )
                        ) {
                            Icon(Icons.Default.Close, "关闭")
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    // 根据视图模式显示不同内容
                    when (viewMode) {
                        "people" -> PeopleNodeDetail(node, graph, onNavigateToNode)
                        "career" -> CareerNodeDetail(node, graph, onNavigateToNode)
                        "education" -> EducationNodeDetail(node, graph, onNavigateToNode)
                        else -> DefaultNodeDetail(node)
                    }
                }
            }
        }
    }
}

/**
 * 人际关系视图节点详情
 */
@Composable
private fun PeopleNodeDetail(
    node: KnowledgeGraphNode,
    graph: KnowledgeGraphView?,
    onNavigateToNode: ((KnowledgeGraphNode) -> Unit)?
) {
    // 使用 displayName 属性（自动处理 label/name/id 的优先级）
    Text(
        node.displayName,
        style = MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.onSurface
    )
    
    Spacer(modifier = Modifier.height(8.dp))
    
    // 节点类型和连接数
    Text(
        "${node.type} · ${node.connections} 个连接",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
    
    Spacer(modifier = Modifier.height(20.dp))
    
    // 基本信息 - 显示所有 metadata 字段
    node.metadata?.let { metadata ->
        if (metadata.isNotEmpty()) {
            SectionTitle("基本信息")
            Spacer(modifier = Modifier.height(10.dp))
            
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                ),
                shape = RoundedCornerShape(10.dp)
            ) {
                Column(
                    modifier = Modifier.padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    // 显示所有 metadata 字段，过滤掉空值
                    metadata.forEach { (key, value) ->
                        val displayValue = when (value) {
                            is List<*> -> {
                                if ((value as List<*>).isEmpty()) "[]"
                                else value.joinToString(", ")
                            }
                            is Number -> value.toString()
                            is String -> if (value.isEmpty()) null else value
                            null -> null
                            else -> value.toString()
                        }
                        
                        // 只显示非空值
                        if (displayValue != null && displayValue.isNotEmpty()) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    "$key:",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.weight(1f)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    displayValue,
                                    style = MaterialTheme.typography.bodySmall,
                                    fontWeight = FontWeight.Medium,
                                    color = MaterialTheme.colorScheme.onSurface,
                                    textAlign = androidx.compose.ui.text.style.TextAlign.End,
                                    modifier = Modifier.weight(1f)
                                )
                            }
                        }
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(20.dp))
        }
    }
    
    // 相关故事
    SectionTitle("相关故事")
    Spacer(modifier = Modifier.height(10.dp))
    
    val stories = node.stories
    val description = node.description ?: node.metadata?.get("description")?.toString()
    
    if (stories.isNullOrEmpty() && description == null) {
        Text(
            "暂无相关故事记录",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f),
            fontStyle = androidx.compose.ui.text.font.FontStyle.Italic
        )
    } else {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            description?.let {
                if (it.isNotEmpty()) {
                    StoryCard(it)
                }
            }
            stories?.forEach { story ->
                if (story.isNotEmpty() && story != description) {
                    StoryCard(story)
                }
            }
        }
    }
    
    Spacer(modifier = Modifier.height(20.dp))
    
    // 关联人物
    graph?.let {
        val relatedNodes = getRelatedNodes(node, it)
        if (relatedNodes.isNotEmpty()) {
            SectionTitle("关联人物 (${relatedNodes.size})")
            Spacer(modifier = Modifier.height(10.dp))
            
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                relatedNodes.forEach { (relatedNode, relation, _) ->
                    RelatedNodeCard(
                        node = relatedNode,
                        relation = relation,
                        onClick = { onNavigateToNode?.invoke(relatedNode) }
                    )
                }
            }
        }
    }
}

/**
 * 职业发展视图节点详情
 */
@Composable
private fun CareerNodeDetail(
    node: KnowledgeGraphNode,
    graph: KnowledgeGraphView?,
    onNavigateToNode: ((KnowledgeGraphNode) -> Unit)?
) {
    // 使用 displayName 属性（自动处理 label/name/id 的优先级）
    Text(
        node.displayName,
        style = MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.onSurface
    )
    
    Spacer(modifier = Modifier.height(8.dp))
    
    // 节点类型和连接数
    Text(
        "${node.type} · ${node.connections} 个连接",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
    
    Spacer(modifier = Modifier.height(20.dp))
    
    // 职业属性 - 详细信息
    node.metadata?.let { metadata ->
        if (metadata.isNotEmpty()) {
            SectionTitle("详细信息")
            Spacer(modifier = Modifier.height(10.dp))
            
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                ),
                shape = RoundedCornerShape(10.dp)
            ) {
                Column(
                    modifier = Modifier.padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // 定义字段显示顺序和中文标签
                    val fieldLabels = linkedMapOf(
                        "node_type" to "节点类型",
                        "entity_type" to "实体类型",
                        "concept_type" to "概念类型",
                        "company" to "公司",
                        "salary" to "薪资",
                        "location" to "地点",
                        "description" to "描述",
                        "confidence" to "置信度",
                        "interest_level" to "兴趣度",
                        "status" to "状态",
                        "sources" to "数据来源",
                        "related_jobs" to "相关岗位",
                        "job_count" to "岗位数量",
                        "related_events" to "相关事件",
                        "event_count" to "事件数量"
                    )
                    
                    // 按定义的顺序显示字段（跳过 related_jobs 和 job_count）
                    fieldLabels.forEach { (key, label) ->
                        metadata[key]?.let { value ->
                            // 特殊处理技能状态
                            if (key == "status" && node.type.contains("skill", ignoreCase = true)) {
                                val statusValue = value.toString()
                                val statusColors = mapOf(
                                    "mastered" to Color(0xFF4CAF50),
                                    "partial" to Color(0xFFFFC107),
                                    "missing" to Color(0xFFF44336)
                                )
                                val statusLabels = mapOf(
                                    "mastered" to "已掌握",
                                    "partial" to "部分掌握",
                                    "missing" to "待学习"
                                )
                                
                                Column {
                                    Text(
                                        label,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(
                                        statusLabels[statusValue] ?: statusValue,
                                        style = MaterialTheme.typography.bodySmall,
                                        fontWeight = FontWeight.SemiBold,
                                        color = statusColors[statusValue] ?: MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            } else {
                                // 普通字段显示 - 尝试解析节点ID为节点名称
                                val displayValue = when (value) {
                                    is List<*> -> {
                                        if ((value as List<*>).isEmpty()) "[]"
                                        else {
                                            // 尝试将列表中的每个值解析为节点名称
                                            value.mapNotNull { item ->
                                                val itemStr = item?.toString() ?: return@mapNotNull null
                                                // 尝试在图中查找节点
                                                graph?.nodes?.find { 
                                                    it.id == itemStr || it.id.endsWith("_$itemStr")
                                                }?.displayName ?: itemStr
                                            }.joinToString(", ")
                                        }
                                    }
                                    is Number -> {
                                        // 数字可能是节点ID，尝试查找对应节点
                                        val numStr = value.toString()
                                        graph?.nodes?.find { 
                                            it.id == numStr || it.id.endsWith("_$numStr")
                                        }?.displayName ?: numStr
                                    }
                                    is String -> {
                                        if (value.isEmpty()) null 
                                        else {
                                            // 字符串也可能是节点ID，尝试查找
                                            graph?.nodes?.find { 
                                                it.id == value || it.id.endsWith("_$value")
                                            }?.displayName ?: value
                                        }
                                    }
                                    null -> null
                                    else -> value.toString()
                                }
                                
                                // 只显示非空值
                                if (displayValue != null && displayValue.isNotEmpty() && displayValue != "[]") {
                                    Column {
                                        Text(
                                            label,
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                        Spacer(modifier = Modifier.height(2.dp))
                                        Text(
                                            displayValue,
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                    }
                                }
                            }
                        }
                    }
                    
                    // 显示其他未定义的字段
                    metadata.forEach { (key, value) ->
                        if (!fieldLabels.containsKey(key)) {
                            // 尝试解析节点ID为节点名称
                            val displayValue = when (value) {
                                is List<*> -> {
                                    if ((value as List<*>).isEmpty()) null
                                    else {
                                        // 尝试将列表中的每个值解析为节点名称
                                        value.mapNotNull { item ->
                                            val itemStr = item?.toString() ?: return@mapNotNull null
                                            // 尝试在图中查找节点
                                            graph?.nodes?.find { 
                                                it.id == itemStr || it.id.endsWith("_$itemStr")
                                            }?.displayName ?: itemStr
                                        }.joinToString(", ")
                                    }
                                }
                                is Number -> {
                                    // 数字可能是节点ID，尝试查找对应节点
                                    val numStr = value.toString()
                                    graph?.nodes?.find { 
                                        it.id == numStr || it.id.endsWith("_$numStr")
                                    }?.displayName ?: numStr
                                }
                                is String -> {
                                    if (value.isEmpty()) null 
                                    else {
                                        // 字符串也可能是节点ID，尝试查找
                                        graph?.nodes?.find { 
                                            it.id == value || it.id.endsWith("_$value")
                                        }?.displayName ?: value
                                    }
                                }
                                null -> null
                                else -> value.toString()
                            }
                            
                            if (displayValue != null && displayValue.isNotEmpty()) {
                                Column {
                                    Text(
                                        key,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(
                                        displayValue,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }
                        }
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(20.dp))
        }
    }
    
    // 技能掌握度（如果是技能节点且有 weight）
    if (node.type.contains("skill", ignoreCase = true) && node.weight != null) {
        SectionTitle("掌握程度")
        Spacer(modifier = Modifier.height(10.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            LinearProgressIndicator(
                progress = node.weight.toFloat(),
                modifier = Modifier
                    .weight(1f)
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp)),
                color = when {
                    node.weight >= 0.8 -> Color(0xFF4CAF50)
                    node.weight >= 0.4 -> Color(0xFFFFC107)
                    else -> Color(0xFFF44336)
                }
            )
            Text(
                "${(node.weight * 100).toInt()}%",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.width(40.dp)
            )
        }
        
        Spacer(modifier = Modifier.height(20.dp))
    }
    
    // 相关岗位列表（如果是技能节点且有 related_jobs）
    if (node.type.contains("skill", ignoreCase = true)) {
        node.metadata?.get("related_jobs")?.let { relatedJobsValue ->
            // 解析 related_jobs 字段
            val relatedJobs = when (relatedJobsValue) {
                is List<*> -> relatedJobsValue.filterIsInstance<String>()
                is String -> {
                    // 如果是字符串，按逗号分隔
                    relatedJobsValue.split(",").map { it.trim() }.filter { it.isNotEmpty() }
                }
                else -> emptyList()
            }
            
            if (relatedJobs.isNotEmpty()) {
                // 获取 job_count
                val jobCount = node.metadata?.get("job_count")?.toString()?.toIntOrNull() ?: relatedJobs.size
                
                SectionTitle("REQUIRES ($jobCount)")
                Spacer(modifier = Modifier.height(10.dp))
                
                Column(
                    modifier = Modifier.heightIn(max = 400.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    relatedJobs.forEach { jobName ->
                        // 尝试在图中查找对应的岗位节点
                        val jobNode = graph?.nodes?.find { 
                            it.name == jobName || it.id.contains(jobName, ignoreCase = true)
                        }
                        
                        if (jobNode != null) {
                            // 如果找到节点，显示可点击的卡片
                            RelatedNodeCard(
                                node = jobNode,
                                relation = "requires",
                                onClick = { onNavigateToNode?.invoke(jobNode) }
                            )
                        } else {
                            // 如果没找到节点，显示纯文本卡片
                            Card(
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.5f)
                                ),
                                shape = RoundedCornerShape(10.dp)
                            ) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(12.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        jobName,
                                        style = MaterialTheme.typography.bodyMedium,
                                        fontWeight = FontWeight.Medium,
                                        color = MaterialTheme.colorScheme.onSecondaryContainer,
                                        modifier = Modifier.weight(1f)
                                    )
                                    Icon(
                                        Icons.Default.ArrowForward,
                                        contentDescription = null,
                                        tint = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.5f),
                                        modifier = Modifier.size(20.dp)
                                    )
                                }
                            }
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(20.dp))
            }
        }
    }
    
    // 关联节点
    graph?.let {
        val relatedNodes = getRelatedNodes(node, it)
        if (relatedNodes.isNotEmpty()) {
            // 按关系类型分组
            val groupedNodes = relatedNodes.groupBy { it.second }
            
            groupedNodes.forEach { (relation, nodes) ->
                val relationLabel = getCareerRelationLabel(relation)
                SectionTitle("$relationLabel (${nodes.size})")
                Spacer(modifier = Modifier.height(10.dp))
                
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    nodes.forEach { (relatedNode, _, _) ->
                        RelatedNodeCard(
                            node = relatedNode,
                            relation = relation,
                            onClick = { onNavigateToNode?.invoke(relatedNode) }
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}

/**
 * 升学规划视图节点详情
 */
@Composable
private fun EducationNodeDetail(
    node: KnowledgeGraphNode,
    graph: KnowledgeGraphView?,
    onNavigateToNode: ((KnowledgeGraphNode) -> Unit)?
) {
    // 使用 displayName 属性（自动处理 label/name/id 的优先级）
    Text(
        node.displayName,
        style = MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.onSurface
    )
    
    Spacer(modifier = Modifier.height(8.dp))
    
    // 节点类型和连接数
    Text(
        "${node.type} · ${node.connections} 个连接",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
    
    Spacer(modifier = Modifier.height(20.dp))
    
    // 非学校节点的通用信息
    if (node.type != "school") {
        node.metadata?.let { metadata ->
            if (metadata.isNotEmpty()) {
                SectionTitle("详细信息")
                Spacer(modifier = Modifier.height(10.dp))
                
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                    ),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        metadata.forEach { (key, value) ->
                            val displayValue = value?.toString()?.takeIf { it.isNotEmpty() }
                            if (displayValue != null) {
                                Column {
                                    Text(
                                        key,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(
                                        displayValue,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(20.dp))
            }
        }
    }
    
    // 学习进度（如果有 weight）
    if (node.weight != null) {
        SectionTitle("掌握程度")
        Spacer(modifier = Modifier.height(10.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            LinearProgressIndicator(
                progress = node.weight.toFloat(),
                modifier = Modifier
                    .weight(1f)
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp)),
                color = Color(0xFF43E97B) // 渐变绿色
            )
            Text(
                "${(node.weight * 100).toInt()}%",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.width(40.dp)
            )
        }
        
        Spacer(modifier = Modifier.height(20.dp))
    }
    
    // 开设专业列表（仅学校节点）
    if (node.type == "school") {
        node.metadata?.get("majors")?.let { majorsValue ->
            @Suppress("UNCHECKED_CAST")
            val majors = when (majorsValue) {
                is List<*> -> majorsValue.filterIsInstance<String>()
                is String -> majorsValue.split(",").map { it.trim() }
                else -> emptyList()
            }
            
            if (majors.isNotEmpty()) {
                SectionTitle("开设专业 (${majors.size})")
                Spacer(modifier = Modifier.height(10.dp))
                
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                    ),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier.heightIn(max = 200.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .padding(12.dp)
                            .verticalScroll(rememberScrollState())
                    ) {
                        majors.chunked(2).forEach { rowMajors ->
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                rowMajors.forEach { major ->
                                    Surface(
                                        shape = RoundedCornerShape(6.dp),
                                        color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f),
                                        border = androidx.compose.foundation.BorderStroke(
                                            1.dp,
                                            MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)
                                        ),
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        Text(
                                            major,
                                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.onPrimaryContainer
                                        )
                                    }
                                }
                                // 填充空白
                                if (rowMajors.size < 2) {
                                    Spacer(modifier = Modifier.weight(1f))
                                }
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(20.dp))
            }
        }
        
        // 知名教授列表（仅学校节点）
        node.metadata?.get("professors")?.let { professorsValue ->
            @Suppress("UNCHECKED_CAST")
            val professors = when (professorsValue) {
                is List<*> -> professorsValue.filterIsInstance<Map<String, Any>>()
                else -> emptyList()
            }
            
            if (professors.isNotEmpty()) {
                SectionTitle("知名教授 (${professors.size})")
                Spacer(modifier = Modifier.height(10.dp))
                
                Column(
                    modifier = Modifier.heightIn(max = 250.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    professors.forEach { prof ->
                        Card(
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                            ),
                            shape = RoundedCornerShape(8.dp),
                            border = androidx.compose.foundation.BorderStroke(
                                1.dp,
                                MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)
                            )
                        ) {
                            Column(modifier = Modifier.padding(10.dp)) {
                                Text(
                                    prof["name"]?.toString() ?: "未知",
                                    style = MaterialTheme.typography.bodyMedium,
                                    fontWeight = FontWeight.SemiBold,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                
                                prof["research_area"]?.toString()?.let { area ->
                                    if (area.isNotEmpty()) {
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            "研究方向: $area",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }
                                
                                prof["h_index"]?.let { hIndex ->
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(
                                        "H-index: $hIndex",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.8f)
                                    )
                                }
                            }
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(20.dp))
            }
        }
    }
    
    // 相关标签
    if (!node.insightTags.isNullOrEmpty()) {
        SectionTitle("标签")
        Spacer(modifier = Modifier.height(10.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            node.insightTags.take(3).forEach { tag ->
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f)
                ) {
                    Text(
                        tag,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(20.dp))
    }
    
    // 关联节点
    graph?.let {
        val relatedNodes = getRelatedNodes(node, it)
        if (relatedNodes.isNotEmpty()) {
            SectionTitle("关联节点 (${relatedNodes.size})")
            Spacer(modifier = Modifier.height(10.dp))
            
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                relatedNodes.forEach { (relatedNode, relation, _) ->
                    RelatedNodeCard(
                        node = relatedNode,
                        relation = relation,
                        onClick = { onNavigateToNode?.invoke(relatedNode) }
                    )
                }
            }
        }
    }
}

/**
 * 默认节点详情
 */
@Composable
private fun DefaultNodeDetail(node: KnowledgeGraphNode) {
    Text(
        node.name,
        style = MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.onSurface
    )
    
    Spacer(modifier = Modifier.height(8.dp))
    
    Text(
        "节点 ID: ${node.id}",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
    
    Text(
        "类型: ${node.type}",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
    
    Text(
        "连接数: ${node.connections}",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
}

/**
 * 章节标题
 */
@Composable
private fun SectionTitle(title: String) {
    Text(
        title,
        style = MaterialTheme.typography.titleSmall,
        fontWeight = FontWeight.SemiBold,
        color = MaterialTheme.colorScheme.primary
    )
}

/**
 * 故事卡片
 */
@Composable
private fun StoryCard(content: String) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
        ),
        shape = RoundedCornerShape(10.dp)
    ) {
        Text(
            content,
            modifier = Modifier.padding(12.dp),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurface,
            lineHeight = 20.sp
        )
    }
}

/**
 * 关联节点卡片
 */
@Composable
private fun RelatedNodeCard(
    node: KnowledgeGraphNode,
    relation: String,
    onClick: () -> Unit
) {
    // 使用 displayName 属性（自动处理 label/name/id 的优先级）
    Card(
        onClick = onClick,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.5f)
        ),
        shape = RoundedCornerShape(10.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 只显示节点名称，不显示关系类型
            Text(
                node.displayName,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.onSecondaryContainer,
                modifier = Modifier.weight(1f)
            )
            Icon(
                Icons.Default.ArrowForward,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.5f),
                modifier = Modifier.size(20.dp)
            )
        }
    }
}

/**
 * 获取关联节点
 */
private fun getRelatedNodes(
    node: KnowledgeGraphNode,
    graph: KnowledgeGraphView
): List<Triple<KnowledgeGraphNode, String, String>> {
    val relatedNodes = mutableListOf<Triple<KnowledgeGraphNode, String, String>>()
    
    // 使用 links 或 edges
    val links = graph.edges ?: graph.links
    
    links.forEach { link ->
        if (link.source == node.id) {
            val targetNode = graph.nodes.find { it.id == link.target }
            if (targetNode != null) {
                relatedNodes.add(Triple(targetNode, link.type, "out"))
            }
        } else if (link.target == node.id) {
            val sourceNode = graph.nodes.find { it.id == link.source }
            if (sourceNode != null) {
                relatedNodes.add(Triple(sourceNode, link.type, "in"))
            }
        }
    }
    
    return relatedNodes
}

/**
 * 获取节点类型颜色
 */
private fun getNodeTypeColor(type: String): Color {
    return when {
        type.contains("skill", ignoreCase = true) -> Color(0xFF4CAF50)
        type.contains("position", ignoreCase = true) -> Color(0xFF2196F3)
        type.contains("company", ignoreCase = true) -> Color(0xFF9C27B0)
        else -> Color(0xFF607D8B)
    }
}

/**
 * 获取职业关系标签
 */
private fun getCareerRelationLabel(relation: String): String {
    return when (relation.lowercase()) {
        "mastery" -> "掌握的技能"
        "requirement", "requires" -> "需要的技能"
        "employment", "works_at" -> "所属公司"
        "dependency", "depends_on" -> "依赖技能"
        "has_skill" -> "已掌握技能"
        "requires_skill" -> "需要的技能"
        else -> relation
    }
}

/**
 * 获取升学关系标签
 */
private fun getEducationRelationLabel(relation: String): String {
    return when (relation.lowercase()) {
        "has_achievement" -> "学业成就"
        "qualifies_for" -> "符合条件的院校"
        "requires_action" -> "需要的行动"
        else -> relation
    }
}
