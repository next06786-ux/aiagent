package com.lifeswarm.android.presentation.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.lifeswarm.android.LifeSwarmApp
import com.lifeswarm.android.presentation.auth.AuthScreen
import com.lifeswarm.android.presentation.auth.AuthViewModel
import com.lifeswarm.android.presentation.auth.AuthViewModelFactory
import com.lifeswarm.android.presentation.chat.ChatScreen
import com.lifeswarm.android.presentation.common.LoadingScreen
import com.lifeswarm.android.presentation.home.EnhancedHomeScreen

/**
 * 应用导航 - 对应 web/src/App.tsx 的路由配置
 */
@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val context = LocalContext.current
    val application = context.applicationContext as LifeSwarmApp
    
    // 使用 Factory 创建 ViewModel
    val authViewModel: AuthViewModel = viewModel(
        factory = AuthViewModelFactory(application)
    )
    
    val isAuthenticated by authViewModel.isAuthenticated.collectAsState()
    
    NavHost(
        navController = navController,
        startDestination = if (isAuthenticated) "home" else "auth"
    ) {
        // 认证页面
        composable("auth") {
            AuthScreen(
                authViewModel = authViewModel,
                onNavigateToHome = {
                    navController.navigate("home") {
                        popUpTo("auth") { inclusive = true }
                    }
                }
            )
        }
        
        // 主页 - 使用增强版UI
        composable("home") {
            EnhancedHomeScreen(
                onNavigateToChat = {
                    navController.navigate("chat")
                },
                onNavigateToDecision = {
                    navController.navigate("decision")
                },
                onNavigateToKnowledgeGraph = {
                    navController.navigate("knowledge-graph")
                },
                onNavigateToInsights = {
                    navController.navigate("insights")
                },
                onNavigateToParallelLife = {
                    navController.navigate("parallel-life")
                },
                onNavigateToSocial = {
                    navController.navigate("social")
                },
                onNavigateToProfile = {
                    navController.navigate("profile")
                }
            )
        }
        
        // AI 对话页面 - 对应 web/src/pages/AIChatPage.tsx
        composable("chat") {
            val chatViewModel: com.lifeswarm.android.presentation.chat.ChatViewModel = viewModel(
                factory = com.lifeswarm.android.presentation.chat.ChatViewModelFactory(application)
            )
            
            ChatScreen(
                viewModel = chatViewModel,
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToKnowledgeGraph = { question ->
                    navController.navigate("knowledge-graph?question=$question")
                },
                onNavigateToDecision = {
                    navController.navigate("decision")
                },
                onNavigateToParallelLife = {
                    navController.navigate("parallel-life")
                },
                onNavigateToConversationList = {
                    navController.navigate("conversation-list")
                }
            )
        }
        
        // 会话列表页面
        composable("conversation-list") {
            println("[Navigation] ========== 进入会话列表页面 ==========")
            
            // 从chat页面共享ViewModel，避免重复创建
            val chatBackStackEntry = navController.getBackStackEntry("chat")
            println("[Navigation] 1. 获取到chat页面的BackStackEntry")
            
            val chatViewModel: com.lifeswarm.android.presentation.chat.ChatViewModel = viewModel(
                viewModelStoreOwner = chatBackStackEntry
            )
            println("[Navigation] 2. 获取到ChatViewModel实例")
            
            val uiState by chatViewModel.uiState.collectAsState()
            println("[Navigation] 3. collectAsState完成")
            println("[Navigation] 4. 会话列表数量: ${uiState.conversations.size}")
            
            // 打印前3个会话的信息
            uiState.conversations.take(3).forEachIndexed { index, conv ->
                println("[Navigation]    会话${index + 1}:")
                println("[Navigation]      id: '${conv.id}'")
                println("[Navigation]      conversationId: '${conv.conversationId}'")
                println("[Navigation]      sessionId: '${conv.sessionId}'")
                println("[Navigation]      title: ${conv.title}")
                println("[Navigation]      lastMessageTime: ${conv.lastMessageTime}")
                println("[Navigation]      displayTime: ${conv.displayTime}")
            }
            
            println("[Navigation] 5. 准备渲染ConversationListScreen")
            
            com.lifeswarm.android.presentation.chat.ConversationListScreen(
                conversations = uiState.conversations,
                isLoading = false,
                onConversationClick = { sessionId ->
                    println("[Navigation] ========== 点击会话 ==========")
                    println("[Navigation] sessionId: '$sessionId'")
                    println("[Navigation] sessionId.length: ${sessionId.length}")
                    println("[Navigation] sessionId.isEmpty: ${sessionId.isEmpty()}")
                    
                    // 加载会话消息
                    chatViewModel.loadConversation(sessionId)
                    
                    // 返回到聊天页面
                    navController.popBackStack()
                },
                onNewConversation = {
                    println("[Navigation] 新建会话")
                    chatViewModel.startNewConversation()
                    navController.popBackStack()
                },
                onNavigateBack = {
                    println("[Navigation] 返回")
                    navController.popBackStack()
                },
                onRefresh = {
                    println("[Navigation] 刷新会话列表")
                    // TODO: 刷新会话列表
                }
            )
            
            println("[Navigation] 6. ConversationListScreen渲染完成")
        }
        
        // 决策副本页面 - 对应 web/src/pages/DecisionWorkbenchPage.tsx
        composable("decision") {
            com.lifeswarm.android.presentation.decision.DecisionScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToCollection = { question ->
                    val encodedQuestion = java.net.URLEncoder.encode(question, "UTF-8")
                    navController.navigate("decision-collection?question=$encodedQuestion&type=general")
                },
                onNavigateToHistory = {
                    navController.navigate("decision-history")
                }
            )
        }
        
        // 决策信息采集页面
        composable(
            route = "decision-collection?question={question}&type={type}",
            arguments = listOf(
                navArgument("question") { 
                    type = NavType.StringType
                    defaultValue = ""
                },
                navArgument("type") { 
                    type = NavType.StringType
                    defaultValue = "general"
                }
            )
        ) { backStackEntry ->
            val question = backStackEntry.arguments?.getString("question") ?: ""
            val decisionType = backStackEntry.arguments?.getString("type") ?: "general"
            
            com.lifeswarm.android.presentation.decision.DecisionCollectionScreen(
                initialQuestion = question,
                decisionType = decisionType,
                onNavigateBack = {
                    navController.popBackStack()
                },
                onComplete = { sessionId ->
                    // 导航到选项确认页面
                    val encodedQuestion = java.net.URLEncoder.encode(question, "UTF-8")
                    navController.navigate("decision-options?sessionId=$sessionId&question=$encodedQuestion&type=$decisionType")
                }
            )
        }
        
        // 决策选项确认页面
        composable(
            route = "decision-options?sessionId={sessionId}&question={question}&type={type}",
            arguments = listOf(
                navArgument("sessionId") { 
                    type = NavType.StringType
                    defaultValue = ""
                },
                navArgument("question") { 
                    type = NavType.StringType
                    defaultValue = ""
                },
                navArgument("type") { 
                    type = NavType.StringType
                    defaultValue = "general"
                }
            )
        ) { backStackEntry ->
            val sessionId = backStackEntry.arguments?.getString("sessionId") ?: ""
            val question = backStackEntry.arguments?.getString("question") ?: ""
            val decisionType = backStackEntry.arguments?.getString("type") ?: "general"
            
            // 使用共享的 ViewModel（通过 navController 的 graph 作为 owner）
            val collectionViewModel: com.lifeswarm.android.presentation.decision.DecisionCollectionViewModel = viewModel(
                viewModelStoreOwner = navController.getBackStackEntry("decision-collection?question=$question&type=$decisionType")
            )
            val collectionState by collectionViewModel.uiState.collectAsState()
            
            android.util.Log.d("Navigation", "[选项页面] 收到 ${collectionState.generatedOptions.size} 个选项")
            
            com.lifeswarm.android.presentation.decision.DecisionOptionsScreen(
                sessionId = sessionId,
                question = question,
                initialOptions = collectionState.generatedOptions,
                collectedInfo = collectionState.collectedInfo,
                onNavigateBack = {
                    navController.popBackStack()
                },
                onStartSimulation = { options ->
                    // 导航到推演页面
                    android.util.Log.d("Navigation", "[选项确认] 准备启动推演")
                    android.util.Log.d("Navigation", "  sessionId: $sessionId")
                    android.util.Log.d("Navigation", "  question: $question")
                    android.util.Log.d("Navigation", "  options数量: ${options.size}")
                    android.util.Log.d("Navigation", "  decisionType: $decisionType")
                    
                    options.forEachIndexed { index, opt ->
                        android.util.Log.d("Navigation", "  选项${index + 1}: title=${opt.title}, desc=${opt.description?.take(50)}")
                    }
                    
                    // 通过 SavedStateHandle 传递选项数据
                    navController.currentBackStackEntry?.savedStateHandle?.apply {
                        set("simulation_options", options)
                        set("simulation_collectedInfo", collectionState.collectedInfo)
                        android.util.Log.d("Navigation", "[选项确认] 已保存到 SavedStateHandle")
                    }
                    
                    // 导航到推演页面
                    val encodedQuestion = java.net.URLEncoder.encode(question, "UTF-8")
                    val route = "decision-simulation?sessionId=$sessionId&question=$encodedQuestion&type=$decisionType"
                    android.util.Log.d("Navigation", "[选项确认] 导航到: $route")
                    navController.navigate(route)
                }
            )
        }
        
        // 决策推演页面
        composable(
            route = "decision-simulation?sessionId={sessionId}&question={question}&type={type}",
            arguments = listOf(
                navArgument("sessionId") { 
                    type = NavType.StringType
                    defaultValue = ""
                },
                navArgument("question") { 
                    type = NavType.StringType
                    defaultValue = ""
                },
                navArgument("type") { 
                    type = NavType.StringType
                    defaultValue = "general"
                }
            )
        ) { backStackEntry ->
            val sessionId = backStackEntry.arguments?.getString("sessionId") ?: ""
            val question = backStackEntry.arguments?.getString("question") ?: ""
            val decisionType = backStackEntry.arguments?.getString("type") ?: "general"
            
            android.util.Log.d("Navigation", "[推演页面] 进入推演页面")
            android.util.Log.d("Navigation", "  sessionId: $sessionId")
            android.util.Log.d("Navigation", "  question: $question")
            android.util.Log.d("Navigation", "  decisionType: $decisionType")
            
            // 从前一个页面获取选项数据
            val previousEntry = navController.previousBackStackEntry
            android.util.Log.d("Navigation", "  previousEntry: ${previousEntry?.destination?.route}")
            
            val options = previousEntry?.savedStateHandle?.get<List<com.lifeswarm.android.data.model.OptionInput>>("simulation_options") ?: emptyList()
            val collectedInfo = previousEntry?.savedStateHandle?.get<com.lifeswarm.android.data.model.CollectedInfo>("simulation_collectedInfo")
            
            android.util.Log.d("Navigation", "  从 SavedStateHandle 获取到 ${options.size} 个选项")
            options.forEachIndexed { index, opt ->
                android.util.Log.d("Navigation", "    选项${index + 1}: ${opt.title}")
            }
            
            // 获取当前用户
            val user by authViewModel.user.collectAsState()
            val userId = user?.userId ?: ""
            
            android.util.Log.d("Navigation", "  userId: $userId")
            android.util.Log.d("Navigation", "  检查参数: sessionId=${sessionId.isNotEmpty()}, userId=${userId.isNotEmpty()}, options=${options.size}")
            
            if (sessionId.isNotEmpty() && userId.isNotEmpty() && options.isNotEmpty()) {
                android.util.Log.d("Navigation", "[推演页面] 参数完整，启动推演界面")
                com.lifeswarm.android.presentation.decision.EnhancedSimulationScreen(
                    sessionId = sessionId,
                    userId = userId,
                    question = question,
                    options = options,
                    collectedInfo = collectedInfo,
                    decisionType = decisionType,
                    onNavigateBack = {
                        navController.popBackStack()
                    }
                )
            } else {
                android.util.Log.e("Navigation", "[推演页面] 参数不完整！")
                android.util.Log.e("Navigation", "  sessionId为空: ${sessionId.isEmpty()}")
                android.util.Log.e("Navigation", "  userId为空: ${userId.isEmpty()}")
                android.util.Log.e("Navigation", "  options为空: ${options.isEmpty()}")
                
                // 参数不完整，显示错误
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            "参数不完整",
                            style = MaterialTheme.typography.titleLarge
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "sessionId: ${sessionId.isNotEmpty()}, userId: ${userId.isNotEmpty()}, options: ${options.size}",
                            style = MaterialTheme.typography.bodyMedium
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = { navController.popBackStack() }) {
                            Text("返回")
                        }
                    }
                }
            }
        }
        
        // 决策历史页面
        composable("decision-history") {
            val user by authViewModel.user.collectAsState()
            user?.let {
                com.lifeswarm.android.presentation.decision.DecisionHistoryScreen(
                    userId = it.userId,
                    onNavigateBack = {
                        navController.popBackStack()
                    },
                    onNavigateToDetail = { simulationId ->
                        navController.navigate("decision-result/$simulationId")
                    },
                    repository = application.decisionRepository
                )
            }
        }
        
        // 决策结果页面
        composable("decision-result/{simulationId}") { backStackEntry ->
            val simulationId = backStackEntry.arguments?.getString("simulationId") ?: ""
            com.lifeswarm.android.presentation.decision.DecisionResultScreen(
                simulationId = simulationId,
                onNavigateBack = {
                    navController.popBackStack()
                },
                repository = application.decisionRepository
            )
        }
        
        // 知识星图页面 - 对应 web/src/pages/KnowledgeGraphPage.tsx
        composable("knowledge-graph") {
            // 从 AuthStorage 读取 token 和 user
            val token by application.authRepository.tokenFlow.collectAsState(initial = "")
            val user by application.authRepository.userFlow.collectAsState(initial = null)
            val userId = user?.userId ?: ""
            
            // 等待 token 和 userId 加载完成
            if (token.isEmpty() || userId.isEmpty()) {
                // 显示加载中
                Box(
                    modifier = androidx.compose.ui.Modifier.fillMaxSize(),
                    contentAlignment = androidx.compose.ui.Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else {
                com.lifeswarm.android.presentation.knowledge.KnowledgeGraphScreen(
                    token = token,
                    userId = userId,
                    onNavigateBack = {
                        navController.popBackStack()
                    }
                )
            }
        }
        
        // 智慧洞察页面 - 对应 web/src/pages/DecisionInsightsPage.tsx
        composable("insights") {
            val token by application.authRepository.tokenFlow.collectAsState(initial = "")
            
            if (token.isEmpty()) {
                // 显示加载中
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else {
                com.lifeswarm.android.presentation.insight.InsightsScreen(
                    token = token,
                    onNavigateBack = {
                        navController.popBackStack()
                    }
                )
            }
        }
        
        // 平行人生页面 - 对应 web/src/pages/ParallelLifePage.tsx
        composable("parallel-life") {
            val user by authViewModel.user.collectAsState()
            val userId = user?.userId ?: ""
            
            if (userId.isEmpty()) {
                // 显示加载中
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else {
                com.lifeswarm.android.presentation.parallellife.ParallelLifeScreen(
                    userId = userId,
                    onNavigateBack = {
                        navController.popBackStack()
                    }
                )
            }
        }
        
        // 社交功能页面 - 对应 web/src/pages/FriendsPage.tsx
        composable("social") {
            val user by authViewModel.user.collectAsState()
            val userId = user?.userId ?: ""
            
            if (userId.isEmpty()) {
                // 显示加载中
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else {
                com.lifeswarm.android.presentation.social.SocialScreen(
                    userId = userId,
                    onNavigateBack = {
                        navController.popBackStack()
                    },
                    onNavigateToTreeHole = {
                        navController.navigate("tree-hole")
                    }
                )
            }
        }
        
        // 树洞世界页面 - 对应 web/src/pages/TreeHolePage.tsx
        composable("tree-hole") {
            val user by authViewModel.user.collectAsState()
            val userId = user?.userId ?: ""
            
            if (userId.isEmpty()) {
                // 显示加载中
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else {
                com.lifeswarm.android.presentation.treehole.TreeHoleScreen(
                    userId = userId,
                    onNavigateBack = {
                        navController.popBackStack()
                    },
                    onNavigateToDetail = { treeHoleId, treeHole ->
                        // 通过 SavedStateHandle 传递树洞数据
                        navController.currentBackStackEntry?.savedStateHandle?.set("tree_hole", treeHole)
                        navController.navigate("tree-hole-detail/$treeHoleId")
                    }
                )
            }
        }
        
        // 树洞详情页面
        composable(
            route = "tree-hole-detail/{treeHoleId}",
            arguments = listOf(
                navArgument("treeHoleId") {
                    type = NavType.StringType
                }
            )
        ) { backStackEntry ->
            val treeHoleId = backStackEntry.arguments?.getString("treeHoleId") ?: ""
            val user by authViewModel.user.collectAsState()
            val userId = user?.userId ?: ""
            
            // 从前一个页面获取树洞数据
            val previousEntry = navController.previousBackStackEntry
            val treeHole = previousEntry?.savedStateHandle?.get<com.lifeswarm.android.data.model.TreeHole>("tree_hole")
            
            if (userId.isEmpty()) {
                // 显示加载中
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else {
                com.lifeswarm.android.presentation.treehole.TreeHoleDetailScreen(
                    userId = userId,
                    treeHoleId = treeHoleId,
                    treeHole = treeHole,
                    onNavigateBack = {
                        navController.popBackStack()
                    }
                )
            }
        }
        
        // 个人中心页面 - 对应 web/src/pages/ProfilePage.tsx
        composable("profile") {
            val user by authViewModel.user.collectAsState()
            com.lifeswarm.android.presentation.profile.ProfileScreen(
                user = user,
                onNavigateBack = {
                    navController.popBackStack()
                },
                onEditProfile = {
                    navController.navigate("edit-profile")
                },
                onChangePassword = {
                    navController.navigate("change-password")
                },
                onNavigateToSettings = {
                    navController.navigate("settings")
                },
                onLogout = {
                    authViewModel.logout()
                    navController.navigate("auth") {
                        popUpTo("home") { inclusive = true }
                    }
                }
            )
        }
        
        // 编辑资料页面
        composable("edit-profile") {
            val user by authViewModel.user.collectAsState()
            user?.let {
                com.lifeswarm.android.presentation.profile.EditProfileScreen(
                    user = it,
                    onNavigateBack = {
                        navController.popBackStack()
                    },
                    repository = application.authRepository
                )
            }
        }
        
        // 修改密码页面
        composable("change-password") {
            val user by authViewModel.user.collectAsState()
            user?.let {
                com.lifeswarm.android.presentation.profile.ChangePasswordScreen(
                    userId = it.userId,
                    onNavigateBack = {
                        navController.popBackStack()
                    },
                    repository = application.authRepository
                )
            }
        }
        
        // 设置页面
        composable("settings") {
            com.lifeswarm.android.presentation.settings.SettingsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
