package com.lifeswarm.android.presentation.decision

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.data.model.OptionSimulationState

/**
 * 选项切换标签栏
 * 支持多选项并行推演的切换和控制
 */
@Composable
fun OptionTabsBar(
    optionStates: Map<String, OptionSimulationState>,
    activeOptionId: String,
    onSelectOption: (String) -> Unit,
    onPauseOption: (String) -> Unit,
    onResumeOption: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    ScrollableTabRow(
        selectedTabIndex = optionStates.keys.indexOf(activeOptionId).coerceAtLeast(0),
        modifier = modifier,
        edgePadding = 8.dp
    ) {
        optionStates.entries.forEachIndexed { index, (optionId, state) ->
            Tab(
                selected = optionId == activeOptionId,
                onClick = { onSelectOption(optionId) },
                text = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        // 选项标题
                        Text(
                            "选项${index + 1}",
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        
                        // 状态指示器
                        when {
                            state.isComplete -> {
                                Icon(
                                    Icons.Default.CheckCircle,
                                    contentDescription = "已完成",
                                    modifier = Modifier.size(16.dp),
                                    tint = MaterialTheme.colorScheme.primary
                                )
                            }
                            state.isPaused -> {
                                IconButton(
                                    onClick = { onResumeOption(optionId) },
                                    modifier = Modifier.size(24.dp)
                                ) {
                                    Icon(
                                        Icons.Default.PlayArrow,
                                        contentDescription = "继续",
                                        modifier = Modifier.size(16.dp)
                                    )
                                }
                            }
                            else -> {
                                IconButton(
                                    onClick = { onPauseOption(optionId) },
                                    modifier = Modifier.size(24.dp)
                                ) {
                                    Icon(
                                        Icons.Default.Pause,
                                        contentDescription = "暂停",
                                        modifier = Modifier.size(16.dp)
                                    )
                                }
                            }
                        }
                        
                        // 评分显示
                        if (state.totalScore > 0) {
                            Text(
                                "${state.totalScore.toInt()}分",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                }
            )
        }
    }
}

/**
 * 简化版选项切换栏（底部导航样式）
 */
@Composable
fun OptionBottomBar(
    optionStates: Map<String, OptionSimulationState>,
    activeOptionId: String,
    onSelectOption: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    NavigationBar(modifier = modifier) {
        optionStates.entries.forEachIndexed { index, (optionId, state) ->
            NavigationBarItem(
                selected = optionId == activeOptionId,
                onClick = { onSelectOption(optionId) },
                icon = {
                    Badge(
                        containerColor = when {
                            state.isComplete -> MaterialTheme.colorScheme.primary
                            state.isPaused -> MaterialTheme.colorScheme.surfaceVariant
                            else -> MaterialTheme.colorScheme.secondary
                        }
                    ) {
                        Text("${index + 1}")
                    }
                },
                label = {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            state.optionTitle,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            style = MaterialTheme.typography.labelSmall
                        )
                        if (state.totalScore > 0) {
                            Text(
                                "${state.totalScore.toInt()}分",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                }
            )
        }
    }
}
