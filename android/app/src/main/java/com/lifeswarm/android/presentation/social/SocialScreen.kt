package com.lifeswarm.android.presentation.social

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel

/**
 * 社交功能主界面 - 对应 web/src/pages/FriendsPage.tsx
 * UI风格：白色背景 + 动态色块 + 玻璃卡片
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SocialScreen(
    userId: String,
    onNavigateBack: () -> Unit,
    onNavigateToTreeHole: () -> Unit = {}
) {
    val viewModel: SocialViewModel = viewModel(
        factory = SocialViewModelFactory(userId)
    )
    
    val uiState by viewModel.uiState.collectAsState()
    
    Box(modifier = Modifier.fillMaxSize()) {
        // 白色背景
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.White)
        )
        
        // 动态色块背景
        AnimatedSocialBackground()
        
        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                TopAppBar(
                    title = { Text("好友", color = Color(0xFF1A1A1A)) },
                    navigationIcon = {
                        IconButton(onClick = onNavigateBack) {
                            Icon(Icons.Default.ArrowBack, "返回", tint = Color(0xFF1A1A1A))
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = Color.Transparent
                    )
                )
            },
        snackbarHost = {
            // 显示错误或成功消息
            if (uiState.error.isNotEmpty() || uiState.successMessage.isNotEmpty()) {
                Snackbar(
                    modifier = Modifier.padding(16.dp),
                    action = {
                        TextButton(onClick = { viewModel.clearMessages() }) {
                            Text("关闭")
                        }
                    }
                ) {
                    Text(uiState.error.ifEmpty { uiState.successMessage })
                }
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .background(MaterialTheme.colorScheme.background)
        ) {
            // 英雄卡片
            HeroCard(friendsCount = uiState.friends.size)
            
            // 标签页
            TabBar(
                activeTab = uiState.activeTab,
                onTabSelected = { viewModel.switchTab(it) }
            )
            
            // 树洞入口卡片
            TreeHoleEntryCard(
                onNavigateToTreeHole = onNavigateToTreeHole
            )
            
            // 内容区域
            when (uiState.activeTab) {
                SocialTab.FRIENDS -> FriendsTab(
                    friends = uiState.friends,
                    isLoading = uiState.isLoading,
                    onRefresh = { viewModel.loadFriends() }
                )
                SocialTab.REQUESTS -> RequestsTab(
                    requests = uiState.friendRequests,
                    isLoading = uiState.isLoading,
                    onAccept = { viewModel.acceptFriendRequest(it) },
                    onReject = { viewModel.rejectFriendRequest(it) }
                )
                SocialTab.SEARCH -> SearchTab(
                    searchQuery = uiState.searchQuery,
                    searchResults = uiState.searchResults,
                    isLoading = uiState.isLoading,
                    onQueryChange = { viewModel.updateSearchQuery(it) },
                    onSearch = { viewModel.searchUsers() },
                    onSendRequest = { viewModel.sendFriendRequest(it) }
                )
            }
        }
    }
    }
}

/**
 * 英雄卡片 - 玻璃质感（对应Web端）
 */
@Composable
fun HeroCard(friendsCount: Int) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        shape = RoundedCornerShape(24.dp),
        color = Color.White.copy(alpha = 0.7f),
        shadowElevation = 8.dp,
        border = androidx.compose.foundation.BorderStroke(
            1.dp,
            Color.White.copy(alpha = 0.3f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 图标
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(
                        Brush.linearGradient(
                            colors = listOf(
                                Color(0xFFB0D9FF),
                                Color(0xFF7DBDFF)
                            )
                        )
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.People,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(32.dp)
                )
            }
            
            // 信息
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    "好友",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF1A1A1A)
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "管理你的好友关系",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color(0xFF666666)
                )
                Spacer(modifier = Modifier.height(8.dp))
                Surface(
                    shape = RoundedCornerShape(999.dp),
                    color = Color(0xFF0A59F7).copy(alpha = 0.15f)
                ) {
                    Text(
                        "$friendsCount 位好友",
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF0A59F7)
                    )
                }
            }
        }
    }
}

/**
 * 树洞入口卡片
 */
@Composable
fun TreeHoleEntryCard(onNavigateToTreeHole: () -> Unit) {
    Card(
        onClick = onNavigateToTreeHole,
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF2D5A4A).copy(alpha = 0.3f)
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 树洞图标
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(CircleShape)
                    .background(
                        Brush.linearGradient(
                            colors = listOf(
                                Color(0xFF8B5A2B),
                                Color(0xFF654321)
                            )
                        )
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.Shield,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(28.dp)
                )
            }
            
            // 内容
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    "树洞世界",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "匿名分享你的心情、秘密和梦想",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            // 箭头
            Icon(
                Icons.Default.ArrowForward,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary
            )
        }
    }
}

/**
 * 标签栏
 */
@Composable
fun TabBar(
    activeTab: SocialTab,
    onTabSelected: (SocialTab) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            TabButton(
                text = "好友列表",
                icon = Icons.Default.People,
                isActive = activeTab == SocialTab.FRIENDS,
                onClick = { onTabSelected(SocialTab.FRIENDS) },
                modifier = Modifier.weight(1f)
            )
            TabButton(
                text = "好友请求",
                icon = Icons.Default.Mail,
                isActive = activeTab == SocialTab.REQUESTS,
                onClick = { onTabSelected(SocialTab.REQUESTS) },
                modifier = Modifier.weight(1f)
            )
            TabButton(
                text = "添加好友",
                icon = Icons.Default.Search,
                isActive = activeTab == SocialTab.SEARCH,
                onClick = { onTabSelected(SocialTab.SEARCH) },
                modifier = Modifier.weight(1f)
            )
        }
    }
}

/**
 * 标签按钮
 */
@Composable
fun TabButton(
    text: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    isActive: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Button(
        onClick = onClick,
        modifier = modifier.height(48.dp),
        shape = RoundedCornerShape(16.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = if (isActive) {
                MaterialTheme.colorScheme.primary
            } else {
                Color.Transparent
            },
            contentColor = if (isActive) {
                MaterialTheme.colorScheme.onPrimary
            } else {
                MaterialTheme.colorScheme.onSurfaceVariant
            }
        ),
        elevation = if (isActive) {
            ButtonDefaults.buttonElevation(defaultElevation = 2.dp)
        } else {
            ButtonDefaults.buttonElevation(defaultElevation = 0.dp)
        }
    ) {
        Icon(
            icon,
            contentDescription = null,
            modifier = Modifier.size(18.dp)
        )
        Spacer(modifier = Modifier.width(4.dp))
        Text(
            text,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = if (isActive) FontWeight.Bold else FontWeight.Normal,
            fontSize = 12.sp
        )
    }
}

// 继续在下一个文件...

/**
 * 好友列表标签页
 */
@Composable
fun FriendsTab(
    friends: List<com.lifeswarm.android.data.model.Friend>,
    isLoading: Boolean,
    onRefresh: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
        ) {
            // 标题
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        "我的好友",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "共 ${friends.size} 位好友",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                
                IconButton(onClick = onRefresh) {
                    Icon(Icons.Default.Refresh, "刷新")
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 好友列表
            if (isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else if (friends.isEmpty()) {
                EmptyState(
                    icon = Icons.Default.People,
                    title = "还没有好友",
                    message = "快去添加吧"
                )
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(friends) { friend ->
                        FriendItem(friend)
                    }
                }
            }
        }
    }
}

/**
 * 好友项
 */
@Composable
fun FriendItem(friend: com.lifeswarm.android.data.model.Friend) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 头像
            Box(
                modifier = Modifier.size(52.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(52.dp)
                        .clip(CircleShape)
                        .background(
                            Brush.linearGradient(
                                colors = listOf(
                                    Color(0xFFB0D9FF),
                                    Color(0xFF7DBDFF)
                                )
                            )
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        friend.nickname.take(1).uppercase(),
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }
                
                // 在线状态
                Box(
                    modifier = Modifier
                        .size(14.dp)
                        .align(Alignment.BottomEnd)
                        .clip(CircleShape)
                        .background(
                            if (friend.status == "online") Color(0xFF34C759) else Color.Gray
                        )
                        .padding(2.dp)
                        .background(Color.White)
                )
            }
            
            // 信息
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    friend.nickname,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "@${friend.username}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            // 发消息按钮
            Button(
                onClick = { /* TODO: 发消息功能 */ },
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary
                )
            ) {
                Text("发消息", fontSize = 13.sp)
            }
        }
    }
}

/**
 * 好友请求标签页
 */
@Composable
fun RequestsTab(
    requests: List<com.lifeswarm.android.data.model.FriendRequest>,
    isLoading: Boolean,
    onAccept: (String) -> Unit,
    onReject: (String) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
        ) {
            // 标题
            Text(
                "好友请求",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
            Text(
                "共 ${requests.size} 条请求",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 请求列表
            if (isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else if (requests.isEmpty()) {
                EmptyState(
                    icon = Icons.Default.Mail,
                    title = "暂无好友请求",
                    message = "当有人向你发送好友请求时，会显示在这里"
                )
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(requests) { request ->
                        FriendRequestItem(
                            request = request,
                            onAccept = { onAccept(request.requestId) },
                            onReject = { onReject(request.requestId) }
                        )
                    }
                }
            }
        }
    }
}

/**
 * 好友请求项
 */
@Composable
fun FriendRequestItem(
    request: com.lifeswarm.android.data.model.FriendRequest,
    onAccept: () -> Unit,
    onReject: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 头像
            Box(
                modifier = Modifier
                    .size(52.dp)
                    .clip(CircleShape)
                    .background(
                        Brush.linearGradient(
                            colors = listOf(
                                Color(0xFFB0D9FF),
                                Color(0xFF7DBDFF)
                            )
                        )
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    request.fromNickname.take(1).uppercase(),
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }
            
            // 信息
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    request.fromNickname,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "@${request.fromUsername}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                if (request.message.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "\"${request.message}\"",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontStyle = androidx.compose.ui.text.font.FontStyle.Italic
                    )
                }
            }
            
            // 操作按钮
            Column(
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = onAccept,
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF34C759)
                    ),
                    modifier = Modifier.width(80.dp)
                ) {
                    Text("接受", fontSize = 13.sp)
                }
                OutlinedButton(
                    onClick = onReject,
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.width(80.dp)
                ) {
                    Text("拒绝", fontSize = 13.sp)
                }
            }
        }
    }
}

/**
 * 搜索标签页
 */
@Composable
fun SearchTab(
    searchQuery: String,
    searchResults: List<com.lifeswarm.android.data.model.SearchResult>,
    isLoading: Boolean,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    onSendRequest: (String) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
        ) {
            // 标题
            Text(
                "添加好友",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
            Text(
                "通过用户名搜索并添加好友",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 搜索框
            OutlinedTextField(
                value = searchQuery,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("输入用户名搜索...") },
                leadingIcon = {
                    Icon(Icons.Default.Search, "搜索")
                },
                trailingIcon = {
                    if (searchQuery.isNotEmpty()) {
                        IconButton(onClick = { onQueryChange("") }) {
                            Icon(Icons.Default.Clear, "清除")
                        }
                    }
                },
                singleLine = true,
                shape = RoundedCornerShape(16.dp),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                keyboardActions = KeyboardActions(onSearch = { onSearch() })
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // 搜索按钮
            Button(
                onClick = onSearch,
                modifier = Modifier.fillMaxWidth(),
                enabled = searchQuery.isNotEmpty() && !isLoading,
                shape = RoundedCornerShape(16.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("搜索中...")
                } else {
                    Text("搜索")
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // 搜索结果
            if (searchResults.isEmpty() && searchQuery.isEmpty()) {
                EmptyState(
                    icon = Icons.Default.Search,
                    title = "开始搜索",
                    message = "输入用户名开始搜索"
                )
            } else if (searchResults.isEmpty() && searchQuery.isNotEmpty() && !isLoading) {
                EmptyState(
                    icon = Icons.Default.SearchOff,
                    title = "未找到用户",
                    message = "请尝试其他关键词"
                )
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(searchResults) { result ->
                        SearchResultItem(
                            result = result,
                            onSendRequest = { onSendRequest(result.userId) }
                        )
                    }
                }
            }
        }
    }
}

/**
 * 搜索结果项
 */
@Composable
fun SearchResultItem(
    result: com.lifeswarm.android.data.model.SearchResult,
    onSendRequest: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 头像
            Box(
                modifier = Modifier
                    .size(52.dp)
                    .clip(CircleShape)
                    .background(
                        Brush.linearGradient(
                            colors = listOf(
                                Color(0xFFB0D9FF),
                                Color(0xFF7DBDFF)
                            )
                        )
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    result.nickname.take(1).uppercase(),
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }
            
            // 信息
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    result.nickname,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "@${result.username}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            // 操作按钮
            if (result.isFriend) {
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = Color(0xFF34C759).copy(alpha = 0.2f)
                ) {
                    Text(
                        "已是好友",
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF34C759)
                    )
                }
            } else {
                Button(
                    onClick = onSendRequest,
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary
                    )
                ) {
                    Text("添加好友", fontSize = 13.sp)
                }
            }
        }
    }
}

/**
 * 空状态组件
 */
@Composable
fun EmptyState(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    message: String
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            icon,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            title,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
            textAlign = TextAlign.Center
        )
    }
}

/**
 * 动态背景 - 色块动画（对应Web端）
 */
@Composable
fun AnimatedSocialBackground() {
    val infiniteTransition = rememberInfiniteTransition(label = "social_bg")
    
    val blob1X by infiniteTransition.animateFloat(
        initialValue = 0.2f,
        targetValue = 0.8f,
        animationSpec = infiniteRepeatable(
            animation = tween(10000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob1X"
    )
    
    val blob2Y by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.7f,
        animationSpec = infiniteRepeatable(
            animation = tween(12000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob2Y"
    )
    
    Canvas(modifier = Modifier.fillMaxSize()) {
        // 蓝色色块
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color(0x400A59F7),
                    Color(0x000A59F7)
                )
            ),
            radius = size.minDimension * 0.4f,
            center = Offset(size.width * blob1X, size.height * 0.25f)
        )
        
        // 紫色色块
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color(0x406B48FF),
                    Color(0x006B48FF)
                )
            ),
            radius = size.minDimension * 0.35f,
            center = Offset(size.width * 0.7f, size.height * blob2Y)
        )
        
        // 青色色块
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color(0x4000D9FF),
                    Color(0x0000D9FF)
                )
            ),
            radius = size.minDimension * 0.3f,
            center = Offset(size.width * 0.3f, size.height * 0.75f)
        )
    }
}
